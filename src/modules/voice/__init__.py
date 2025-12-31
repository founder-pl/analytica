"""
ANALYTICA Voice Module
======================
Voice input processing and speech-to-text integration.

Features:
- Speech-to-text transcription
- Voice command parsing
- Natural language to DSL conversion
- Audio file processing
"""

from typing import Dict, List, Any, Optional
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
import re

from .. import BaseModule


class VoiceProvider(Enum):
    """Speech-to-text providers"""
    WHISPER = "whisper"
    GOOGLE = "google"
    AZURE = "azure"
    LOCAL = "local"


class AudioFormat(Enum):
    """Supported audio formats"""
    WAV = "wav"
    MP3 = "mp3"
    OGG = "ogg"
    WEBM = "webm"
    M4A = "m4a"


@dataclass
class TranscriptionResult:
    """Result of speech-to-text transcription"""
    id: str
    text: str
    confidence: float
    language: str = "pl"
    duration_seconds: float = 0
    provider: VoiceProvider = VoiceProvider.WHISPER
    created_at: datetime = field(default_factory=datetime.utcnow)
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "text": self.text,
            "confidence": self.confidence,
            "language": self.language,
            "duration_seconds": self.duration_seconds,
            "provider": self.provider.value,
            "created_at": self.created_at.isoformat(),
        }


@dataclass
class VoiceCommand:
    """Parsed voice command"""
    raw_text: str
    intent: str
    entities: Dict[str, Any] = field(default_factory=dict)
    dsl: Optional[str] = None
    confidence: float = 0.0
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "raw_text": self.raw_text,
            "intent": self.intent,
            "entities": self.entities,
            "dsl": self.dsl,
            "confidence": self.confidence,
        }


class VoiceCommandParser:
    """Parse voice commands into DSL"""
    
    # Intent patterns (Polish)
    INTENT_PATTERNS = {
        "load_data": [
            r"(załaduj|wczytaj|pobierz)\s+(dane|plik|raport)\s+(.+)",
            r"(load|get)\s+(data|file)\s+(.+)",
        ],
        "calculate": [
            r"(oblicz|policz|wylicz)\s+(sumę|średnią|ilość)\s+(.+)",
            r"(calculate|compute)\s+(sum|average|count)\s+(.+)",
        ],
        "filter": [
            r"(filtruj|pokaż|wyświetl)\s+(.+)\s+(gdzie|gdy|dla)\s+(.+)",
            r"(filter|show)\s+(.+)\s+(where|when)\s+(.+)",
        ],
        "report": [
            r"(wygeneruj|stwórz|zrób)\s+(raport|zestawienie)\s*(.+)?",
            r"(generate|create)\s+(report|summary)\s*(.+)?",
        ],
        "forecast": [
            r"(prognozuj|przewiduj)\s+(.+)\s+na\s+(\d+)\s+(dni|tygodni|miesięcy)",
            r"(forecast|predict)\s+(.+)\s+for\s+(\d+)\s+(days|weeks|months)",
        ],
        "alert": [
            r"(ustaw|stwórz)\s+alert\s+(.+)\s+(powyżej|poniżej)\s+(\d+)",
            r"(set|create)\s+alert\s+(.+)\s+(above|below)\s+(\d+)",
        ],
    }
    
    # Entity extraction patterns
    ENTITY_PATTERNS = {
        "number": r"\b(\d+(?:\.\d+)?)\b",
        "date": r"\b(\d{4}-\d{2}-\d{2})\b",
        "field": r"pole\s+['\"]?(\w+)['\"]?",
        "file": r"plik\s+['\"]?([^'\"]+)['\"]?",
    }
    
    @classmethod
    def parse(cls, text: str) -> VoiceCommand:
        """Parse voice text into command"""
        text_lower = text.lower().strip()
        
        for intent, patterns in cls.INTENT_PATTERNS.items():
            for pattern in patterns:
                match = re.search(pattern, text_lower, re.IGNORECASE)
                if match:
                    entities = cls._extract_entities(text, match.groups())
                    dsl = cls._generate_dsl(intent, entities)
                    
                    return VoiceCommand(
                        raw_text=text,
                        intent=intent,
                        entities=entities,
                        dsl=dsl,
                        confidence=0.85,
                    )
        
        # No intent matched
        return VoiceCommand(
            raw_text=text,
            intent="unknown",
            entities={},
            dsl=None,
            confidence=0.0,
        )
    
    @classmethod
    def _extract_entities(cls, text: str, groups: tuple) -> Dict[str, Any]:
        """Extract entities from matched groups"""
        entities = {"matched_groups": list(groups)}
        
        for name, pattern in cls.ENTITY_PATTERNS.items():
            matches = re.findall(pattern, text, re.IGNORECASE)
            if matches:
                entities[name] = matches[0] if len(matches) == 1 else matches
        
        return entities
    
    @classmethod
    def _generate_dsl(cls, intent: str, entities: Dict[str, Any]) -> Optional[str]:
        """Generate DSL from intent and entities"""
        groups = entities.get("matched_groups", [])
        
        if intent == "load_data" and len(groups) >= 3:
            source = groups[2].strip()
            return f'data.load("{source}")'
        
        elif intent == "calculate" and len(groups) >= 3:
            func_map = {"sumę": "sum", "średnią": "avg", "ilość": "count", 
                       "sum": "sum", "average": "avg", "count": "count"}
            func = func_map.get(groups[1], "sum")
            field = groups[2].strip()
            return f'metrics.{func}("{field}")'
        
        elif intent == "filter" and len(groups) >= 4:
            condition = groups[3].strip()
            return f'transform.filter({condition})'
        
        elif intent == "report":
            template = groups[2].strip() if len(groups) > 2 and groups[2] else "executive_summary"
            return f'report.generate("{template}")'
        
        elif intent == "forecast" and len(groups) >= 4:
            periods = int(groups[2])
            unit_map = {"dni": 1, "tygodni": 7, "miesięcy": 30,
                       "days": 1, "weeks": 7, "months": 30}
            multiplier = unit_map.get(groups[3], 1)
            total_days = periods * multiplier
            return f'forecast.predict({total_days})'
        
        elif intent == "alert" and len(groups) >= 4:
            metric = groups[1].strip()
            op = "gt" if groups[2] in ["powyżej", "above"] else "lt"
            threshold = groups[3]
            return f'alert.threshold("{metric}", "{op}", {threshold})'
        
        return None


