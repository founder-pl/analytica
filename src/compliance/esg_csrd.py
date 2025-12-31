"""
ANALYTICA Compliance - ESG & CSRD Reporting
=============================================

Corporate Sustainability Reporting Directive (CSRD)
Obowiązkowe raportowanie ESG od 2025-2026

Zakres:
- Environmental (Środowisko)
- Social (Społeczność)  
- Governance (Zarządzanie)

Standardy: ESRS (European Sustainability Reporting Standards)

Terminy:
- 2025: Duże spółki giełdowe (>500 pracowników)
- 2026: Duże przedsiębiorstwa (>250 pracowników, >40M EUR)
- 2027: MŚP giełdowe
"""

from typing import Any, Dict, List, Optional, Union, Tuple
from dataclasses import dataclass, field
from datetime import datetime, date
from decimal import Decimal
from enum import Enum
import json


# ============================================================
# ENUMS & CONSTANTS
# ============================================================

class ESGCategory(Enum):
    """Kategorie ESG"""
    ENVIRONMENTAL = "E"
    SOCIAL = "S"
    GOVERNANCE = "G"


class ESRSStandard(Enum):
    """Standardy ESRS"""
    # Cross-cutting
    ESRS_1 = "ESRS 1"  # General requirements
    ESRS_2 = "ESRS 2"  # General disclosures
    
    # Environmental
    E1 = "E1"  # Climate change
    E2 = "E2"  # Pollution
    E3 = "E3"  # Water and marine resources
    E4 = "E4"  # Biodiversity and ecosystems
    E5 = "E5"  # Resource use and circular economy
    
    # Social
    S1 = "S1"  # Own workforce
    S2 = "S2"  # Workers in value chain
    S3 = "S3"  # Affected communities
    S4 = "S4"  # Consumers and end-users
    
    # Governance
    G1 = "G1"  # Business conduct


class EmissionScope(Enum):
    """Zakresy emisji GHG"""
    SCOPE_1 = "scope_1"  # Bezpośrednie emisje
    SCOPE_2 = "scope_2"  # Pośrednie (energia)
    SCOPE_3 = "scope_3"  # Pośrednie (łańcuch wartości)


class CSRDEntitySize(Enum):
    """Wielkość podmiotu wg CSRD"""
    LARGE_PIE = "LARGE_PIE"        # Duża spółka interesu publicznego
    LARGE = "LARGE"                # Duże przedsiębiorstwo
    SME_LISTED = "SME_LISTED"      # MŚP giełdowe
    SME = "SME"                    # MŚP (dobrowolne)
    MICRO = "MICRO"                # Mikroprzedsiębiorstwo


# ============================================================
# DATA MODELS - ENVIRONMENTAL
# ============================================================

@dataclass
class GHGEmission:
    """Emisja gazów cieplarnianych"""
    scope: EmissionScope
    amount_tonnes_co2e: Decimal
    year: int
    source: str
    methodology: str = "GHG Protocol"
    verified: bool = False
    verifier: Optional[str] = None
    
    # Szczegóły
    co2: Optional[Decimal] = None
    ch4: Optional[Decimal] = None
    n2o: Optional[Decimal] = None
    hfcs: Optional[Decimal] = None
    pfcs: Optional[Decimal] = None
    sf6: Optional[Decimal] = None
    nf3: Optional[Decimal] = None


@dataclass
class EnergyConsumption:
    """Zużycie energii"""
    year: int
    total_mwh: Decimal
    renewable_mwh: Decimal
    non_renewable_mwh: Decimal
    renewable_percentage: Decimal
    
    # Szczegóły
    electricity_mwh: Optional[Decimal] = None
    heating_mwh: Optional[Decimal] = None
    cooling_mwh: Optional[Decimal] = None
    fuel_mwh: Optional[Decimal] = None


@dataclass
class WaterConsumption:
    """Zużycie wody"""
    year: int
    total_m3: Decimal
    withdrawn_m3: Decimal
    discharged_m3: Decimal
    recycled_m3: Decimal
    water_stress_areas: bool = False


