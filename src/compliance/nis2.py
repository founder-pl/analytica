"""
ANALYTICA Compliance - NIS2 Directive
======================================

Network and Information Security Directive 2 (NIS2)
Dyrektywa o bezpieczeństwie sieci i systemów informatycznych

Obowiązuje od: 17 października 2024 (transpozycja do prawa krajowego)
Polska ustawa: Ustawa o Krajowym Systemie Cyberbezpieczeństwa (nowelizacja)

Podmioty objęte:
- Sektory kluczowe (essential): energia, transport, bankowość, zdrowie, woda, infrastruktura cyfrowa
- Sektory ważne (important): poczta, odpady, żywność, produkcja, usługi cyfrowe

Wymagania:
- Zarządzanie ryzykiem cyberbezpieczeństwa
- Zgłaszanie incydentów (24h wstępne, 72h pełne)
- Łańcuch dostaw - bezpieczeństwo dostawców
- Szkolenia dla zarządu
- Audyty i testy penetracyjne
"""

from typing import Any, Dict, List, Optional, Union, Tuple
from dataclasses import dataclass, field
from datetime import datetime, date, timedelta
from decimal import Decimal
from enum import Enum
import json


# ============================================================
# ENUMS & CONSTANTS
# ============================================================

class NIS2Sector(Enum):
    """Sektory objęte NIS2"""
    # Sektory kluczowe (essential)
    ENERGY = "energy"
    TRANSPORT = "transport"
    BANKING = "banking"
    FINANCIAL_MARKET = "financial_market"
    HEALTH = "health"
    DRINKING_WATER = "drinking_water"
    WASTE_WATER = "waste_water"
    DIGITAL_INFRASTRUCTURE = "digital_infrastructure"
    ICT_SERVICE_MANAGEMENT = "ict_service_management"
    PUBLIC_ADMINISTRATION = "public_administration"
    SPACE = "space"
    
    # Sektory ważne (important)
    POSTAL = "postal"
    WASTE_MANAGEMENT = "waste_management"
    CHEMICALS = "chemicals"
    FOOD = "food"
    MANUFACTURING = "manufacturing"
    DIGITAL_PROVIDERS = "digital_providers"
    RESEARCH = "research"


class EntityCategory(Enum):
    """Kategoria podmiotu NIS2"""
    ESSENTIAL = "essential"    # Kluczowy
    IMPORTANT = "important"    # Ważny
    NOT_COVERED = "not_covered"


class IncidentSeverity(Enum):
    """Poziom krytyczności incydentu"""
    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"


class IncidentStatus(Enum):
    """Status incydentu"""
    DETECTED = "detected"
    CONTAINED = "contained"
    ERADICATED = "eradicated"
    RECOVERED = "recovered"
    CLOSED = "closed"


# Sektory kluczowe vs ważne
ESSENTIAL_SECTORS = [
    NIS2Sector.ENERGY, NIS2Sector.TRANSPORT, NIS2Sector.BANKING,
    NIS2Sector.FINANCIAL_MARKET, NIS2Sector.HEALTH, NIS2Sector.DRINKING_WATER,
    NIS2Sector.WASTE_WATER, NIS2Sector.DIGITAL_INFRASTRUCTURE,
    NIS2Sector.ICT_SERVICE_MANAGEMENT, NIS2Sector.PUBLIC_ADMINISTRATION,
    NIS2Sector.SPACE
]

IMPORTANT_SECTORS = [
    NIS2Sector.POSTAL, NIS2Sector.WASTE_MANAGEMENT, NIS2Sector.CHEMICALS,
    NIS2Sector.FOOD, NIS2Sector.MANUFACTURING, NIS2Sector.DIGITAL_PROVIDERS,
    NIS2Sector.RESEARCH
]


# ============================================================
# DATA MODELS
# ============================================================

