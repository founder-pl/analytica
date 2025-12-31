"""
ANALYTICA Compliance - CBAM
============================

Carbon Border Adjustment Mechanism (CBAM)
Mechanizm dostosowywania cen na granicach z uwzględnieniem emisji CO2

Obowiązuje od 2026 (pełne wdrożenie), okres przejściowy 2023-2025

Produkty objęte:
- Cement
- Żelazo i stal
- Aluminium
- Nawozy
- Energia elektryczna
- Wodór

Dokumentacja: https://taxation-customs.ec.europa.eu/carbon-border-adjustment-mechanism_en
"""

from typing import Any, Dict, List, Optional, Union
from dataclasses import dataclass, field
from datetime import datetime, date
from decimal import Decimal
from enum import Enum
import json


# ============================================================
# ENUMS & CONSTANTS
# ============================================================

class CBAMProduct(Enum):
    """Produkty objęte CBAM"""
    CEMENT = "cement"
    IRON_STEEL = "iron_steel"
    ALUMINIUM = "aluminium"
    FERTILIZERS = "fertilizers"
    ELECTRICITY = "electricity"
    HYDROGEN = "hydrogen"


class CBAMPhase(Enum):
    """Fazy wdrożenia CBAM"""
    TRANSITIONAL = "transitional"  # 2023-2025: tylko raportowanie
    FULL = "full"                  # od 2026: certyfikaty CBAM


# CN codes objęte CBAM
CBAM_CN_CODES = {
    CBAMProduct.CEMENT: [
        "2523",  # Cement portlandzki
    ],
    CBAMProduct.IRON_STEEL: [
        "7201", "7202", "7203", "7204", "7205", "7206", "7207", "7208",
        "7209", "7210", "7211", "7212", "7213", "7214", "7215", "7216",
        "7217", "7218", "7219", "7220", "7221", "7222", "7223", "7224",
        "7225", "7226", "7227", "7228", "7229", "7301", "7302", "7303",
        "7304", "7305", "7306"
    ],
    CBAMProduct.ALUMINIUM: [
        "7601", "7602", "7603", "7604", "7605", "7606", "7607", "7608",
        "7609"
    ],
    CBAMProduct.FERTILIZERS: [
        "2808", "2814", "2834", "3102", "3105"
    ],
    CBAMProduct.ELECTRICITY: [
        "2716"
    ],
    CBAMProduct.HYDROGEN: [
        "2804"
    ]
}

# Domyślne współczynniki emisji (tCO2/t produktu)
DEFAULT_EMISSION_FACTORS = {
    CBAMProduct.CEMENT: Decimal("0.766"),
    CBAMProduct.IRON_STEEL: Decimal("1.85"),
    CBAMProduct.ALUMINIUM: Decimal("8.4"),
    CBAMProduct.FERTILIZERS: Decimal("2.54"),
    CBAMProduct.ELECTRICITY: Decimal("0.429"),  # tCO2/MWh
    CBAMProduct.HYDROGEN: Decimal("9.0"),
}


# ============================================================
# DATA MODELS
# ============================================================

@dataclass
class CBAMImport:
    """Import objęty CBAM"""
    # Identyfikacja
    import_id: str
    import_date: date
    
    # Produkt
    cn_code: str
    product_category: CBAMProduct
    description: str
    
    # Ilości
    quantity_tonnes: Decimal
    
    # Pochodzenie
    country_of_origin: str
    
    # Optional fields (with defaults) must come after required fields
    quantity_mwh: Optional[Decimal] = None  # dla energii elektrycznej
    installation_id: Optional[str] = None
    installation_name: Optional[str] = None
    
    # Emisje
    direct_emissions_tco2: Optional[Decimal] = None
    indirect_emissions_tco2: Optional[Decimal] = None
    total_emissions_tco2: Optional[Decimal] = None
    
    # Cena węgla w kraju pochodzenia
    carbon_price_paid_eur: Decimal = Decimal("0")
    carbon_price_currency: str = "EUR"
    
    # Wartość celna
    customs_value_eur: Decimal = Decimal("0")
    
    # Weryfikacja
    verified: bool = False
    verification_body: Optional[str] = None
    
    def calculate_emissions(self, use_default: bool = True) -> Decimal:
        """Oblicz emisje jeśli nie podano"""
        if self.total_emissions_tco2:
            return self.total_emissions_tco2
        
        if self.direct_emissions_tco2:
            indirect = self.indirect_emissions_tco2 or Decimal("0")
            return self.direct_emissions_tco2 + indirect
        
        if use_default:
            factor = DEFAULT_EMISSION_FACTORS.get(self.product_category, Decimal("1"))
            if self.product_category == CBAMProduct.ELECTRICITY:
                return (self.quantity_mwh or Decimal("0")) * factor
            return self.quantity_tonnes * factor
        
        return Decimal("0")


