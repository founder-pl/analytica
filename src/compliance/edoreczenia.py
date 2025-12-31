"""
ANALYTICA Compliance - E-Doręczenia
====================================

System E-Doręczeń - obowiązkowy dla podmiotów publicznych i firm od 2026

Funkcjonalności:
- Wysyłanie dokumentów przez system e-Doręczeń
- Odbieranie korespondencji
- Weryfikacja adresów ADE (Adres Do Doręczeń Elektronicznych)
- Potwierdzenia doręczeń
- Integracja z BAE (Baza Adresów Elektronicznych)

Dokumentacja: https://www.gov.pl/web/e-doreczenia
"""

from typing import Any, Dict, List, Optional, Union
from dataclasses import dataclass, field
from datetime import datetime, date
from enum import Enum
from abc import ABC, abstractmethod
import base64
import hashlib
import json

import httpx


# ============================================================
# ENUMS & CONSTANTS
# ============================================================

class EDoreczeniaEnvironment(Enum):
    """Środowiska E-Doręczeń"""
    PRODUCTION = "https://edoreczenia.gov.pl/api"
    TEST = "https://test-edoreczenia.gov.pl/api"


class DocumentType(Enum):
    """Typy dokumentów"""
    LETTER = "LETTER"              # List
    INVOICE = "INVOICE"            # Faktura
    CONTRACT = "CONTRACT"          # Umowa
    NOTIFICATION = "NOTIFICATION"  # Powiadomienie
    OFFICIAL = "OFFICIAL"          # Pismo urzędowe
    OTHER = "OTHER"


class DeliveryStatus(Enum):
    """Status doręczenia"""
    PENDING = "PENDING"            # Oczekuje
    SENT = "SENT"                  # Wysłano
    DELIVERED = "DELIVERED"        # Doręczono
    READ = "READ"                  # Odczytano
    FAILED = "FAILED"              # Błąd
    REJECTED = "REJECTED"          # Odrzucono


class RecipientType(Enum):
    """Typ adresata"""
    NATURAL_PERSON = "NATURAL"     # Osoba fizyczna
    LEGAL_ENTITY = "LEGAL"         # Osoba prawna
    PUBLIC_ENTITY = "PUBLIC"       # Podmiot publiczny


# ============================================================
# DATA MODELS
# ============================================================

@dataclass
class EDoreczeniaAddress:
    """
    Adres Do Doręczeń Elektronicznych (ADE)
    
    Format: AE:PL-XXXXX-XXXXX-XXXXX-XX
    """
    ade: str  # Adres ADE
    name: str
    recipient_type: RecipientType
    nip: Optional[str] = None
    regon: Optional[str] = None
    pesel: Optional[str] = None
    email: Optional[str] = None
    
    def validate(self) -> List[str]:
        """Walidacja adresu ADE"""
        errors = []
        
        if not self.ade:
            errors.append("Adres ADE jest wymagany")
        elif not self.ade.startswith("AE:PL-"):
            errors.append("Nieprawidłowy format adresu ADE")
        
        if not self.name:
            errors.append("Nazwa adresata jest wymagana")
        
        if self.recipient_type == RecipientType.LEGAL_ENTITY and not self.nip:
            errors.append("NIP jest wymagany dla osoby prawnej")
        
        return errors


@dataclass
class EDoreczeniaDocument:
    """Dokument do wysłania"""
    title: str
    content: bytes  # Treść dokumentu (PDF, XML, etc.)
    content_type: str = "application/pdf"
    document_type: DocumentType = DocumentType.LETTER
    filename: Optional[str] = None
    metadata: Dict = field(default_factory=dict)
    
    @classmethod
    def from_file(cls, filepath: str, title: str = None, **kwargs) -> 'EDoreczeniaDocument':
        """Utwórz dokument z pliku"""
        from pathlib import Path
        
        path = Path(filepath)
        
        with open(filepath, 'rb') as f:
            content = f.read()
        
        # Auto-detect content type
        content_type_map = {
            '.pdf': 'application/pdf',
            '.xml': 'application/xml',
            '.txt': 'text/plain',
            '.html': 'text/html',
            '.docx': 'application/vnd.openxmlformats-officedocument.wordprocessingml.document'
        }
        
        content_type = content_type_map.get(path.suffix.lower(), 'application/octet-stream')
        
        return cls(
            title=title or path.stem,
            content=content,
            content_type=content_type,
            filename=path.name,
            **kwargs
        )
    
    def get_hash(self) -> str:
        """SHA-256 hash dokumentu"""
        return hashlib.sha256(self.content).hexdigest()