@dataclass
class WasteGeneration:
    """Generowanie odpadów"""
    year: int
    total_tonnes: Decimal
    hazardous_tonnes: Decimal
    non_hazardous_tonnes: Decimal
    recycled_tonnes: Decimal
    recycling_rate: Decimal


@dataclass
class EnvironmentalData:
    """Dane środowiskowe (E)"""
    emissions: List[GHGEmission] = field(default_factory=list)
    energy: List[EnergyConsumption] = field(default_factory=list)
    water: List[WaterConsumption] = field(default_factory=list)
    waste: List[WasteGeneration] = field(default_factory=list)
    
    # Cele
    net_zero_target_year: Optional[int] = None
    science_based_targets: bool = False
    sbti_commitment: Optional[str] = None
    
    # Dodatkowe
    biodiversity_policy: bool = False
    circular_economy_initiatives: List[str] = field(default_factory=list)


# ============================================================
# DATA MODELS - SOCIAL
# ============================================================

@dataclass
class WorkforceMetrics:
    """Metryki pracownicze"""
    year: int
    total_employees: int
    full_time: int
    part_time: int
    contractors: int
    
    # Różnorodność
    female_percentage: Decimal
    female_management_percentage: Decimal
    female_board_percentage: Decimal
    
    # Wiek
    under_30_percentage: Decimal
    between_30_50_percentage: Decimal
    over_50_percentage: Decimal
    
    # Inne
    turnover_rate: Decimal
    new_hires: int
    training_hours_per_employee: Decimal
    
    # Wynagrodzenia
    gender_pay_gap: Optional[Decimal] = None
    ceo_to_median_pay_ratio: Optional[Decimal] = None


@dataclass
class HealthSafetyMetrics:
    """BHP"""
    year: int
    fatalities: int
    recordable_injuries: int
    lost_time_injuries: int
    ltir: Decimal  # Lost Time Injury Rate
    trir: Decimal  # Total Recordable Injury Rate
    near_misses: int
    safety_training_hours: Decimal


@dataclass
class SocialData:
    """Dane społeczne (S)"""
    workforce: List[WorkforceMetrics] = field(default_factory=list)
    health_safety: List[HealthSafetyMetrics] = field(default_factory=list)
    
    # Polityki
    human_rights_policy: bool = False
    diversity_policy: bool = False
    anti_discrimination_policy: bool = False
    whistleblower_policy: bool = False
    
    # Społeczność
    community_investment_eur: Decimal = Decimal("0")
    volunteer_hours: Decimal = Decimal("0")
    local_hiring_percentage: Decimal = Decimal("0")


# ============================================================
# DATA MODELS - GOVERNANCE
# ============================================================

@dataclass
class BoardComposition:
    """Skład zarządu"""
    year: int
    total_members: int
    independent_members: int
    female_members: int
    
    # Komitety
    audit_committee: bool = True
    risk_committee: bool = False
    sustainability_committee: bool = False
    remuneration_committee: bool = False
    
    # Doświadczenie
    members_with_esg_experience: int = 0
    average_tenure_years: Decimal = Decimal("0")


@dataclass
class EthicsCompliance:
    """Etyka i zgodność"""
    year: int
    
    # Polityki
    code_of_conduct: bool = True
    anti_corruption_policy: bool = True
    anti_bribery_training_percentage: Decimal = Decimal("0")
    
    # Incydenty
    corruption_incidents: int = 0
    confirmed_corruption_cases: int = 0
    legal_proceedings: int = 0
    fines_eur: Decimal = Decimal("0")
    
    # Audyt
    internal_audit: bool = True
    external_audit: bool = True