@dataclass
class CBAMQuarterlyReport:
    """Kwartalny raport CBAM (okres przejściowy)"""
    # Okres
    year: int
    quarter: int  # 1-4
    
    # Importer
    importer_name: str
    importer_eori: str
    importer_country: str = "PL"
    
    # Importy
    imports: List[CBAMImport] = field(default_factory=list)
    
    # Podsumowanie
    total_imports_tonnes: Decimal = Decimal("0")
    total_emissions_tco2: Decimal = Decimal("0")
    total_customs_value_eur: Decimal = Decimal("0")
    
    # Status
    submission_date: Optional[date] = None
    submission_reference: Optional[str] = None
    
    def calculate_totals(self):
        """Przelicz sumy"""
        self.total_imports_tonnes = sum(i.quantity_tonnes for i in self.imports)
        self.total_emissions_tco2 = sum(i.calculate_emissions() for i in self.imports)
        self.total_customs_value_eur = sum(i.customs_value_eur for i in self.imports)
    
    def get_summary_by_product(self) -> Dict[str, Dict]:
        """Podsumowanie według kategorii produktów"""
        summary = {}
        
        for imp in self.imports:
            cat = imp.product_category.value
            if cat not in summary:
                summary[cat] = {
                    "quantity_tonnes": Decimal("0"),
                    "emissions_tco2": Decimal("0"),
                    "value_eur": Decimal("0"),
                    "count": 0
                }
            
            summary[cat]["quantity_tonnes"] += imp.quantity_tonnes
            summary[cat]["emissions_tco2"] += imp.calculate_emissions()
            summary[cat]["value_eur"] += imp.customs_value_eur
            summary[cat]["count"] += 1
        
        return summary
    
    def get_summary_by_country(self) -> Dict[str, Dict]:
        """Podsumowanie według kraju pochodzenia"""
        summary = {}
        
        for imp in self.imports:
            country = imp.country_of_origin
            if country not in summary:
                summary[country] = {
                    "quantity_tonnes": Decimal("0"),
                    "emissions_tco2": Decimal("0"),
                    "value_eur": Decimal("0"),
                    "count": 0
                }
            
            summary[country]["quantity_tonnes"] += imp.quantity_tonnes
            summary[country]["emissions_tco2"] += imp.calculate_emissions()
            summary[country]["value_eur"] += imp.customs_value_eur
            summary[country]["count"] += 1
        
        return summary


@dataclass
class CBAMCertificate:
    """Certyfikat CBAM (od 2026)"""
    certificate_id: str
    issue_date: date
    valid_until: date
    
    # Wartość
    emissions_tco2: Decimal
    price_per_tco2_eur: Decimal
    total_value_eur: Decimal
    
    # Status
    used: bool = False
    used_date: Optional[date] = None
    used_for_import_id: Optional[str] = None


@dataclass
class CBAMAnnualDeclaration:
    """Roczna deklaracja CBAM (od 2026)"""
    year: int
    
    # Importer
    importer_name: str
    importer_eori: str
    
    # Podsumowanie importów
    total_imports_tonnes: Decimal
    total_emissions_tco2: Decimal
    
    # Certyfikaty
    certificates_required: int
    certificates_surrendered: int
    certificates_value_eur: Decimal
    
    # Odliczenia (cena CO2 zapłacona w kraju pochodzenia)
    carbon_price_deductions_eur: Decimal = Decimal("0")
    
    # Darmowe przydziały EU ETS
    free_allocation_deduction_tco2: Decimal = Decimal("0")
    
    # Finalne zobowiązanie
    net_obligation_tco2: Decimal = Decimal("0")
    net_obligation_eur: Decimal = Decimal("0")
    
    # Status
    submitted: bool = False
    submission_date: Optional[date] = None


# ============================================================
# CBAM CALCULATOR
# ============================================================