@dataclass
class EDoreczeniaMessage:
    """Wiadomość do wysłania"""
    sender: EDoreczeniaAddress
    recipient: EDoreczeniaAddress
    subject: str
    documents: List[EDoreczeniaDocument]
    body: Optional[str] = None
    priority: str = "NORMAL"  # NORMAL, HIGH
    require_confirmation: bool = True
    reference_id: Optional[str] = None
    
    def validate(self) -> List[str]:
        """Walidacja wiadomości"""
        errors = []
        
        errors.extend([f"Nadawca: {e}" for e in self.sender.validate()])
        errors.extend([f"Odbiorca: {e}" for e in self.recipient.validate()])
        
        if not self.subject:
            errors.append("Temat jest wymagany")
        
        if not self.documents:
            errors.append("Wymagany co najmniej jeden dokument")
        
        # Max 25MB łącznie
        total_size = sum(len(doc.content) for doc in self.documents)
        if total_size > 25 * 1024 * 1024:
            errors.append("Łączny rozmiar dokumentów przekracza 25MB")
        
        return errors


@dataclass
class EDoreczeniaDeliveryConfirmation:
    """Potwierdzenie doręczenia"""
    message_id: str
    status: DeliveryStatus
    timestamp: datetime
    recipient_ade: str
    confirmation_id: Optional[str] = None
    signature: Optional[bytes] = None  # Podpis kwalifikowany
    raw_data: Dict = field(default_factory=dict)


@dataclass
class EDoreczeniaResponse:
    """Odpowiedź z API"""
    success: bool
    message_id: Optional[str] = None
    status: Optional[DeliveryStatus] = None
    timestamp: Optional[datetime] = None
    confirmation: Optional[EDoreczeniaDeliveryConfirmation] = None
    errors: List[str] = field(default_factory=list)
    raw_response: Dict = field(default_factory=dict)


# ============================================================
# BAE CLIENT - Baza Adresów Elektronicznych
# ============================================================