@dataclass
class GovernanceData:
    """Dane zarządcze (G)"""
    board: List[BoardComposition] = field(default_factory=list)
    ethics: List[EthicsCompliance] = field(default_factory=list)
    
    # Polityki
    sustainability_governance: bool = False
    esg_linked_remuneration: bool = False
    stakeholder_engagement: bool = False
    
    # Łańcuch dostaw
    supplier_code_of_conduct: bool = False
    supplier_audits: int = 0
    suppliers_assessed_on_esg: int = 0


# ============================================================
# ESG REPORT
# ============================================================

@dataclass
class ESGReport:
    """Kompletny raport ESG/CSRD"""
    # Identyfikacja
    company_name: str
    reporting_year: int
    entity_size: CSRDEntitySize
    
    # Dane ESG
    environmental: EnvironmentalData
    social: SocialData
    governance: GovernanceData
    
    # Metadane
    reporting_period_start: date = None
    reporting_period_end: date = None
    prepared_by: str = ""
    approved_by: str = ""
    approval_date: Optional[date] = None
    
    # Weryfikacja
    externally_assured: bool = False
    assurance_provider: Optional[str] = None
    assurance_standard: Optional[str] = None  # ISAE 3000
    
    # ESRS
    esrs_standards_applied: List[ESRSStandard] = field(default_factory=list)
    materiality_assessment_done: bool = False
    double_materiality: bool = False
    
    def __post_init__(self):
        if self.reporting_period_start is None:
            self.reporting_period_start = date(self.reporting_year, 1, 1)
        if self.reporting_period_end is None:
            self.reporting_period_end = date(self.reporting_year, 12, 31)
    
    def get_esg_score(self) -> Dict[str, Decimal]:
        """Oblicz uproszczony score ESG"""
        scores = {}
        
        # E score (0-100)
        e_score = Decimal("50")
        if self.environmental.emissions:
            latest = max(self.environmental.emissions, key=lambda x: x.year)
            if latest.verified:
                e_score += Decimal("10")
        if self.environmental.science_based_targets:
            e_score += Decimal("15")
        if self.environmental.net_zero_target_year:
            e_score += Decimal("10")
        scores["E"] = min(e_score, Decimal("100"))
        
        # S score (0-100)
        s_score = Decimal("50")
        if self.social.workforce:
            latest = max(self.social.workforce, key=lambda x: x.year)
            if latest.female_management_percentage >= 30:
                s_score += Decimal("10")
            if latest.gender_pay_gap and latest.gender_pay_gap < 5:
                s_score += Decimal("10")
        if self.social.human_rights_policy:
            s_score += Decimal("10")
        scores["S"] = min(s_score, Decimal("100"))
        
        # G score (0-100)
        g_score = Decimal("50")
        if self.governance.board:
            latest = max(self.governance.board, key=lambda x: x.year)
            if latest.independent_members / latest.total_members >= 0.5:
                g_score += Decimal("15")
            if latest.sustainability_committee:
                g_score += Decimal("10")
        if self.governance.ethics:
            latest = max(self.governance.ethics, key=lambda x: x.year)
            if latest.corruption_incidents == 0:
                g_score += Decimal("10")
        scores["G"] = min(g_score, Decimal("100"))
        
        # Total
        scores["Total"] = (scores["E"] + scores["S"] + scores["G"]) / 3
        
        return scores


# ============================================================
# CSRD COMPLIANCE CHECKER
# ============================================================