@dataclass
class NIS2Entity:
    """Podmiot objęty NIS2"""
    name: str
    sector: NIS2Sector
    category: EntityCategory
    
    # Dane organizacji
    employees: int
    annual_turnover_eur: Decimal
    balance_sheet_eur: Decimal
    
    # Kontakt
    security_contact_name: str = ""
    security_contact_email: str = ""
    security_contact_phone: str = ""
    
    # Rejestracja
    registered_with_csirt: bool = False
    registration_date: Optional[date] = None
    
    # Status
    compliant: bool = False
    last_audit_date: Optional[date] = None
    next_audit_date: Optional[date] = None


@dataclass
class SecurityIncident:
    """Incydent bezpieczeństwa"""
    # Identyfikacja
    incident_id: str
    title: str
    description: str
    
    # Czas
    detection_time: datetime
    occurrence_time: Optional[datetime] = None
    containment_time: Optional[datetime] = None
    resolution_time: Optional[datetime] = None
    
    # Klasyfikacja
    severity: IncidentSeverity = IncidentSeverity.MEDIUM
    status: IncidentStatus = IncidentStatus.DETECTED
    
    # Wpływ
    affected_systems: List[str] = field(default_factory=list)
    affected_users: int = 0
    affected_countries: List[str] = field(default_factory=list)
    data_breach: bool = False
    personal_data_affected: bool = False
    
    # Przyczyna
    attack_vector: Optional[str] = None  # phishing, malware, ddos, etc.
    threat_actor: Optional[str] = None
    
    # Zgłoszenia
    reported_to_csirt: bool = False
    csirt_report_time: Optional[datetime] = None
    csirt_report_id: Optional[str] = None
    reported_to_authorities: bool = False
    
    # Działania
    remediation_actions: List[str] = field(default_factory=list)
    lessons_learned: Optional[str] = None
    
    def get_response_times(self) -> Dict[str, Optional[timedelta]]:
        """Oblicz czasy reakcji"""
        times = {}
        
        if self.occurrence_time and self.detection_time:
            times["time_to_detect"] = self.detection_time - self.occurrence_time
        
        if self.detection_time and self.containment_time:
            times["time_to_contain"] = self.containment_time - self.detection_time
        
        if self.detection_time and self.resolution_time:
            times["time_to_resolve"] = self.resolution_time - self.detection_time
        
        if self.detection_time and self.csirt_report_time:
            times["time_to_report"] = self.csirt_report_time - self.detection_time
        
        return times
    
    def check_reporting_compliance(self) -> Dict:
        """Sprawdź zgodność z wymogami raportowania"""
        result = {
            "compliant": True,
            "issues": []
        }
        
        if not self.reported_to_csirt:
            result["compliant"] = False
            result["issues"].append("Incydent nie zgłoszony do CSIRT")
        
        if self.csirt_report_time and self.detection_time:
            time_to_report = self.csirt_report_time - self.detection_time
            
            # Wstępne zgłoszenie w 24h
            if time_to_report > timedelta(hours=24):
                result["compliant"] = False
                result["issues"].append(
                    f"Wstępne zgłoszenie po {time_to_report.total_seconds()/3600:.1f}h (wymagane: 24h)"
                )
        
        if self.severity in [IncidentSeverity.CRITICAL, IncidentSeverity.HIGH]:
            if not self.reported_to_authorities:
                result["issues"].append("Poważny incydent - rozważ zgłoszenie do organów ścigania")
        
        return result