class CBAMCalculator:
    """Kalkulator CBAM"""
    
    # Cena referencyjna EU ETS (aktualizowana)
    EU_ETS_PRICE_EUR = Decimal("80")  # ~80 EUR/tCO2 (2024)
    
    @classmethod
    def calculate_cbam_liability(
        cls,
        emissions_tco2: Decimal,
        carbon_price_paid_eur: Decimal = Decimal("0"),
        free_allocation_tco2: Decimal = Decimal("0"),
        eu_ets_price: Decimal = None
    ) -> Dict:
        """
        Oblicz zobowiązanie CBAM
        
        Args:
            emissions_tco2: Całkowite emisje związane z importem
            carbon_price_paid_eur: Cena CO2 zapłacona w kraju pochodzenia
            free_allocation_tco2: Darmowe przydziały EU ETS dla sektora
            eu_ets_price: Cena EU ETS (domyślnie aktualna)
        """
        ets_price = eu_ets_price or cls.EU_ETS_PRICE_EUR
        
        # Emisje netto po odliczeniu darmowych przydziałów
        net_emissions = max(emissions_tco2 - free_allocation_tco2, Decimal("0"))
        
        # Wartość brutto
        gross_liability_eur = net_emissions * ets_price
        
        # Odliczenie ceny CO2 zapłaconej w kraju pochodzenia
        net_liability_eur = max(gross_liability_eur - carbon_price_paid_eur, Decimal("0"))
        
        # Liczba wymaganych certyfikatów (1 certyfikat = 1 tCO2)
        certificates_required = int(net_emissions.quantize(Decimal("1")))
        
        return {
            "total_emissions_tco2": float(emissions_tco2),
            "free_allocation_tco2": float(free_allocation_tco2),
            "net_emissions_tco2": float(net_emissions),
            "eu_ets_price_eur": float(ets_price),
            "gross_liability_eur": float(gross_liability_eur),
            "carbon_price_deduction_eur": float(carbon_price_paid_eur),
            "net_liability_eur": float(net_liability_eur),
            "certificates_required": certificates_required,
            "effective_carbon_price_eur": float(
                net_liability_eur / net_emissions if net_emissions > 0 else 0
            )
        }
    
    @classmethod
    def calculate_import_emissions(
        cls,
        cn_code: str,
        quantity_tonnes: Decimal,
        country_of_origin: str,
        actual_emissions_tco2: Optional[Decimal] = None
    ) -> Dict:
        """Oblicz emisje dla importu"""
        # Znajdź kategorię produktu
        product_category = None
        for cat, codes in CBAM_CN_CODES.items():
            if any(cn_code.startswith(code) for code in codes):
                product_category = cat
                break
        
        if not product_category:
            return {
                "error": f"CN code {cn_code} not covered by CBAM",
                "covered": False
            }
        
        # Użyj rzeczywistych emisji lub domyślnych
        if actual_emissions_tco2:
            emissions = actual_emissions_tco2
            method = "actual"
        else:
            factor = DEFAULT_EMISSION_FACTORS[product_category]
            emissions = quantity_tonnes * factor
            method = "default"
        
        return {
            "covered": True,
            "cn_code": cn_code,
            "product_category": product_category.value,
            "quantity_tonnes": float(quantity_tonnes),
            "emissions_tco2": float(emissions),
            "calculation_method": method,
            "emission_factor": float(DEFAULT_EMISSION_FACTORS[product_category]),
            "country_of_origin": country_of_origin
        }
    
    @classmethod
    def is_cbam_product(cls, cn_code: str) -> bool:
        """Sprawdź czy produkt jest objęty CBAM"""
        for codes in CBAM_CN_CODES.values():
            if any(cn_code.startswith(code) for code in codes):
                return True
        return False
    
    @classmethod
    def get_product_category(cls, cn_code: str) -> Optional[CBAMProduct]:
        """Pobierz kategorię produktu CBAM"""
        for cat, codes in CBAM_CN_CODES.items():
            if any(cn_code.startswith(code) for code in codes):
                return cat
        return None


# ============================================================
# CBAM COMPLIANCE CHECKER
# ============================================================