class CSRDComplianceChecker:
    """Sprawdzanie zgodności z CSRD"""
    
    # Progi CSRD
    THRESHOLDS = {
        CSRDEntitySize.LARGE_PIE: {
            "employees": 500,
            "revenue_eur": 0,
            "assets_eur": 0,
            "mandatory_from": date(2025, 1, 1),
            "first_report_year": 2024
        },
        CSRDEntitySize.LARGE: {
            "employees": 250,
            "revenue_eur": 40_000_000,
            "assets_eur": 20_000_000,
            "mandatory_from": date(2026, 1, 1),
            "first_report_year": 2025
        },
        CSRDEntitySize.SME_LISTED: {
            "employees": 10,
            "revenue_eur": 700_000,
            "assets_eur": 350_000,
            "mandatory_from": date(2027, 1, 1),
            "first_report_year": 2026
        }
    }
    
    @classmethod
    def determine_entity_size(
        cls,
        employees: int,
        revenue_eur: Decimal,
        assets_eur: Decimal,
        is_listed: bool = False,
        is_pie: bool = False  # Public Interest Entity
    ) -> CSRDEntitySize:
        """Określ kategorię podmiotu"""
        if is_pie and employees >= 500:
            return CSRDEntitySize.LARGE_PIE
        
        # Duże przedsiębiorstwo - 2 z 3 kryteriów
        large_criteria = [
            employees >= 250,
            revenue_eur >= 40_000_000,
            assets_eur >= 20_000_000
        ]
        if sum(large_criteria) >= 2:
            return CSRDEntitySize.LARGE
        
        if is_listed:
            sme_criteria = [
                employees >= 10,
                revenue_eur >= 700_000,
                assets_eur >= 350_000
            ]
            if sum(sme_criteria) >= 2:
                return CSRDEntitySize.SME_LISTED
        
        if employees < 10:
            return CSRDEntitySize.MICRO
        
        return CSRDEntitySize.SME
    
    @classmethod
    def check_compliance(
        cls,
        entity_size: CSRDEntitySize,
        has_report: bool = False,
        report_year: Optional[int] = None,
        esrs_applied: List[ESRSStandard] = None,
        externally_assured: bool = False
    ) -> Dict:
        """Sprawdź zgodność z CSRD"""
        thresholds = cls.THRESHOLDS.get(entity_size)
        
        if not thresholds:
            return {
                "compliant": True,
                "mandatory": False,
                "entity_size": entity_size.value,
                "message": "Raportowanie CSRD nie jest obowiązkowe dla tej kategorii podmiotu"
            }
        
        today = date.today()
        mandatory_from = thresholds["mandatory_from"]
        first_report_year = thresholds["first_report_year"]
        
        is_mandatory = today >= mandatory_from
        
        # Wymagane standardy ESRS
        required_esrs = [ESRSStandard.ESRS_1, ESRSStandard.ESRS_2]
        if entity_size in [CSRDEntitySize.LARGE_PIE, CSRDEntitySize.LARGE]:
            required_esrs.extend([
                ESRSStandard.E1, ESRSStandard.S1, ESRSStandard.G1
            ])
        
        esrs_applied = esrs_applied or []
        missing_esrs = [e for e in required_esrs if e not in esrs_applied]
        
        compliant = (
            not is_mandatory or
            (has_report and report_year and report_year >= first_report_year and not missing_esrs)
        )
        
        return {
            "compliant": compliant,
            "mandatory": is_mandatory,
            "entity_size": entity_size.value,
            "mandatory_from": mandatory_from.isoformat(),
            "first_report_year": first_report_year,
            "days_to_mandatory": (mandatory_from - today).days if not is_mandatory else 0,
            "has_report": has_report,
            "report_year": report_year,
            "externally_assured": externally_assured,
            "required_esrs": [e.value for e in required_esrs],
            "applied_esrs": [e.value for e in esrs_applied],
            "missing_esrs": [e.value for e in missing_esrs],
            "recommendations": cls._get_recommendations(
                is_mandatory, has_report, missing_esrs, externally_assured
            )
        }
    
    @staticmethod
    def _get_recommendations(
        is_mandatory: bool,
        has_report: bool,
        missing_esrs: List[ESRSStandard],
        externally_assured: bool
    ) -> List[str]:
        """Generuj rekomendacje"""
        recommendations = []
        
        if is_mandatory and not has_report:
            recommendations.append("PILNE: Wymagane przygotowanie raportu CSRD")
        
        if missing_esrs:
            recommendations.append(
                f"Uzupełnij raportowanie wg standardów: {', '.join(e.value for e in missing_esrs)}"
            )
        
        if has_report and not externally_assured:
            recommendations.append(
                "Zalecane zewnętrzne poświadczenie raportu (limited assurance)"
            )
        
        if not missing_esrs and has_report:
            recommendations.append("Raportowanie CSRD jest zgodne z wymogami")
        
        return recommendations