@dataclass
class RiskAssessment:
    """Ocena ryzyka cyberbezpieczeństwa"""
    assessment_id: str
    assessment_date: date
    assessor: str
    
    # Obszary
    areas_assessed: List[str] = field(default_factory=list)
    # network, applications, data, physical, personnel, supply_chain
    
    # Wyniki
    risks_identified: List[Dict] = field(default_factory=list)
    # [{id, description, likelihood, impact, risk_level, mitigation}]
    
    critical_risks: int = 0
    high_risks: int = 0
    medium_risks: int = 0
    low_risks: int = 0
    
    # Plan działań
    remediation_plan: List[Dict] = field(default_factory=list)
    # [{risk_id, action, deadline, responsible, status}]
    
    # Następna ocena
    next_assessment_date: Optional[date] = None
    
    def calculate_risk_score(self) -> Decimal:
        """Oblicz ogólny score ryzyka (0-100)"""
        total_risks = self.critical_risks + self.high_risks + self.medium_risks + self.low_risks
        
        if total_risks == 0:
            return Decimal("0")
        
        weighted_score = (
            self.critical_risks * 40 +
            self.high_risks * 30 +
            self.medium_risks * 20 +
            self.low_risks * 10
        )
        
        # Normalizuj do 0-100
        max_score = total_risks * 40
        return Decimal(str(weighted_score / max_score * 100)).quantize(Decimal("0.1"))


@dataclass
class SupplyChainAssessment:
    """Ocena bezpieczeństwa łańcucha dostaw"""
    assessment_date: date
    
    # Dostawcy
    total_suppliers: int = 0
    critical_suppliers: int = 0
    suppliers_assessed: int = 0
    
    # Wyniki
    suppliers_compliant: int = 0
    suppliers_with_issues: int = 0
    suppliers_high_risk: int = 0
    
    # Szczegóły dostawców
    supplier_details: List[Dict] = field(default_factory=list)
    # [{name, category, risk_level, last_audit, certifications, issues}]
    
    # Działania
    actions_required: List[Dict] = field(default_factory=list)


@dataclass
class NIS2ComplianceReport:
    """Raport zgodności NIS2"""
    entity: NIS2Entity
    report_date: date
    reporting_period_start: date
    reporting_period_end: date
    
    # Zarządzanie ryzykiem
    risk_assessment: Optional[RiskAssessment] = None
    risk_management_policy: bool = False
    risk_management_updated: Optional[date] = None
    
    # Incydenty
    incidents: List[SecurityIncident] = field(default_factory=list)
    incidents_reported_on_time: int = 0
    incidents_total: int = 0
    
    # Łańcuch dostaw
    supply_chain_assessment: Optional[SupplyChainAssessment] = None
    
    # Polityki i procedury
    policies: Dict[str, bool] = field(default_factory=dict)
    # incident_response, business_continuity, access_control, encryption, etc.
    
    # Szkolenia
    management_trained: bool = False
    management_training_date: Optional[date] = None
    staff_security_training_percentage: Decimal = Decimal("0")
    
    # Audyty
    last_security_audit: Optional[date] = None
    last_penetration_test: Optional[date] = None
    vulnerabilities_found: int = 0
    vulnerabilities_remediated: int = 0
    
    # Certyfikacje
    certifications: List[str] = field(default_factory=list)
    # ISO27001, SOC2, etc.
    
    def calculate_compliance_score(self) -> Decimal:
        """Oblicz score zgodności (0-100)"""
        score = Decimal("0")
        max_score = Decimal("100")
        
        # Zarządzanie ryzykiem (20 punktów)
        if self.risk_assessment:
            score += Decimal("10")
        if self.risk_management_policy:
            score += Decimal("10")
        
        # Raportowanie incydentów (20 punktów)
        if self.incidents_total > 0:
            ratio = self.incidents_reported_on_time / self.incidents_total
            score += Decimal(str(ratio * 20))
        else:
            score += Decimal("20")  # Brak incydentów = pełne punkty
        
        # Łańcuch dostaw (15 punktów)
        if self.supply_chain_assessment:
            if self.supply_chain_assessment.suppliers_assessed > 0:
                ratio = self.supply_chain_assessment.suppliers_compliant / self.supply_chain_assessment.suppliers_assessed
                score += Decimal(str(ratio * 15))
        
        # Polityki (15 punktów)
        required_policies = [
            "incident_response", "business_continuity", "access_control",
            "encryption", "backup"
        ]
        policies_count = sum(1 for p in required_policies if self.policies.get(p, False))
        score += Decimal(str(policies_count / len(required_policies) * 15))
        
        # Szkolenia (10 punktów)
        if self.management_trained:
            score += Decimal("5")
        if self.staff_security_training_percentage >= 80:
            score += Decimal("5")
        elif self.staff_security_training_percentage >= 50:
            score += Decimal("3")
        
        # Audyty (10 punktów)
        if self.last_security_audit:
            days_since_audit = (date.today() - self.last_security_audit).days
            if days_since_audit <= 365:
                score += Decimal("5")
        if self.last_penetration_test:
            days_since_pentest = (date.today() - self.last_penetration_test).days
            if days_since_pentest <= 365:
                score += Decimal("5")
        
        # Certyfikacje (10 punktów)
        if "ISO27001" in self.certifications:
            score += Decimal("5")
        if any(c in self.certifications for c in ["SOC2", "SOC1"]):
            score += Decimal("5")
        
        return min(score, max_score)