class CBAMComplianceChecker:
    """Sprawdzanie zgodności z CBAM"""
    
    # Terminy
    TRANSITIONAL_START = date(2023, 10, 1)
    TRANSITIONAL_END = date(2025, 12, 31)
    FULL_START = date(2026, 1, 1)
    
    # Terminy raportowania kwartalnego
    QUARTERLY_DEADLINES = {
        1: (1, 31),   # Q4 poprzedniego roku -> 31 stycznia
        2: (4, 30),   # Q1 -> 30 kwietnia
        3: (7, 31),   # Q2 -> 31 lipca
        4: (10, 31),  # Q3 -> 31 października
    }
    
    @classmethod
    def get_current_phase(cls) -> CBAMPhase:
        """Pobierz aktualną fazę CBAM"""
        today = date.today()
        
        if today < cls.FULL_START:
            return CBAMPhase.TRANSITIONAL
        return CBAMPhase.FULL
    
    @classmethod
    def check_quarterly_report_compliance(
        cls,
        year: int,
        quarter: int,
        report_submitted: bool = False,
        submission_date: Optional[date] = None
    ) -> Dict:
        """Sprawdź zgodność raportu kwartalnego"""
        # Oblicz deadline
        if quarter == 4:
            deadline_year = year + 1
            deadline_month, deadline_day = cls.QUARTERLY_DEADLINES[1]
        else:
            deadline_year = year
            deadline_month, deadline_day = cls.QUARTERLY_DEADLINES[quarter + 1]
        
        deadline = date(deadline_year, deadline_month, deadline_day)
        today = date.today()
        
        # Status
        is_overdue = not report_submitted and today > deadline
        is_on_time = report_submitted and submission_date and submission_date <= deadline
        
        return {
            "year": year,
            "quarter": quarter,
            "deadline": deadline.isoformat(),
            "report_submitted": report_submitted,
            "submission_date": submission_date.isoformat() if submission_date else None,
            "is_overdue": is_overdue,
            "is_on_time": is_on_time,
            "days_to_deadline": (deadline - today).days if today <= deadline else 0,
            "days_overdue": (today - deadline).days if is_overdue else 0,
            "phase": cls.get_current_phase().value,
            "recommendations": cls._get_quarterly_recommendations(
                report_submitted, is_overdue, deadline
            )
        }
    
    @classmethod
    def check_annual_declaration_compliance(
        cls,
        year: int,
        declaration_submitted: bool = False,
        certificates_surrendered: int = 0,
        certificates_required: int = 0
    ) -> Dict:
        """Sprawdź zgodność rocznej deklaracji (od 2026)"""
        # Deadline: 31 maja następnego roku
        deadline = date(year + 1, 5, 31)
        today = date.today()
        
        # Sprawdź czy CBAM w pełni obowiązuje
        if year < 2026:
            return {
                "applicable": False,
                "message": "Annual CBAM declarations start from 2026"
            }
        
        certificate_compliant = certificates_surrendered >= certificates_required
        
        return {
            "year": year,
            "deadline": deadline.isoformat(),
            "declaration_submitted": declaration_submitted,
            "certificates_required": certificates_required,
            "certificates_surrendered": certificates_surrendered,
            "certificate_compliant": certificate_compliant,
            "certificate_shortfall": max(0, certificates_required - certificates_surrendered),
            "is_overdue": not declaration_submitted and today > deadline,
            "days_to_deadline": (deadline - today).days if today <= deadline else 0,
            "recommendations": cls._get_annual_recommendations(
                declaration_submitted, certificate_compliant, certificates_required - certificates_surrendered
            )
        }
    
    @staticmethod
    def _get_quarterly_recommendations(
        submitted: bool,
        overdue: bool,
        deadline: date
    ) -> List[str]:
        """Rekomendacje dla raportu kwartalnego"""
        recommendations = []
        
        if overdue:
            recommendations.append("PILNE: Raport kwartalny CBAM jest zaległy. Złóż natychmiast.")
            recommendations.append("Możliwe kary za opóźnienie w raportowaniu")
        elif not submitted:
            recommendations.append(f"Złóż raport kwartalny CBAM przed {deadline}")
            recommendations.append("Zbierz dane o emisjach od dostawców spoza UE")
        else:
            recommendations.append("Raport kwartalny złożony prawidłowo")
        
        return recommendations
    
    @staticmethod
    def _get_annual_recommendations(
        submitted: bool,
        certificate_compliant: bool,
        shortfall: int
    ) -> List[str]:
        """Rekomendacje dla deklaracji rocznej"""
        recommendations = []
        
        if not submitted:
            recommendations.append("Przygotuj roczną deklarację CBAM")
        
        if not certificate_compliant:
            recommendations.append(f"Kup {shortfall} dodatkowych certyfikatów CBAM")
            recommendations.append("Sprawdź możliwość odliczeń za cenę CO2 w kraju pochodzenia")
        else:
            recommendations.append("Zgodność z wymogami CBAM")
        
        return recommendations