# ============================================================
# CARBON CALCULATOR
# ============================================================

class CarbonCalculator:
    """Kalkulator śladu węglowego"""
    
    # Współczynniki emisji (kg CO2e)
    EMISSION_FACTORS = {
        # Energia (per kWh)
        "electricity_pl": Decimal("0.708"),  # Polska - mix energetyczny
        "electricity_eu_avg": Decimal("0.295"),
        "electricity_renewable": Decimal("0"),
        "natural_gas": Decimal("0.202"),  # per kWh
        "heating_oil": Decimal("0.267"),
        
        # Transport (per km)
        "car_petrol": Decimal("0.171"),
        "car_diesel": Decimal("0.168"),
        "car_electric_pl": Decimal("0.053"),
        "train": Decimal("0.041"),
        "bus": Decimal("0.089"),
        "flight_short": Decimal("0.255"),
        "flight_long": Decimal("0.195"),
        
        # Materiały (per kg)
        "paper": Decimal("0.919"),
        "plastic": Decimal("2.53"),
        "steel": Decimal("1.46"),
        "aluminium": Decimal("8.14"),
        "concrete": Decimal("0.103"),
    }
    
    @classmethod
    def calculate_scope1(
        cls,
        natural_gas_kwh: Decimal = Decimal("0"),
        heating_oil_kwh: Decimal = Decimal("0"),
        company_vehicles_km: Dict[str, Decimal] = None
    ) -> GHGEmission:
        """Oblicz emisje Scope 1 (bezpośrednie)"""
        total = Decimal("0")
        
        # Gaz
        total += natural_gas_kwh * cls.EMISSION_FACTORS["natural_gas"]
        
        # Olej
        total += heating_oil_kwh * cls.EMISSION_FACTORS["heating_oil"]
        
        # Pojazdy
        if company_vehicles_km:
            for fuel_type, km in company_vehicles_km.items():
                factor = cls.EMISSION_FACTORS.get(f"car_{fuel_type}", Decimal("0.17"))
                total += km * factor
        
        return GHGEmission(
            scope=EmissionScope.SCOPE_1,
            amount_tonnes_co2e=(total / 1000).quantize(Decimal("0.01")),
            year=date.today().year,
            source="ANALYTICA Carbon Calculator",
            methodology="GHG Protocol"
        )
    
    @classmethod
    def calculate_scope2(
        cls,
        electricity_kwh: Decimal,
        country: str = "pl",
        renewable_percentage: Decimal = Decimal("0")
    ) -> GHGEmission:
        """Oblicz emisje Scope 2 (energia)"""
        factor_key = f"electricity_{country.lower()}"
        factor = cls.EMISSION_FACTORS.get(factor_key, cls.EMISSION_FACTORS["electricity_eu_avg"])
        
        # Uwzględnij energię odnawialną
        non_renewable = electricity_kwh * (1 - renewable_percentage / 100)
        total = non_renewable * factor
        
        return GHGEmission(
            scope=EmissionScope.SCOPE_2,
            amount_tonnes_co2e=(total / 1000).quantize(Decimal("0.01")),
            year=date.today().year,
            source="ANALYTICA Carbon Calculator",
            methodology="GHG Protocol - Location-based"
        )
    
    @classmethod
    def calculate_scope3_travel(
        cls,
        flights_short_km: Decimal = Decimal("0"),
        flights_long_km: Decimal = Decimal("0"),
        train_km: Decimal = Decimal("0"),
        bus_km: Decimal = Decimal("0")
    ) -> GHGEmission:
        """Oblicz emisje Scope 3 z podróży służbowych"""
        total = Decimal("0")
        
        total += flights_short_km * cls.EMISSION_FACTORS["flight_short"]
        total += flights_long_km * cls.EMISSION_FACTORS["flight_long"]
        total += train_km * cls.EMISSION_FACTORS["train"]
        total += bus_km * cls.EMISSION_FACTORS["bus"]
        
        return GHGEmission(
            scope=EmissionScope.SCOPE_3,
            amount_tonnes_co2e=(total / 1000).quantize(Decimal("0.01")),
            year=date.today().year,
            source="ANALYTICA Carbon Calculator - Business Travel",
            methodology="GHG Protocol"
        )