# ============================================================
# NIS2 COMPLIANCE CHECKER
# ============================================================

class NIS2ComplianceChecker:
    """Sprawdzanie zgodności z NIS2"""
    
    # Progi wielkości
    SIZE_THRESHOLDS = {
        "medium": {"employees": 50, "turnover_eur": 10_000_000, "balance_eur": 10_000_000},
        "large": {"employees": 250, "turnover_eur": 50_000_000, "balance_eur": 43_000_000}
    }
    
    # Terminy
    DIRECTIVE_DATE = date(2024, 10, 17)
    
    @classmethod
    def determine_category(
        cls,
        sector: NIS2Sector,
        employees: int,
        turnover_eur: Decimal,
        balance_eur: Decimal
    ) -> EntityCategory:
        """Określ kategorię podmiotu"""
        # Sprawdź wielkość
        is_medium = (
            employees >= cls.SIZE_THRESHOLDS["medium"]["employees"] or
            (turnover_eur >= cls.SIZE_THRESHOLDS["medium"]["turnover_eur"] and
             balance_eur >= cls.SIZE_THRESHOLDS["medium"]["balance_eur"])
        )
        
        is_large = (
            employees >= cls.SIZE_THRESHOLDS["large"]["employees"] or
            (turnover_eur >= cls.SIZE_THRESHOLDS["large"]["turnover_eur"] and
             balance_eur >= cls.SIZE_THRESHOLDS["large"]["balance_eur"])
        )
        
        if not is_medium:
            return EntityCategory.NOT_COVERED
        
        # Sektory kluczowe = essential
        if sector in ESSENTIAL_SECTORS:
            return EntityCategory.ESSENTIAL
        
        # Sektory ważne = important (tylko duże firmy)
        if sector in IMPORTANT_SECTORS and is_large:
            return EntityCategory.IMPORTANT
        
        # Średnie firmy w sektorach ważnych
        if sector in IMPORTANT_SECTORS and is_medium:
            return EntityCategory.IMPORTANT
        
        return EntityCategory.NOT_COVERED
    
    @classmethod
    def check_compliance(
        cls,
        entity: NIS2Entity,
        report: NIS2ComplianceReport = None
    ) -> Dict:
        """Sprawdź zgodność z NIS2"""
        results = {
            "entity_name": entity.name,
            "sector": entity.sector.value,
            "category": entity.category.value,
            "covered_by_nis2": entity.category != EntityCategory.NOT_COVERED,
            "check_date": date.today().isoformat(),
            "requirements": {},
            "compliance_score": 0,
            "gaps": [],
            "recommendations": []
        }
        
        if entity.category == EntityCategory.NOT_COVERED:
            results["recommendations"].append(
                "Podmiot nie jest objęty NIS2, ale dobre praktyki są zalecane"
            )
            return results
        
        # Rejestracja
        results["requirements"]["registration"] = {
            "required": True,
            "compliant": entity.registered_with_csirt,
            "details": f"Zarejestrowany: {entity.registration_date}" if entity.registered_with_csirt else "Niezarejestrowany"
        }
        if not entity.registered_with_csirt:
            results["gaps"].append("Brak rejestracji w CSIRT")
            results["recommendations"].append("Zarejestruj podmiot w krajowym CSIRT")
        
        # Kontakt bezpieczeństwa
        results["requirements"]["security_contact"] = {
            "required": True,
            "compliant": bool(entity.security_contact_email),
            "details": entity.security_contact_email or "Brak"
        }
        if not entity.security_contact_email:
            results["gaps"].append("Brak wyznaczonego kontaktu ds. bezpieczeństwa")
        
        if report:
            # Zarządzanie ryzykiem
            results["requirements"]["risk_management"] = {
                "required": True,
                "compliant": report.risk_management_policy and report.risk_assessment is not None,
                "details": "Polityka i ocena ryzyka" if report.risk_management_policy else "Brak"
            }
            if not report.risk_management_policy:
                results["gaps"].append("Brak polityki zarządzania ryzykiem")
            if not report.risk_assessment:
                results["gaps"].append("Brak oceny ryzyka cyberbezpieczeństwa")
            
            # Szkolenia zarządu
            results["requirements"]["management_training"] = {
                "required": True,
                "compliant": report.management_trained,
                "details": f"Szkolenie: {report.management_training_date}" if report.management_trained else "Brak"
            }
            if not report.management_trained:
                results["gaps"].append("Zarząd nie przeszedł szkolenia z cyberbezpieczeństwa")
                results["recommendations"].append("Przeprowadź szkolenie zarządu z NIS2")
            
            # Polityki
            required_policies = ["incident_response", "business_continuity", "access_control"]
            missing_policies = [p for p in required_policies if not report.policies.get(p)]
            results["requirements"]["policies"] = {
                "required": True,
                "compliant": len(missing_policies) == 0,
                "details": f"Brakujące: {', '.join(missing_policies)}" if missing_policies else "Wszystkie wymagane"
            }
            for p in missing_policies:
                results["gaps"].append(f"Brak polityki: {p}")
            
            # Audyty
            audit_current = (
                report.last_security_audit and 
                (date.today() - report.last_security_audit).days <= 365
            )
            results["requirements"]["security_audit"] = {
                "required": True,
                "compliant": audit_current,
                "details": f"Ostatni: {report.last_security_audit}" if report.last_security_audit else "Brak"
            }
            if not audit_current:
                results["gaps"].append("Brak aktualnego audytu bezpieczeństwa (wymagany co 12 miesięcy)")
                results["recommendations"].append("Przeprowadź audyt bezpieczeństwa")
            
            # Score
            results["compliance_score"] = float(report.calculate_compliance_score())
        
        # Podsumowanie
        total_requirements = len([r for r in results["requirements"].values() if r["required"]])
        compliant_requirements = len([r for r in results["requirements"].values() if r.get("compliant")])
        
        results["summary"] = {
            "total_requirements": total_requirements,
            "compliant": compliant_requirements,
            "gaps_count": len(results["gaps"]),
            "overall_compliant": len(results["gaps"]) == 0
        }
        
        return results
    
    @classmethod
    def get_incident_reporting_requirements(cls, severity: IncidentSeverity) -> Dict:
        """Pobierz wymagania dotyczące raportowania incydentu"""
        requirements = {
            "early_warning": {
                "deadline_hours": 24,
                "description": "Wstępne powiadomienie CSIRT w ciągu 24 godzin"
            },
            "incident_notification": {
                "deadline_hours": 72,
                "description": "Pełne zgłoszenie incydentu w ciągu 72 godzin"
            },
            "final_report": {
                "deadline_days": 30,
                "description": "Raport końcowy w ciągu 1 miesiąca (lub po zamknięciu incydentu)"
            }
        }
        
        if severity == IncidentSeverity.CRITICAL:
            requirements["immediate_notification"] = {
                "deadline_hours": 4,
                "description": "Natychmiastowe powiadomienie dla incydentów krytycznych"
            }
        
        return requirements