class BAEClient:
    """
    Klient Bazy Adresów Elektronicznych
    
    Umożliwia wyszukiwanie adresów ADE podmiotów
    """
    
    BASE_URL = "https://bae.gov.pl/api/v1"
    
    def __init__(self, api_key: str):
        self.api_key = api_key
        self._client = None
    
    def _get_client(self) -> httpx.Client:
        if self._client is None:
            self._client = httpx.Client(timeout=30.0)
        return self._client
    
    def _headers(self) -> Dict[str, str]:
        return {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
    
    def search_by_nip(self, nip: str) -> Optional[EDoreczeniaAddress]:
        """Wyszukaj adres ADE po NIP"""
        response = self._get_client().get(
            f"{self.BASE_URL}/search",
            params={"nip": nip},
            headers=self._headers()
        )
        
        if response.status_code == 404:
            return None
        
        response.raise_for_status()
        data = response.json()
        
        if not data.get("results"):
            return None
        
        result = data["results"][0]
        return EDoreczeniaAddress(
            ade=result["ade"],
            name=result["name"],
            recipient_type=RecipientType(result.get("type", "LEGAL")),
            nip=result.get("nip")
        )
    
    def search_by_regon(self, regon: str) -> Optional[EDoreczeniaAddress]:
        """Wyszukaj adres ADE po REGON"""
        response = self._get_client().get(
            f"{self.BASE_URL}/search",
            params={"regon": regon},
            headers=self._headers()
        )
        
        if response.status_code == 404:
            return None
        
        response.raise_for_status()
        data = response.json()
        
        if not data.get("results"):
            return None
        
        result = data["results"][0]
        return EDoreczeniaAddress(
            ade=result["ade"],
            name=result["name"],
            recipient_type=RecipientType(result.get("type", "LEGAL")),
            regon=result.get("regon")
        )
    
    def search_by_name(self, name: str, limit: int = 10) -> List[EDoreczeniaAddress]:
        """Wyszukaj adresy ADE po nazwie"""
        response = self._get_client().get(
            f"{self.BASE_URL}/search",
            params={"name": name, "limit": limit},
            headers=self._headers()
        )
        response.raise_for_status()
        
        addresses = []
        for result in response.json().get("results", []):
            addresses.append(EDoreczeniaAddress(
                ade=result["ade"],
                name=result["name"],
                recipient_type=RecipientType(result.get("type", "LEGAL")),
                nip=result.get("nip"),
                regon=result.get("regon")
            ))
        
        return addresses
    
    def verify_ade(self, ade: str) -> bool:
        """Zweryfikuj czy adres ADE jest aktywny"""
        response = self._get_client().get(
            f"{self.BASE_URL}/verify/{ade}",
            headers=self._headers()
        )
        
        if response.status_code == 404:
            return False
        
        response.raise_for_status()
        return response.json().get("active", False)
    
    def close(self):
        if self._client:
            self._client.close()
            self._client = None


# ============================================================
# E-DORĘCZENIA CLIENT
# ============================================================

class EDoreczeniaClient:
    """
    Klient E-Doręczeń
    
    Obsługuje:
    - Wysyłanie korespondencji
    - Odbieranie wiadomości
    - Potwierdzenia doręczeń
    - Zarządzanie skrzynką
    """
    
    def __init__(
        self,
        ade: str,
        api_key: str,
        certificate_path: Optional[str] = None,
        certificate_password: Optional[str] = None,
        environment: EDoreczeniaEnvironment = EDoreczeniaEnvironment.TEST
    ):
        self.ade = ade
        self.api_key = api_key
        self.certificate_path = certificate_path
        self.certificate_password = certificate_password
        self.base_url = environment.value
        self._client = None
        self._bae = BAEClient(api_key)
    
    def _get_client(self) -> httpx.Client:
        if self._client is None:
            # Konfiguracja z certyfikatem jeśli dostępny
            cert = None
            if self.certificate_path:
                cert = (self.certificate_path, self.certificate_password)
            
            self._client = httpx.Client(timeout=60.0, cert=cert)
        return self._client
    
    def _headers(self) -> Dict[str, str]:
        return {
            "Authorization": f"Bearer {self.api_key}",
            "X-ADE": self.ade,
            "Content-Type": "application/json"
        }
    
    # ----------------------------------------------------------
    # SENDING
    # ----------------------------------------------------------
    
    def send_message(self, message: EDoreczeniaMessage) -> EDoreczeniaResponse:
        """Wyślij wiadomość przez e-Doręczenia"""
        # Walidacja
        errors = message.validate()
        if errors:
            return EDoreczeniaResponse(success=False, errors=errors)
        
        # Przygotuj payload
        payload = {
            "sender": {
                "ade": message.sender.ade,
                "name": message.sender.name
            },
            "recipient": {
                "ade": message.recipient.ade,
                "name": message.recipient.name
            },
            "subject": message.subject,
            "body": message.body,
            "priority": message.priority,
            "requireConfirmation": message.require_confirmation,
            "referenceId": message.reference_id,
            "attachments": [
                {
                    "title": doc.title,
                    "filename": doc.filename or f"{doc.title}.pdf",
                    "contentType": doc.content_type,
                    "content": base64.b64encode(doc.content).decode('utf-8'),
                    "hash": doc.get_hash()
                }
                for doc in message.documents
            ]
        }
        
        try:
            response = self._get_client().post(
                f"{self.base_url}/messages/send",
                json=payload,
                headers=self._headers()
            )
            response.raise_for_status()
            
            data = response.json()
            
            return EDoreczeniaResponse(
                success=True,
                message_id=data.get("messageId"),
                status=DeliveryStatus.SENT,
                timestamp=datetime.fromisoformat(data.get("timestamp", "").replace("Z", "+00:00")) if data.get("timestamp") else datetime.now(),
                raw_response=data
            )
            
        except httpx.HTTPStatusError as e:
            return EDoreczeniaResponse(
                success=False,
                errors=[f"HTTP {e.response.status_code}: {e.response.text}"]
            )
        except Exception as e:
            return EDoreczeniaResponse(success=False, errors=[str(e)])
    
    def send_invoice(
        self,
        recipient_ade: str,
        recipient_name: str,
        invoice_pdf: bytes,
        invoice_number: str,
        ksef_number: Optional[str] = None
    ) -> EDoreczeniaResponse:
        """
        Wyślij fakturę przez e-Doręczenia
        
        Integracja z KSeF - można dołączyć numer KSeF
        """
        sender = EDoreczeniaAddress(
            ade=self.ade,
            name="",  # Uzupełniane z konfiguracji
            recipient_type=RecipientType.LEGAL_ENTITY
        )
        
        recipient = EDoreczeniaAddress(
            ade=recipient_ade,
            name=recipient_name,
            recipient_type=RecipientType.LEGAL_ENTITY
        )
        
        metadata = {"invoice_number": invoice_number}
        if ksef_number:
            metadata["ksef_number"] = ksef_number
        
        document = EDoreczeniaDocument(
            title=f"Faktura {invoice_number}",
            content=invoice_pdf,
            content_type="application/pdf",
            document_type=DocumentType.INVOICE,
            filename=f"Faktura_{invoice_number.replace('/', '_')}.pdf",
            metadata=metadata
        )
        
        message = EDoreczeniaMessage(
            sender=sender,
            recipient=recipient,
            subject=f"Faktura {invoice_number}" + (f" (KSeF: {ksef_number})" if ksef_number else ""),
            documents=[document],
            require_confirmation=True
        )
        
        return self.send_message(message)
    
    # ----------------------------------------------------------
    # RECEIVING
    # ----------------------------------------------------------
    
    def get_inbox(
        self,
        status: Optional[DeliveryStatus] = None,
        date_from: Optional[date] = None,
        date_to: Optional[date] = None,
        limit: int = 50
    ) -> List[Dict]:
        """Pobierz wiadomości ze skrzynki"""
        params = {"limit": limit}
        
        if status:
            params["status"] = status.value
        if date_from:
            params["dateFrom"] = date_from.isoformat()
        if date_to:
            params["dateTo"] = date_to.isoformat()
        
        response = self._get_client().get(
            f"{self.base_url}/messages/inbox",
            params=params,
            headers=self._headers()
        )
        response.raise_for_status()
        
        return response.json().get("messages", [])
    
    def get_message(self, message_id: str) -> Dict:
        """Pobierz szczegóły wiadomości"""
        response = self._get_client().get(
            f"{self.base_url}/messages/{message_id}",
            headers=self._headers()
        )
        response.raise_for_status()
        return response.json()
    
    def download_attachment(self, message_id: str, attachment_id: str) -> bytes:
        """Pobierz załącznik"""
        response = self._get_client().get(
            f"{self.base_url}/messages/{message_id}/attachments/{attachment_id}",
            headers=self._headers()
        )
        response.raise_for_status()
        return response.content
    
    def mark_as_read(self, message_id: str) -> bool:
        """Oznacz wiadomość jako przeczytaną"""
        response = self._get_client().post(
            f"{self.base_url}/messages/{message_id}/read",
            headers=self._headers()
        )
        return response.status_code == 200
    
    # ----------------------------------------------------------
    # CONFIRMATIONS
    # ----------------------------------------------------------
    
    def get_delivery_confirmation(self, message_id: str) -> Optional[EDoreczeniaDeliveryConfirmation]:
        """Pobierz potwierdzenie doręczenia"""
        response = self._get_client().get(
            f"{self.base_url}/messages/{message_id}/confirmation",
            headers=self._headers()
        )
        
        if response.status_code == 404:
            return None
        
        response.raise_for_status()
        data = response.json()
        
        return EDoreczeniaDeliveryConfirmation(
            message_id=message_id,
            status=DeliveryStatus(data.get("status", "PENDING")),
            timestamp=datetime.fromisoformat(data.get("timestamp", "").replace("Z", "+00:00")),
            recipient_ade=data.get("recipientAde", ""),
            confirmation_id=data.get("confirmationId"),
            signature=base64.b64decode(data["signature"]) if data.get("signature") else None,
            raw_data=data
        )
    
    def get_sent_messages_status(self, limit: int = 50) -> List[Dict]:
        """Pobierz statusy wysłanych wiadomości"""
        response = self._get_client().get(
            f"{self.base_url}/messages/sent",
            params={"limit": limit},
            headers=self._headers()
        )
        response.raise_for_status()
        return response.json().get("messages", [])
    
    # ----------------------------------------------------------
    # ADDRESS MANAGEMENT
    # ----------------------------------------------------------
    
    def lookup_recipient(self, nip: str = None, regon: str = None, name: str = None) -> Optional[EDoreczeniaAddress]:
        """Wyszukaj adresata w BAE"""
        if nip:
            return self._bae.search_by_nip(nip)
        if regon:
            return self._bae.search_by_regon(regon)
        if name:
            results = self._bae.search_by_name(name, limit=1)
            return results[0] if results else None
        return None
    
    def verify_recipient(self, ade: str) -> bool:
        """Zweryfikuj czy adresat ma aktywne e-Doręczenia"""
        return self._bae.verify_ade(ade)
    
    # ----------------------------------------------------------
    # HELPERS
    # ----------------------------------------------------------
    
    def close(self):
        """Zamknij połączenie"""
        if self._client:
            self._client.close()
            self._client = None
        self._bae.close()
    
    def __enter__(self):
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()


# ============================================================
# COMPLIANCE CHECKER
# ============================================================

class EDoreczeniaComplianceChecker:
    """
    Sprawdzanie zgodności z wymogami e-Doręczeń
    
    Od 1 stycznia 2026:
    - Podmioty publiczne: obowiązkowe
    - Podmioty wpisane do CEIDG: obowiązkowe
    - Podmioty wpisane do KRS: obowiązkowe
    """
    
    MANDATORY_DATE = date(2026, 1, 1)
    
    @staticmethod
    def check_compliance(
        entity_type: str,  # PUBLIC, CEIDG, KRS, OTHER
        has_ade: bool,
        ade_active: bool = False
    ) -> Dict:
        """Sprawdź zgodność podmiotu"""
        mandatory_types = ["PUBLIC", "CEIDG", "KRS"]
        is_mandatory = entity_type.upper() in mandatory_types
        
        today = date.today()
        deadline_passed = today >= EDoreczeniaComplianceChecker.MANDATORY_DATE
        
        compliant = not is_mandatory or (has_ade and ade_active)
        
        return {
            "compliant": compliant,
            "mandatory": is_mandatory,
            "entity_type": entity_type,
            "has_ade": has_ade,
            "ade_active": ade_active,
            "deadline": EDoreczeniaComplianceChecker.MANDATORY_DATE.isoformat(),
            "deadline_passed": deadline_passed,
            "days_to_deadline": (EDoreczeniaComplianceChecker.MANDATORY_DATE - today).days if not deadline_passed else 0,
            "recommendations": EDoreczeniaComplianceChecker._get_recommendations(
                is_mandatory, has_ade, ade_active, deadline_passed
            )
        }
    
    @staticmethod
    def _get_recommendations(
        is_mandatory: bool,
        has_ade: bool,
        ade_active: bool,
        deadline_passed: bool
    ) -> List[str]:
        """Generuj rekomendacje"""
        recommendations = []
        
        if is_mandatory and not has_ade:
            if deadline_passed:
                recommendations.append("PILNE: Wymagana natychmiastowa rejestracja w systemie e-Doręczeń")
            else:
                recommendations.append("Zalecana rejestracja w systemie e-Doręczeń przed terminem obowiązkowym")
        
        if has_ade and not ade_active:
            recommendations.append("Adres ADE jest nieaktywny - należy go aktywować")
        
        if is_mandatory and has_ade and ade_active:
            recommendations.append("Podmiot jest zgodny z wymogami e-Doręczeń")
            recommendations.append("Zalecana integracja systemu fakturowego z e-Doręczeniami")
        
        return recommendations


__all__ = [
    'EDoreczeniaEnvironment',
    'DocumentType',
    'DeliveryStatus',
    'RecipientType',
    'EDoreczeniaAddress',
    'EDoreczeniaDocument',
    'EDoreczeniaMessage',
    'EDoreczeniaDeliveryConfirmation',
    'EDoreczeniaResponse',
    'BAEClient',
    'EDoreczeniaClient',
    'EDoreczeniaComplianceChecker'
]