# ============================================================
# REPORT GENERATOR
# ============================================================

class ESGReportGenerator:
    """Generator raportów ESG w różnych formatach"""
    
    @staticmethod
    def to_json(report: ESGReport) -> str:
        """Eksport do JSON"""
        def serialize(obj):
            if isinstance(obj, (date, datetime)):
                return obj.isoformat()
            if isinstance(obj, Decimal):
                return float(obj)
            if isinstance(obj, Enum):
                return obj.value
            if hasattr(obj, '__dict__'):
                return {k: serialize(v) for k, v in obj.__dict__.items()}
            if isinstance(obj, list):
                return [serialize(i) for i in obj]
            return obj
        
        return json.dumps(serialize(report), indent=2, ensure_ascii=False)
    
    @staticmethod
    def generate_summary(report: ESGReport) -> Dict:
        """Generuj podsumowanie raportu"""
        scores = report.get_esg_score()
        
        summary = {
            "company": report.company_name,
            "year": report.reporting_year,
            "entity_size": report.entity_size.value,
            "scores": {k: float(v) for k, v in scores.items()},
            "highlights": {
                "environmental": {},
                "social": {},
                "governance": {}
            }
        }
        
        # E highlights
        if report.environmental.emissions:
            latest_emissions = max(report.environmental.emissions, key=lambda x: x.year)
            summary["highlights"]["environmental"]["total_emissions_tco2e"] = float(latest_emissions.amount_tonnes_co2e)
        
        if report.environmental.energy:
            latest_energy = max(report.environmental.energy, key=lambda x: x.year)
            summary["highlights"]["environmental"]["renewable_energy_pct"] = float(latest_energy.renewable_percentage)
        
        summary["highlights"]["environmental"]["net_zero_target"] = report.environmental.net_zero_target_year
        summary["highlights"]["environmental"]["sbti"] = report.environmental.science_based_targets
        
        # S highlights
        if report.social.workforce:
            latest_wf = max(report.social.workforce, key=lambda x: x.year)
            summary["highlights"]["social"]["total_employees"] = latest_wf.total_employees
            summary["highlights"]["social"]["female_management_pct"] = float(latest_wf.female_management_percentage)
            if latest_wf.gender_pay_gap:
                summary["highlights"]["social"]["gender_pay_gap"] = float(latest_wf.gender_pay_gap)
        
        # G highlights
        if report.governance.board:
            latest_board = max(report.governance.board, key=lambda x: x.year)
            summary["highlights"]["governance"]["board_size"] = latest_board.total_members
            summary["highlights"]["governance"]["independent_pct"] = float(
                Decimal(latest_board.independent_members) / Decimal(latest_board.total_members) * 100
            )
            summary["highlights"]["governance"]["sustainability_committee"] = latest_board.sustainability_committee
        
        return summary


__all__ = [
    'ESGCategory',
    'ESRSStandard',
    'EmissionScope',
    'CSRDEntitySize',
    'GHGEmission',
    'EnergyConsumption',
    'WaterConsumption',
    'WasteGeneration',
    'EnvironmentalData',
    'WorkforceMetrics',
    'HealthSafetyMetrics',
    'SocialData',
    'BoardComposition',
    'EthicsCompliance',
    'GovernanceData',
    'ESGReport',
    'CSRDComplianceChecker',
    'CarbonCalculator',
    'ESGReportGenerator'
]