# ============================================================
# INCIDENT REPORTER
# ============================================================

class NIS2IncidentReporter:
    """Generator raportów incydentów NIS2"""
    
    @staticmethod
    def generate_early_warning(incident: SecurityIncident) -> Dict:
        """Generuj wstępne powiadomienie (24h)"""
        return {
            "report_type": "early_warning",
            "incident_id": incident.incident_id,
            "detection_time": incident.detection_time.isoformat(),
            "severity": incident.severity.value,
            "brief_description": incident.title,
            "suspected_cause": incident.attack_vector,
            "cross_border": len(incident.affected_countries) > 1,
            "affected_countries": incident.affected_countries,
            "initial_assessment": {
                "data_breach_suspected": incident.data_breach,
                "personal_data_involved": incident.personal_data_affected,
                "estimated_impact": incident.affected_users
            },
            "generated_at": datetime.now().isoformat()
        }
    
    @staticmethod
    def generate_incident_notification(incident: SecurityIncident) -> Dict:
        """Generuj pełne zgłoszenie incydentu (72h)"""
        response_times = incident.get_response_times()
        
        return {
            "report_type": "incident_notification",
            "incident_id": incident.incident_id,
            "title": incident.title,
            "description": incident.description,
            "timeline": {
                "occurrence": incident.occurrence_time.isoformat() if incident.occurrence_time else None,
                "detection": incident.detection_time.isoformat(),
                "containment": incident.containment_time.isoformat() if incident.containment_time else None
            },
            "classification": {
                "severity": incident.severity.value,
                "status": incident.status.value,
                "attack_vector": incident.attack_vector,
                "threat_actor": incident.threat_actor
            },
            "impact": {
                "affected_systems": incident.affected_systems,
                "affected_users": incident.affected_users,
                "affected_countries": incident.affected_countries,
                "data_breach": incident.data_breach,
                "personal_data_affected": incident.personal_data_affected
            },
            "response": {
                "containment_actions": incident.remediation_actions[:3] if incident.remediation_actions else [],
                "response_times": {
                    k: str(v) for k, v in response_times.items() if v
                }
            },
            "generated_at": datetime.now().isoformat()
        }
    
    @staticmethod
    def generate_final_report(incident: SecurityIncident) -> Dict:
        """Generuj raport końcowy"""
        return {
            "report_type": "final_report",
            "incident_id": incident.incident_id,
            "title": incident.title,
            "executive_summary": incident.description,
            "full_timeline": {
                "occurrence": incident.occurrence_time.isoformat() if incident.occurrence_time else None,
                "detection": incident.detection_time.isoformat(),
                "containment": incident.containment_time.isoformat() if incident.containment_time else None,
                "resolution": incident.resolution_time.isoformat() if incident.resolution_time else None
            },
            "root_cause_analysis": {
                "attack_vector": incident.attack_vector,
                "threat_actor": incident.threat_actor,
                "vulnerabilities_exploited": []
            },
            "total_impact": {
                "systems_affected": len(incident.affected_systems),
                "users_affected": incident.affected_users,
                "countries_affected": incident.affected_countries,
                "data_compromised": incident.data_breach
            },
            "remediation": {
                "actions_taken": incident.remediation_actions,
                "effectiveness": "assessed"
            },
            "lessons_learned": incident.lessons_learned,
            "preventive_measures": [],
            "status": incident.status.value,
            "generated_at": datetime.now().isoformat()
        }


__all__ = [
    'NIS2Sector',
    'EntityCategory',
    'IncidentSeverity',
    'IncidentStatus',
    'ESSENTIAL_SECTORS',
    'IMPORTANT_SECTORS',
    'NIS2Entity',
    'SecurityIncident',
    'RiskAssessment',
    'SupplyChainAssessment',
    'NIS2ComplianceReport',
    'NIS2ComplianceChecker',
    'NIS2IncidentReporter'
]