class VoiceModule(BaseModule):
    """Voice module implementation"""
    
    name = "voice"
    version = "1.0.0"
    
    def __init__(self):
        self._transcriptions: Dict[str, TranscriptionResult] = {}
    
    def get_routes(self) -> List[Any]:
        return []
    
    def get_atoms(self) -> Dict[str, Any]:
        return {
            "voice.transcribe": self.transcribe,
            "voice.parse": self.parse_command,
            "voice.to_dsl": self.to_dsl,
        }
    
    def transcribe(self, **kwargs) -> Dict[str, Any]:
        """Transcribe audio to text (mock - returns provided text or placeholder)"""
        from uuid import uuid4
        
        # In production, this would call actual STT API
        text = kwargs.get("text", kwargs.get("_arg0", ""))
        audio_url = kwargs.get("audio_url")
        provider = kwargs.get("provider", "whisper")
        language = kwargs.get("language", "pl")
        
        if not text and audio_url:
            # Mock transcription for demo
            text = f"[Transkrypcja audio: {audio_url}]"
        
        transcription_id = f"trans_{uuid4().hex[:8]}"
        result = TranscriptionResult(
            id=transcription_id,
            text=text,
            confidence=0.95 if text else 0.0,
            language=language,
            provider=VoiceProvider(provider) if provider in [p.value for p in VoiceProvider] else VoiceProvider.WHISPER,
        )
        
        self._transcriptions[transcription_id] = result
        return result.to_dict()
    
    def parse_command(self, **kwargs) -> Dict[str, Any]:
        """Parse voice text into structured command"""
        text = kwargs.get("text", kwargs.get("_arg0", ""))
        
        if not text:
            return {"error": "No text provided", "intent": "unknown"}
        
        command = VoiceCommandParser.parse(text)
        return command.to_dict()
    
    def to_dsl(self, **kwargs) -> Dict[str, Any]:
        """Convert voice text directly to DSL"""
        text = kwargs.get("text", kwargs.get("_arg0", ""))
        
        if not text:
            return {"error": "No text provided", "dsl": None}
        
        command = VoiceCommandParser.parse(text)
        
        return {
            "input": text,
            "dsl": command.dsl,
            "intent": command.intent,
            "confidence": command.confidence,
            "can_execute": command.dsl is not None,
        }


# Module instance
voice_module = VoiceModule()

__all__ = [
    "VoiceModule",
    "TranscriptionResult",
    "VoiceCommand",
    "VoiceProvider",
    "AudioFormat",
    "VoiceCommandParser",
    "voice_module",
]
