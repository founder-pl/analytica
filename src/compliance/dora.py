"""
ANALYTICA Compliance - DORA
============================

Digital Operational Resilience Act (DORA)
Rozporządzenie o cyfrowej odporności operacyjnej sektora finansowego

Obowiązuje od: 17 stycznia 2025

Podmioty objęte:
- Banki i instytucje kredytowe
- Firmy inwestycyjne
- Ubezpieczyciele
- Fundusze inwestycyjne
- Dostawcy usług płatniczych
- Emitenci pieniądza elektronicznego
- Dostawcy usług kryptoaktywów
- Krytyczni dostawcy ICT

Filary DORA:
1. Zarządzanie ryzykiem ICT
2. Raportowanie incydentów ICT
3. Testowanie odporności cyfrowej
4. Zarządzanie ryzykiem stron trzecich ICT
5. Wymiana informacji o zagrożeniach
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

class DORAEntityType(Enum):
    """Typy podmiotów objętych DORA"""
    CREDIT_INSTITUTION = "credit_institution"
    INVESTMENT_FIRM = "investment_firm"
    INSURANCE = "insurance"
    REINSURANCE = "reinsurance"
    IORP = "iorp"  # Instytucje pracowniczych programów emerytalnych
    PAYMENT_INSTITUTION = "payment_institution"
    E_MONEY = "e_money"
    CRYPTO_ASSET = "crypto_asset"
    UCITS = "ucits"  # Fundusze UCITS
    AIFM = "aifm"    # Zarządzający alternatywnymi funduszami
    ICT_PROVIDER = "ict_provider"  # Krytyczny dostawca ICT
    OTHER = "other"


class ICTRiskCategory(Enum):
    """Kategorie ryzyka ICT"""
    AVAILABILITY = "availability"
    INTEGRITY = "integrity"
    CONFIDENTIALITY = "confidentiality"
    AUTHENTICITY = "authenticity"
    CONTINUITY = "continuity"


class TestingType(Enum):
    """Typy testów odporności"""
    VULNERABILITY_ASSESSMENT = "vulnerability_assessment"
    PENETRATION_TEST = "penetration_test"
    TLPT = "tlpt"  # Threat-Led Penetration Testing
    SCENARIO_TESTING = "scenario_testing"
    SOURCE_CODE_REVIEW = "source_code_review"
    COMPATIBILITY_TESTING = "compatibility_testing"
    PERFORMANCE_TESTING = "performance_testing"
    END_TO_END_TESTING = "end_to_end_testing"


class ThirdPartyRiskLevel(Enum):
    """Poziom ryzyka dostawcy ICT"""
    CRITICAL = "critical"
    IMPORTANT = "important"
    STANDARD = "standard"


# ============================================================
# DATA MODELS - ICT RISK MANAGEMENT
# ============================================================

@dataclass
class ICTAsset:
    """Aktywo ICT"""
    asset_id: str
    name: str
    asset_type: str  # hardware, software, network, data, cloud
    description: str
    
    # Klasyfikacja
    criticality: str  # critical, important, standard
    business_function: str
    data_classification: str
    
    # Lokalizacja
    location: str
    cloud_provider: Optional[str] = None
    
    # Odpowiedzialność
    owner: str = ""
    technical_contact: str = ""
    
    # Status
    status: str = "active"
    last_update: Optional[date] = None


@dataclass
class ICTRisk:
    """Ryzyko ICT"""
    risk_id: str
    title: str
    description: str
    category: ICTRiskCategory
    
    # Ocena
    likelihood: int  # 1-5
    impact: int      # 1-5
    risk_score: int  # likelihood * impact
    
    # Powiązania
    affected_assets: List[str] = field(default_factory=list)
    affected_processes: List[str] = field(default_factory=list)
    
    # Kontrole
    existing_controls: List[str] = field(default_factory=list)
    residual_risk_score: int = 0
    
    # Mitygacja
    treatment: str = ""  # accept, mitigate, transfer, avoid
    mitigation_plan: str = ""
    mitigation_deadline: Optional[date] = None
    responsible: str = ""
    
    # Status
    status: str = "open"
    last_review: Optional[date] = None


@dataclass
class ICTRiskFramework:
    """Framework zarządzania ryzykiem ICT"""
    # Polityki
    ict_risk_policy: bool = False
    ict_risk_policy_date: Optional[date] = None
    ict_security_policy: bool = False
    
    # Struktura
    ciso_appointed: bool = False
    ict_risk_function: bool = False
    reporting_lines_defined: bool = False
    
    # Procesy
    risk_assessment_frequency: str = ""  # annual, semi-annual, quarterly
    risk_appetite_defined: bool = False
    risk_tolerance_levels: Dict[str, int] = field(default_factory=dict)
    
    # Zasoby
    ict_assets_inventory: bool = False
    assets_count: int = 0
    critical_assets_count: int = 0
    
    # Ryzyka
    risks: List[ICTRisk] = field(default_factory=list)
    total_risks: int = 0
    critical_risks: int = 0
    high_risks: int = 0


# ============================================================
# DATA MODELS - INCIDENT MANAGEMENT
# ============================================================

@dataclass
class ICTIncident:
    """Incydent ICT wg DORA"""
    incident_id: str
    title: str
    description: str
    
    # Czas
    detection_time: datetime
    occurrence_time: Optional[datetime] = None
    recovery_time: Optional[datetime] = None
    
    # Klasyfikacja DORA
    is_major: bool = False  # Poważny incydent wymaga zgłoszenia
    classification_criteria: Dict[str, bool] = field(default_factory=dict)
    # clients_affected, transactions_affected, reputation_impact, 
    # duration, geographic_spread, data_losses, critical_services
    
    # Wpływ
    affected_clients: int = 0
    affected_transactions: int = 0
    financial_impact_eur: Decimal = Decimal("0")
    affected_services: List[str] = field(default_factory=list)
    
    # Zgłoszenia
    reported_to_authority: bool = False
    report_time: Optional[datetime] = None
    authority_reference: Optional[str] = None
    
    # Status
    status: str = "open"
    root_cause: str = ""
    remediation_actions: List[str] = field(default_factory=list)
    
    def classify_as_major(self) -> Tuple[bool, List[str]]:
        """
        Klasyfikacja jako poważny incydent (Art. 18 DORA)
        
        Kryteria:
        - >10% klientów dotkniętych
        - Wpływ na krytyczne funkcje
        - Czas trwania >2h dla krytycznych usług
        - Straty finansowe >100k EUR
        - Naruszenie danych osobowych
        """
        reasons = []
        
        if self.classification_criteria.get("clients_affected_significant"):
            reasons.append("Znacząca liczba klientów dotkniętych")
        
        if self.classification_criteria.get("critical_services_impacted"):
            reasons.append("Wpływ na krytyczne usługi")
        
        if self.classification_criteria.get("duration_extended"):
            reasons.append("Przedłużony czas trwania")
        
        if self.financial_impact_eur >= 100000:
            reasons.append(f"Straty finansowe: {self.financial_impact_eur} EUR")
        
        if self.classification_criteria.get("data_breach"):
            reasons.append("Naruszenie danych")
        
        if self.classification_criteria.get("geographic_spread"):
            reasons.append("Szeroki zasięg geograficzny")
        
        is_major = len(reasons) >= 2 or self.classification_criteria.get("critical_services_impacted")
        
        return is_major, reasons


# ============================================================
# DATA MODELS - RESILIENCE TESTING
# ============================================================

@dataclass
class ResilienceTest:
    """Test odporności cyfrowej"""
    test_id: str
    test_type: TestingType
    test_date: date
    
    # Zakres
    scope: str
    systems_tested: List[str] = field(default_factory=list)
    
    # Wykonawca
    internal: bool = True
    external_provider: Optional[str] = None
    tester_certified: bool = False
    
    # Wyniki
    findings_critical: int = 0
    findings_high: int = 0
    findings_medium: int = 0
    findings_low: int = 0
    
    findings_details: List[Dict] = field(default_factory=list)
    # [{id, severity, description, recommendation, status}]
    
    # Remediacja
    remediation_deadline: Optional[date] = None
    remediation_complete: bool = False
    
    # Raport
    report_available: bool = False
    report_date: Optional[date] = None


@dataclass
class TLPTProgram:
    """Program TLPT (Threat-Led Penetration Testing)"""
    # TLPT wymagany dla dużych instytucji finansowych co 3 lata
    
    last_tlpt_date: Optional[date] = None
    next_tlpt_due: Optional[date] = None
    
    # Zakres
    critical_functions_in_scope: List[str] = field(default_factory=list)
    third_parties_in_scope: List[str] = field(default_factory=list)
    
    # Wykonawca
    threat_intelligence_provider: str = ""
    red_team_provider: str = ""
    providers_certified: bool = False
    
    # Wyniki ostatniego TLPT
    last_findings: List[Dict] = field(default_factory=list)
    remediation_status: str = ""


# ============================================================
# DATA MODELS - THIRD PARTY RISK
# ============================================================

@dataclass
class ICTThirdParty:
    """Dostawca usług ICT"""
    provider_id: str
    name: str
    country: str
    
    # Klasyfikacja
    risk_level: ThirdPartyRiskLevel
    services_provided: List[str] = field(default_factory=list)
    critical_or_important_functions: bool = False
    
    # Umowa
    contract_start_date: Optional[date] = None
    contract_end_date: Optional[date] = None
    contract_compliant_with_dora: bool = False
    
    # Wymagane klauzule DORA (Art. 30)
    contractual_requirements: Dict[str, bool] = field(default_factory=dict)
    # service_levels, audit_rights, exit_strategy, subcontracting,
    # data_location, incident_reporting, business_continuity
    
    # Ocena
    last_assessment_date: Optional[date] = None
    assessment_score: int = 0
    issues_identified: List[str] = field(default_factory=list)
    
    # Koncentracja
    dependency_level: str = ""  # high, medium, low
    alternative_providers: List[str] = field(default_factory=list)
    
    # Certyfikacje dostawcy
    certifications: List[str] = field(default_factory=list)


@dataclass
class ThirdPartyRiskRegister:
    """Rejestr ryzyka stron trzecich ICT"""
    last_update: date
    
    # Dostawcy
    total_providers: int = 0
    critical_providers: int = 0
    important_providers: int = 0
    
    providers: List[ICTThirdParty] = field(default_factory=list)
    
    # Koncentracja
    concentration_risks: List[Dict] = field(default_factory=list)
    # [{provider, service, dependency_percentage, risk}]
    
    # Exit strategie
    exit_strategies_documented: int = 0
    
    # Zgłoszenia do regulatora
    register_submitted: bool = False
    submission_date: Optional[date] = None


# ============================================================
# DATA MODELS - COMPLIANCE REPORT
# ============================================================

@dataclass
class DORAComplianceReport:
    """Raport zgodności DORA"""
    entity_name: str
    entity_type: DORAEntityType
    report_date: date
    reporting_period: str
    
    # Filar 1: Zarządzanie ryzykiem ICT
    ict_risk_framework: Optional[ICTRiskFramework] = None
    
    # Filar 2: Raportowanie incydentów
    incidents_total: int = 0
    major_incidents: int = 0
    incidents_reported_on_time: int = 0
    
    # Filar 3: Testowanie
    tests_conducted: List[ResilienceTest] = field(default_factory=list)
    tlpt_program: Optional[TLPTProgram] = None
    
    # Filar 4: Strony trzecie
    third_party_register: Optional[ThirdPartyRiskRegister] = None
    
    # Filar 5: Wymiana informacji
    information_sharing_arrangements: bool = False
    threat_intelligence_feeds: List[str] = field(default_factory=list)
    
    # Ogólne
    board_oversight: bool = False
    dora_training_completed: bool = False
    
    def calculate_pillar_scores(self) -> Dict[str, Decimal]:
        """Oblicz score dla każdego filaru"""
        scores = {}
        
        # Filar 1: Zarządzanie ryzykiem (0-100)
        if self.ict_risk_framework:
            f1_score = Decimal("0")
            if self.ict_risk_framework.ict_risk_policy:
                f1_score += Decimal("20")
            if self.ict_risk_framework.ciso_appointed:
                f1_score += Decimal("20")
            if self.ict_risk_framework.ict_assets_inventory:
                f1_score += Decimal("20")
            if self.ict_risk_framework.risk_appetite_defined:
                f1_score += Decimal("20")
            if self.ict_risk_framework.ict_risk_function:
                f1_score += Decimal("20")
            scores["pillar_1_ict_risk"] = f1_score
        else:
            scores["pillar_1_ict_risk"] = Decimal("0")
        
        # Filar 2: Incydenty (0-100)
        if self.incidents_total > 0:
            report_ratio = self.incidents_reported_on_time / self.incidents_total
            scores["pillar_2_incidents"] = Decimal(str(report_ratio * 100))
        else:
            scores["pillar_2_incidents"] = Decimal("100")
        
        # Filar 3: Testowanie (0-100)
        f3_score = Decimal("0")
        has_vuln_scan = any(t.test_type == TestingType.VULNERABILITY_ASSESSMENT for t in self.tests_conducted)
        has_pentest = any(t.test_type == TestingType.PENETRATION_TEST for t in self.tests_conducted)
        has_tlpt = self.tlpt_program and self.tlpt_program.last_tlpt_date
        
        if has_vuln_scan:
            f3_score += Decimal("30")
        if has_pentest:
            f3_score += Decimal("40")
        if has_tlpt:
            f3_score += Decimal("30")
        scores["pillar_3_testing"] = f3_score
        
        # Filar 4: Strony trzecie (0-100)
        if self.third_party_register:
            f4_score = Decimal("0")
            if self.third_party_register.total_providers > 0:
                assessed_ratio = len([p for p in self.third_party_register.providers if p.last_assessment_date]) / self.third_party_register.total_providers
                f4_score += Decimal(str(assessed_ratio * 50))
            if self.third_party_register.register_submitted:
                f4_score += Decimal("25")
            if self.third_party_register.exit_strategies_documented > 0:
                f4_score += Decimal("25")
            scores["pillar_4_third_party"] = f4_score
        else:
            scores["pillar_4_third_party"] = Decimal("0")
        
        # Filar 5: Wymiana informacji (0-100)
        f5_score = Decimal("0")
        if self.information_sharing_arrangements:
            f5_score += Decimal("50")
        if self.threat_intelligence_feeds:
            f5_score += Decimal("50")
        scores["pillar_5_information_sharing"] = f5_score
        
        # Średnia
        scores["overall"] = sum(scores.values()) / len(scores)
        
        return scores


# ============================================================
# DORA COMPLIANCE CHECKER
# ============================================================

class DORAComplianceChecker:
    """Sprawdzanie zgodności z DORA"""
    
    EFFECTIVE_DATE = date(2025, 1, 17)
    
    # Wymagania testowania według wielkości
    TESTING_REQUIREMENTS = {
        "large": {
            "vulnerability_scan": "quarterly",
            "penetration_test": "annual",
            "tlpt": "every_3_years"
        },
        "medium": {
            "vulnerability_scan": "semi_annual",
            "penetration_test": "every_2_years",
            "tlpt": None
        },
        "small": {
            "vulnerability_scan": "annual",
            "penetration_test": "every_3_years",
            "tlpt": None
        }
    }
    
    @classmethod
    def is_covered(cls, entity_type: DORAEntityType) -> bool:
        """Sprawdź czy podmiot jest objęty DORA"""
        return entity_type != DORAEntityType.OTHER
    
    @classmethod
    def check_compliance(
        cls,
        report: DORAComplianceReport
    ) -> Dict:
        """Sprawdź zgodność z DORA"""
        results = {
            "entity": report.entity_name,
            "entity_type": report.entity_type.value,
            "check_date": date.today().isoformat(),
            "effective_date": cls.EFFECTIVE_DATE.isoformat(),
            "days_since_effective": (date.today() - cls.EFFECTIVE_DATE).days,
            "pillars": {},
            "gaps": [],
            "recommendations": [],
            "overall_compliant": True
        }
        
        scores = report.calculate_pillar_scores()
        
        # Filar 1: Zarządzanie ryzykiem ICT
        pillar1 = {
            "name": "ICT Risk Management",
            "score": float(scores["pillar_1_ict_risk"]),
            "requirements": []
        }
        
        if report.ict_risk_framework:
            rf = report.ict_risk_framework
            if not rf.ict_risk_policy:
                results["gaps"].append("Brak polityki zarządzania ryzykiem ICT")
                pillar1["requirements"].append({"item": "ICT Risk Policy", "status": "missing"})
            if not rf.ciso_appointed:
                results["gaps"].append("Brak wyznaczonego CISO / osoby odpowiedzialnej za bezpieczeństwo ICT")
                pillar1["requirements"].append({"item": "CISO/Security Officer", "status": "missing"})
            if not rf.ict_assets_inventory:
                results["gaps"].append("Brak inwentaryzacji aktywów ICT")
                pillar1["requirements"].append({"item": "ICT Assets Inventory", "status": "missing"})
        else:
            results["gaps"].append("Brak framework zarządzania ryzykiem ICT")
        
        results["pillars"]["pillar_1"] = pillar1
        
        # Filar 2: Raportowanie incydentów
        pillar2 = {
            "name": "ICT Incident Reporting",
            "score": float(scores["pillar_2_incidents"]),
            "requirements": []
        }
        
        if report.major_incidents > report.incidents_reported_on_time:
            results["gaps"].append(
                f"Nie wszystkie poważne incydenty zgłoszone na czas ({report.incidents_reported_on_time}/{report.major_incidents})"
            )
        
        results["pillars"]["pillar_2"] = pillar2
        
        # Filar 3: Testowanie
        pillar3 = {
            "name": "Digital Operational Resilience Testing",
            "score": float(scores["pillar_3_testing"]),
            "requirements": []
        }
        
        recent_tests = [t for t in report.tests_conducted if (date.today() - t.test_date).days <= 365]
        has_recent_vuln = any(t.test_type == TestingType.VULNERABILITY_ASSESSMENT for t in recent_tests)
        has_recent_pentest = any(t.test_type == TestingType.PENETRATION_TEST for t in recent_tests)
        
        if not has_recent_vuln:
            results["gaps"].append("Brak aktualnego skanowania podatności (wymagane min. rocznie)")
            pillar3["requirements"].append({"item": "Vulnerability Assessment", "status": "overdue"})
        
        if not has_recent_pentest:
            results["recommendations"].append("Przeprowadź testy penetracyjne")
            pillar3["requirements"].append({"item": "Penetration Test", "status": "recommended"})
        
        results["pillars"]["pillar_3"] = pillar3
        
        # Filar 4: Strony trzecie
        pillar4 = {
            "name": "ICT Third-Party Risk Management",
            "score": float(scores["pillar_4_third_party"]),
            "requirements": []
        }
        
        if report.third_party_register:
            tpr = report.third_party_register
            
            # Krytyczni dostawcy
            critical_without_assessment = [
                p for p in tpr.providers 
                if p.risk_level == ThirdPartyRiskLevel.CRITICAL and not p.last_assessment_date
            ]
            if critical_without_assessment:
                results["gaps"].append(
                    f"{len(critical_without_assessment)} krytycznych dostawców bez oceny"
                )
            
            # Klauzule umowne
            non_compliant_contracts = [
                p for p in tpr.providers 
                if p.critical_or_important_functions and not p.contract_compliant_with_dora
            ]
            if non_compliant_contracts:
                results["gaps"].append(
                    f"{len(non_compliant_contracts)} umów z krytycznymi dostawcami niezgodnych z DORA"
                )
                results["recommendations"].append("Renegocjuj umowy z krytycznymi dostawcami ICT wg Art. 30 DORA")
            
            if not tpr.register_submitted:
                results["gaps"].append("Rejestr dostawców ICT nie został zgłoszony do regulatora")
        else:
            results["gaps"].append("Brak rejestru dostawców ICT")
        
        results["pillars"]["pillar_4"] = pillar4
        
        # Filar 5: Wymiana informacji
        pillar5 = {
            "name": "Information Sharing",
            "score": float(scores["pillar_5_information_sharing"]),
            "requirements": []
        }
        
        if not report.information_sharing_arrangements:
            results["recommendations"].append("Rozważ dołączenie do programu wymiany informacji o zagrożeniach")
        
        results["pillars"]["pillar_5"] = pillar5
        
        # Wymagania zarządcze
        if not report.board_oversight:
            results["gaps"].append("Brak nadzoru zarządu nad ryzykiem ICT")
        
        if not report.dora_training_completed:
            results["gaps"].append("Zarząd nie ukończył szkolenia z DORA")
            results["recommendations"].append("Przeprowadź szkolenie zarządu z wymogów DORA")
        
        # Podsumowanie
        results["overall_score"] = float(scores["overall"])
        results["overall_compliant"] = len(results["gaps"]) == 0
        results["gaps_count"] = len(results["gaps"])
        results["recommendations_count"] = len(results["recommendations"])
        
        return results
    
    @classmethod
    def get_incident_reporting_timeline(cls) -> Dict:
        """Harmonogram raportowania incydentów DORA"""
        return {
            "initial_notification": {
                "deadline": "4 hours",
                "description": "Wstępne powiadomienie o poważnym incydencie",
                "content": ["Rodzaj incydentu", "Wstępna ocena wpływu", "Czas wykrycia"]
            },
            "intermediate_report": {
                "deadline": "72 hours",
                "description": "Raport pośredni",
                "content": ["Status incydentu", "Podjęte działania", "Zaktualizowana ocena wpływu"]
            },
            "final_report": {
                "deadline": "1 month (or after resolution)",
                "description": "Raport końcowy",
                "content": ["Analiza przyczyn", "Pełna ocena wpływu", "Działania naprawcze", "Wnioski"]
            }
        }


# ============================================================
# CONTRACT REQUIREMENTS CHECKER
# ============================================================

class DORAContractChecker:
    """Sprawdzanie zgodności umów z dostawcami ICT (Art. 30 DORA)"""
    
    REQUIRED_CLAUSES = [
        "service_level_agreements",
        "security_requirements",
        "data_location",
        "audit_rights",
        "incident_notification",
        "business_continuity",
        "exit_strategy",
        "subcontracting_restrictions",
        "cooperation_with_authorities",
        "termination_rights"
    ]
    
    @classmethod
    def check_contract(
        cls,
        provider: ICTThirdParty
    ) -> Dict:
        """Sprawdź zgodność umowy z Art. 30 DORA"""
        result = {
            "provider": provider.name,
            "risk_level": provider.risk_level.value,
            "critical_function": provider.critical_or_important_functions,
            "clauses": {},
            "compliant": True,
            "missing_clauses": [],
            "recommendations": []
        }
        
        for clause in cls.REQUIRED_CLAUSES:
            is_present = provider.contractual_requirements.get(clause, False)
            result["clauses"][clause] = is_present
            
            if not is_present:
                result["missing_clauses"].append(clause)
                if provider.critical_or_important_functions:
                    result["compliant"] = False
        
        if result["missing_clauses"]:
            result["recommendations"].append(
                f"Dodaj brakujące klauzule do umowy: {', '.join(result['missing_clauses'])}"
            )
        
        # Dodatkowe wymagania dla krytycznych dostawców
        if provider.critical_or_important_functions:
            if not provider.certifications:
                result["recommendations"].append("Wymagaj certyfikacji bezpieczeństwa od dostawcy (ISO27001, SOC2)")
            
            if (date.today() - (provider.last_assessment_date or date.min)).days > 365:
                result["recommendations"].append("Przeprowadź roczną ocenę dostawcy")
        
        return result


__all__ = [
    'DORAEntityType',
    'ICTRiskCategory',
    'TestingType',
    'ThirdPartyRiskLevel',
    'ICTAsset',
    'ICTRisk',
    'ICTRiskFramework',
    'ICTIncident',
    'ResilienceTest',
    'TLPTProgram',
    'ICTThirdParty',
    'ThirdPartyRiskRegister',
    'DORAComplianceReport',
    'DORAComplianceChecker',
    'DORAContractChecker'
]