# ============================================================
# REPORT GENERATOR
# ============================================================

class CBAMReportGenerator:
    """Generator raportów CBAM"""
    
    @staticmethod
    def generate_quarterly_xml(report: CBAMQuarterlyReport) -> str:
        """Generuj XML raportu kwartalnego (format CBAM)"""
        import xml.etree.ElementTree as ET
        
        root = ET.Element("CBAMReport")
        root.set("version", "1.0")
        
        # Header
        header = ET.SubElement(root, "Header")
        ET.SubElement(header, "Year").text = str(report.year)
        ET.SubElement(header, "Quarter").text = str(report.quarter)
        ET.SubElement(header, "ImporterName").text = report.importer_name
        ET.SubElement(header, "ImporterEORI").text = report.importer_eori
        ET.SubElement(header, "ImporterCountry").text = report.importer_country
        
        # Imports
        imports_elem = ET.SubElement(root, "Imports")
        
        for imp in report.imports:
            imp_elem = ET.SubElement(imports_elem, "Import")
            ET.SubElement(imp_elem, "ImportId").text = imp.import_id
            ET.SubElement(imp_elem, "Date").text = imp.import_date.isoformat()
            ET.SubElement(imp_elem, "CNCode").text = imp.cn_code
            ET.SubElement(imp_elem, "ProductCategory").text = imp.product_category.value
            ET.SubElement(imp_elem, "Description").text = imp.description
            ET.SubElement(imp_elem, "QuantityTonnes").text = str(imp.quantity_tonnes)
            ET.SubElement(imp_elem, "CountryOfOrigin").text = imp.country_of_origin
            
            if imp.installation_id:
                ET.SubElement(imp_elem, "InstallationId").text = imp.installation_id
            
            emissions = ET.SubElement(imp_elem, "Emissions")
            ET.SubElement(emissions, "DirectTCO2").text = str(imp.direct_emissions_tco2 or 0)
            ET.SubElement(emissions, "IndirectTCO2").text = str(imp.indirect_emissions_tco2 or 0)
            ET.SubElement(emissions, "TotalTCO2").text = str(imp.calculate_emissions())
            
            if imp.carbon_price_paid_eur > 0:
                carbon = ET.SubElement(imp_elem, "CarbonPricePaid")
                ET.SubElement(carbon, "Amount").text = str(imp.carbon_price_paid_eur)
                ET.SubElement(carbon, "Currency").text = imp.carbon_price_currency
        
        # Summary
        summary = ET.SubElement(root, "Summary")
        ET.SubElement(summary, "TotalImportsTonnes").text = str(report.total_imports_tonnes)
        ET.SubElement(summary, "TotalEmissionsTCO2").text = str(report.total_emissions_tco2)
        ET.SubElement(summary, "TotalCustomsValueEUR").text = str(report.total_customs_value_eur)
        
        return ET.tostring(root, encoding='unicode', xml_declaration=True)
    
    @staticmethod
    def generate_summary(report: CBAMQuarterlyReport) -> Dict:
        """Generuj podsumowanie raportu"""
        report.calculate_totals()
        
        return {
            "period": f"Q{report.quarter}/{report.year}",
            "importer": {
                "name": report.importer_name,
                "eori": report.importer_eori,
                "country": report.importer_country
            },
            "totals": {
                "imports_count": len(report.imports),
                "imports_tonnes": float(report.total_imports_tonnes),
                "emissions_tco2": float(report.total_emissions_tco2),
                "customs_value_eur": float(report.total_customs_value_eur)
            },
            "by_product": {
                k: {key: float(v) if isinstance(v, Decimal) else v for key, v in val.items()}
                for k, val in report.get_summary_by_product().items()
            },
            "by_country": {
                k: {key: float(v) if isinstance(v, Decimal) else v for key, v in val.items()}
                for k, val in report.get_summary_by_country().items()
            },
            "cbam_liability": CBAMCalculator.calculate_cbam_liability(
                report.total_emissions_tco2
            )
        }


__all__ = [
    'CBAMProduct',
    'CBAMPhase',
    'CBAM_CN_CODES',
    'DEFAULT_EMISSION_FACTORS',
    'CBAMImport',
    'CBAMQuarterlyReport',
    'CBAMCertificate',
    'CBAMAnnualDeclaration',
    'CBAMCalculator',
    'CBAMComplianceChecker',
    'CBAMReportGenerator'
]
