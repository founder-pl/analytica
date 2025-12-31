"""
ANALYTICA Compliance - ViDA & EU VAT Changes
=============================================

VAT in the Digital Age (ViDA) - reforma VAT w UE

Główne zmiany:
1. Digital Reporting Requirements (DRR) - e-fakturowanie i raportowanie
2. Single VAT Registration (SVR) - jedna rejestracja VAT w UE
3. Platform Economy - odpowiedzialność platform

Harmonogram:
- 2025: Początek wdrożenia
- 2028: E-fakturowanie wewnątrzunijne
- 2030: Pełne wdrożenie

Powiązane regulacje:
- DAC7/DAC8 - wymiana informacji podatkowych
- OSS/IOSS - procedury uproszczone
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

class VATScheme(Enum):
    """Schematy VAT"""
    STANDARD = "standard"
    OSS = "oss"           # One-Stop Shop
    IOSS = "ioss"         # Import One-Stop Shop
    MOSS = "moss"         # Mini One-Stop Shop (zastąpiony przez OSS)
    REVERSE_CHARGE = "reverse_charge"
    MARGIN = "margin"


class TransactionType(Enum):
    """Typy transakcji"""
    B2B_DOMESTIC = "b2b_domestic"
    B2B_INTRA_EU = "b2b_intra_eu"
    B2B_EXPORT = "b2b_export"
    B2C_DOMESTIC = "b2c_domestic"
    B2C_INTRA_EU = "b2c_intra_eu"
    B2C_DISTANCE_SALES = "b2c_distance_sales"
    B2C_IMPORT = "b2c_import"
    PLATFORM_FACILITATOR = "platform_facilitator"


class EUCountry(Enum):
    """Kraje UE"""
    AT = "Austria"
    BE = "Belgium"
    BG = "Bulgaria"
    HR = "Croatia"
    CY = "Cyprus"
    CZ = "Czechia"
    DK = "Denmark"
    EE = "Estonia"
    FI = "Finland"
    FR = "France"
    DE = "Germany"
    GR = "Greece"
    HU = "Hungary"
    IE = "Ireland"
    IT = "Italy"
    LV = "Latvia"
    LT = "Lithuania"
    LU = "Luxembourg"
    MT = "Malta"
    NL = "Netherlands"
    PL = "Poland"
    PT = "Portugal"
    RO = "Romania"
    SK = "Slovakia"
    SI = "Slovenia"
    ES = "Spain"
    SE = "Sweden"


# Stawki VAT w UE (standardowe, 2024)
EU_VAT_RATES = {
    EUCountry.AT: Decimal("20"),
    EUCountry.BE: Decimal("21"),
    EUCountry.BG: Decimal("20"),
    EUCountry.HR: Decimal("25"),
    EUCountry.CY: Decimal("19"),
    EUCountry.CZ: Decimal("21"),
    EUCountry.DK: Decimal("25"),
    EUCountry.EE: Decimal("22"),
    EUCountry.FI: Decimal("24"),
    EUCountry.FR: Decimal("20"),
    EUCountry.DE: Decimal("19"),
    EUCountry.GR: Decimal("24"),
    EUCountry.HU: Decimal("27"),
    EUCountry.IE: Decimal("23"),
    EUCountry.IT: Decimal("22"),
    EUCountry.LV: Decimal("21"),
    EUCountry.LT: Decimal("21"),
    EUCountry.LU: Decimal("17"),
    EUCountry.MT: Decimal("18"),
    EUCountry.NL: Decimal("21"),
    EUCountry.PL: Decimal("23"),
    EUCountry.PT: Decimal("23"),
    EUCountry.RO: Decimal("19"),
    EUCountry.SK: Decimal("20"),
    EUCountry.SI: Decimal("22"),
    EUCountry.ES: Decimal("21"),
    EUCountry.SE: Decimal("25"),
}


# ============================================================
# DATA MODELS
# ============================================================

@dataclass
class VATRegistration:
    """Rejestracja VAT"""
    country: EUCountry
    vat_number: str
    valid_from: date
    valid_to: Optional[date] = None
    scheme: VATScheme = VATScheme.STANDARD
    oss_registration: bool = False
    ioss_registration: bool = False
    
    def is_valid(self, check_date: date = None) -> bool:
        """Sprawdź czy rejestracja jest ważna"""
        check_date = check_date or date.today()
        
        if check_date < self.valid_from:
            return False
        
        if self.valid_to and check_date > self.valid_to:
            return False
        
        return True


@dataclass
class VATTransaction:
    """Transakcja VAT"""
    # Identyfikacja
    transaction_id: str
    transaction_date: date
    invoice_number: str
    
    # Strony
    seller_country: EUCountry
    seller_vat_number: str
    buyer_country: str  # Może być spoza UE
    buyer_vat_number: Optional[str] = None
    
    # Typ
    transaction_type: TransactionType = TransactionType.B2B_DOMESTIC
    is_b2c: bool = False
    
    # Kwoty
    net_amount: Decimal = Decimal("0")
    vat_rate: Decimal = Decimal("0")
    vat_amount: Decimal = Decimal("0")
    gross_amount: Decimal = Decimal("0")
    currency: str = "EUR"
    
    # Towary/Usługi
    goods_or_services: str = "services"  # goods, services, mixed
    
    # OSS/IOSS
    oss_applicable: bool = False
    ioss_applicable: bool = False
    
    # Platform
    platform_facilitator: bool = False
    platform_id: Optional[str] = None


@dataclass
class OSSDeclaration:
    """Deklaracja OSS"""
    # Okres
    year: int
    quarter: int
    
    # Podatnik
    trader_name: str
    trader_vat_number: str
    registration_country: EUCountry
    
    # Transakcje według kraju
    transactions_by_country: Dict[str, Dict] = field(default_factory=dict)
    # Format: {"PL": {"net": 1000, "vat": 230, "rate": 23}, ...}
    
    # Sumy
    total_net: Decimal = Decimal("0")
    total_vat: Decimal = Decimal("0")
    
    # Status
    submitted: bool = False
    submission_date: Optional[date] = None
    payment_date: Optional[date] = None
    payment_reference: Optional[str] = None
    
    def calculate_totals(self):
        """Przelicz sumy"""
        self.total_net = sum(
            Decimal(str(data.get("net", 0))) 
            for data in self.transactions_by_country.values()
        )
        self.total_vat = sum(
            Decimal(str(data.get("vat", 0))) 
            for data in self.transactions_by_country.values()
        )


@dataclass
class DAC7Report:
    """Raport DAC7 dla platform cyfrowych"""
    # Platforma
    platform_name: str
    platform_id: str  # Identyfikator w UE
    reporting_year: int
    
    # Sprzedawcy do zgłoszenia
    reportable_sellers: List[Dict] = field(default_factory=list)
    # Każdy sprzedawca: {name, tax_id, address, transactions_count, total_amount, ...}
    
    # Podsumowanie
    total_sellers: int = 0
    total_transactions: int = 0
    total_amount_eur: Decimal = Decimal("0")
    
    # Status
    submitted: bool = False
    submission_date: Optional[date] = None
    submission_country: Optional[EUCountry] = None


# ============================================================
# VAT CALCULATOR
# ============================================================

class EUVATCalculator:
    """Kalkulator VAT UE"""
    
    # Próg dla sprzedaży wysyłkowej (od lipca 2021)
    DISTANCE_SELLING_THRESHOLD_EUR = Decimal("10000")
    
    # Próg IOSS
    IOSS_THRESHOLD_EUR = Decimal("150")
    
    @classmethod
    def get_vat_rate(cls, country: EUCountry) -> Decimal:
        """Pobierz stawkę VAT dla kraju"""
        return EU_VAT_RATES.get(country, Decimal("20"))
    
    @classmethod
    def calculate_vat(
        cls,
        net_amount: Decimal,
        seller_country: EUCountry,
        buyer_country: str,
        is_b2c: bool = False,
        buyer_vat_number: Optional[str] = None,
        goods_or_services: str = "services"
    ) -> Dict:
        """
        Oblicz VAT dla transakcji UE
        
        Zwraca: {rate, vat_amount, gross_amount, scheme, country_of_taxation}
        """
        # Konwersja kraju kupującego
        try:
            buyer_eu_country = EUCountry[buyer_country.upper()]
            buyer_in_eu = True
        except (KeyError, AttributeError):
            buyer_eu_country = None
            buyer_in_eu = False
        
        # Określ miejsce opodatkowania i stawkę
        if not buyer_in_eu:
            # Eksport poza UE - 0% VAT
            return {
                "net_amount": float(net_amount),
                "vat_rate": 0,
                "vat_amount": 0,
                "gross_amount": float(net_amount),
                "scheme": "export",
                "country_of_taxation": None,
                "reverse_charge": False
            }
        
        if is_b2c:
            # B2C - miejsce opodatkowania zależy od progu
            # Uproszczenie: zakładamy przekroczenie progu
            vat_rate = cls.get_vat_rate(buyer_eu_country)
            country_of_taxation = buyer_eu_country
            scheme = VATScheme.OSS if seller_country != buyer_eu_country else VATScheme.STANDARD
        else:
            # B2B
            if buyer_vat_number and seller_country != buyer_eu_country:
                # WDT - reverse charge
                return {
                    "net_amount": float(net_amount),
                    "vat_rate": 0,
                    "vat_amount": 0,
                    "gross_amount": float(net_amount),
                    "scheme": "reverse_charge",
                    "country_of_taxation": buyer_eu_country.name,
                    "reverse_charge": True
                }
            else:
                # Lokalna sprzedaż lub brak VAT nabywcy
                vat_rate = cls.get_vat_rate(seller_country)
                country_of_taxation = seller_country
                scheme = VATScheme.STANDARD
        
        vat_amount = net_amount * vat_rate / 100
        gross_amount = net_amount + vat_amount
        
        return {
            "net_amount": float(net_amount),
            "vat_rate": float(vat_rate),
            "vat_amount": float(vat_amount.quantize(Decimal("0.01"))),
            "gross_amount": float(gross_amount.quantize(Decimal("0.01"))),
            "scheme": scheme.value if isinstance(scheme, VATScheme) else scheme,
            "country_of_taxation": country_of_taxation.name if country_of_taxation else None,
            "reverse_charge": False
        }
    
    @classmethod
    def check_oss_requirement(
        cls,
        seller_country: EUCountry,
        annual_b2c_sales_other_eu: Decimal
    ) -> Dict:
        """Sprawdź czy wymagana rejestracja OSS"""
        threshold_exceeded = annual_b2c_sales_other_eu > cls.DISTANCE_SELLING_THRESHOLD_EUR
        
        return {
            "threshold_eur": float(cls.DISTANCE_SELLING_THRESHOLD_EUR),
            "annual_sales_eur": float(annual_b2c_sales_other_eu),
            "threshold_exceeded": threshold_exceeded,
            "oss_recommended": threshold_exceeded,
            "alternative": "Register for VAT in each destination country" if threshold_exceeded else None,
            "benefits": [
                "Single VAT registration for all EU B2C sales",
                "One quarterly declaration",
                "One payment to home country tax authority"
            ] if threshold_exceeded else []
        }
    
    @classmethod
    def check_ioss_eligibility(
        cls,
        goods_value_eur: Decimal,
        origin_country: str
    ) -> Dict:
        """Sprawdź kwalifikację do IOSS"""
        # IOSS dla importów do 150 EUR z krajów spoza UE
        try:
            EUCountry[origin_country.upper()]
            from_eu = True
        except (KeyError, AttributeError):
            from_eu = False
        
        eligible = not from_eu and goods_value_eur <= cls.IOSS_THRESHOLD_EUR
        
        return {
            "eligible": eligible,
            "goods_value_eur": float(goods_value_eur),
            "threshold_eur": float(cls.IOSS_THRESHOLD_EUR),
            "origin_country": origin_country,
            "from_eu": from_eu,
            "reason": "Goods from non-EU country below €150 threshold" if eligible else
                     "From EU country" if from_eu else
                     "Exceeds €150 threshold"
        }


# ============================================================
# VIDA COMPLIANCE CHECKER
# ============================================================

class ViDAComplianceChecker:
    """Sprawdzanie zgodności z ViDA"""
    
    # Harmonogram ViDA
    VIDA_TIMELINE = {
        "digital_reporting": date(2028, 1, 1),
        "single_vat_registration": date(2025, 1, 1),
        "platform_liability": date(2025, 1, 1),
        "full_implementation": date(2030, 1, 1)
    }
    
    @classmethod
    def check_e_invoicing_readiness(
        cls,
        has_einvoicing_system: bool = False,
        ksef_ready: bool = False,  # Polski KSeF
        peppol_ready: bool = False,
        structured_invoice_format: Optional[str] = None  # UBL, CII
    ) -> Dict:
        """Sprawdź gotowość do e-fakturowania"""
        mandatory_date = cls.VIDA_TIMELINE["digital_reporting"]
        today = date.today()
        
        readiness_score = 0
        if has_einvoicing_system:
            readiness_score += 30
        if ksef_ready:
            readiness_score += 30  # Polski wymóg od 2026
        if peppol_ready:
            readiness_score += 20
        if structured_invoice_format in ["UBL", "CII"]:
            readiness_score += 20
        
        return {
            "mandatory_date": mandatory_date.isoformat(),
            "days_to_mandatory": (mandatory_date - today).days,
            "readiness_score": readiness_score,
            "has_einvoicing_system": has_einvoicing_system,
            "ksef_ready": ksef_ready,
            "peppol_ready": peppol_ready,
            "structured_format": structured_invoice_format,
            "recommendations": cls._get_einvoicing_recommendations(
                has_einvoicing_system, ksef_ready, peppol_ready
            )
        }
    
    @classmethod
    def check_vat_registration_optimization(
        cls,
        current_registrations: List[VATRegistration],
        transaction_countries: List[str]
    ) -> Dict:
        """Sprawdź optymalizację rejestracji VAT"""
        # SVR pozwoli na jedną rejestrację
        svr_date = cls.VIDA_TIMELINE["single_vat_registration"]
        
        current_count = len(current_registrations)
        oss_active = any(r.oss_registration for r in current_registrations)
        
        # Kraje z transakcjami bez rejestracji
        registered_countries = {r.country.name for r in current_registrations}
        unregistered = [c for c in transaction_countries if c not in registered_countries]
        
        return {
            "current_registrations": current_count,
            "oss_active": oss_active,
            "svr_available_from": svr_date.isoformat(),
            "transaction_countries": transaction_countries,
            "unregistered_countries": unregistered,
            "optimization_potential": current_count > 1,
            "recommendations": [
                "Consider OSS registration to simplify B2C compliance" if not oss_active else None,
                f"SVR will allow single registration from {svr_date}" if current_count > 1 else None,
                f"Missing registration in: {', '.join(unregistered)}" if unregistered else None
            ]
        }
    
    @classmethod
    def check_platform_obligations(
        cls,
        is_platform: bool = False,
        facilitates_sales: bool = False,
        sellers_count: int = 0,
        annual_gmv_eur: Decimal = Decimal("0")
    ) -> Dict:
        """Sprawdź obowiązki platform (ViDA + DAC7)"""
        platform_date = cls.VIDA_TIMELINE["platform_liability"]
        
        # DAC7 thresholds
        dac7_applicable = (
            sellers_count >= 30 or
            annual_gmv_eur >= Decimal("2000000")
        )
        
        return {
            "is_platform": is_platform,
            "facilitates_sales": facilitates_sales,
            "sellers_count": sellers_count,
            "annual_gmv_eur": float(annual_gmv_eur),
            "vida_obligations": {
                "deemed_supplier": is_platform and facilitates_sales,
                "vat_collection_required": is_platform and facilitates_sales,
                "effective_date": platform_date.isoformat()
            },
            "dac7_obligations": {
                "reporting_required": dac7_applicable,
                "deadline": "January 31 of following year",
                "threshold_sellers": 30,
                "threshold_gmv_eur": 2000000
            },
            "recommendations": cls._get_platform_recommendations(
                is_platform, dac7_applicable
            )
        }
    
    @staticmethod
    def _get_einvoicing_recommendations(
        has_system: bool,
        ksef: bool,
        peppol: bool
    ) -> List[str]:
        """Rekomendacje dla e-fakturowania"""
        recommendations = []
        
        if not has_system:
            recommendations.append("Wdróż system e-fakturowania")
        
        if not ksef:
            recommendations.append("Przygotuj integrację z KSeF (obowiązkowy w PL od 2026)")
        
        if not peppol:
            recommendations.append("Rozważ integrację z PEPPOL dla transakcji B2G i B2B w UE")
        
        recommendations.append("Przygotuj się na obowiązkowe e-fakturowanie wewnątrzunijowe od 2028")
        
        return [r for r in recommendations if r]
    
    @staticmethod
    def _get_platform_recommendations(
        is_platform: bool,
        dac7: bool
    ) -> List[str]:
        """Rekomendacje dla platform"""
        recommendations = []
        
        if is_platform:
            recommendations.append("Przygotuj systemy do poboru VAT jako deemed supplier")
            recommendations.append("Wdróż weryfikację sprzedawców (KYC)")
        
        if dac7:
            recommendations.append("Wdróż raportowanie DAC7 - zbieraj dane o sprzedawcach")
            recommendations.append("Termin raportowania: 31 stycznia następnego roku")
        
        return recommendations


# ============================================================
# DAC7/DAC8 REPORTER
# ============================================================

class DAC7Reporter:
    """Generator raportów DAC7"""
    
    @staticmethod
    def create_seller_record(
        seller_name: str,
        seller_type: str,  # individual, entity
        tax_id: str,
        country: str,
        address: Dict,
        transactions_count: int,
        total_consideration_eur: Decimal,
        fees_eur: Decimal
    ) -> Dict:
        """Utwórz rekord sprzedawcy dla DAC7"""
        return {
            "seller_name": seller_name,
            "seller_type": seller_type,
            "tax_identification_number": tax_id,
            "residence_country": country,
            "address": {
                "street": address.get("street", ""),
                "city": address.get("city", ""),
                "postal_code": address.get("postal_code", ""),
                "country": address.get("country", country)
            },
            "activity_data": {
                "transactions_count": transactions_count,
                "total_consideration_eur": float(total_consideration_eur),
                "fees_deducted_eur": float(fees_eur),
                "net_amount_eur": float(total_consideration_eur - fees_eur)
            }
        }
    
    @staticmethod
    def generate_dac7_xml(report: DAC7Report) -> str:
        """Generuj XML raportu DAC7"""
        import xml.etree.ElementTree as ET
        
        # Namespace DAC7
        ns = "urn:oecd:ties:dpi:v1"
        
        root = ET.Element("DPI_OECD", xmlns=ns)
        root.set("version", "1.0")
        
        # Message header
        header = ET.SubElement(root, "MessageHeader")
        ET.SubElement(header, "PlatformOperatorId").text = report.platform_id
        ET.SubElement(header, "ReportingYear").text = str(report.reporting_year)
        ET.SubElement(header, "Timestamp").text = datetime.now().isoformat()
        
        # Platform operator info
        platform = ET.SubElement(root, "PlatformOperator")
        ET.SubElement(platform, "Name").text = report.platform_name
        ET.SubElement(platform, "PlatformId").text = report.platform_id
        
        # Reportable sellers
        sellers = ET.SubElement(root, "ReportableSellers")
        
        for seller_data in report.reportable_sellers:
            seller = ET.SubElement(sellers, "ReportableSeller")
            
            # Identity
            identity = ET.SubElement(seller, "Identity")
            ET.SubElement(identity, "Name").text = seller_data["seller_name"]
            ET.SubElement(identity, "TIN").text = seller_data["tax_identification_number"]
            ET.SubElement(identity, "ResCountryCode").text = seller_data["residence_country"]
            
            # Address
            addr = ET.SubElement(seller, "Address")
            addr_data = seller_data.get("address", {})
            ET.SubElement(addr, "Street").text = addr_data.get("street", "")
            ET.SubElement(addr, "City").text = addr_data.get("city", "")
            ET.SubElement(addr, "PostCode").text = addr_data.get("postal_code", "")
            ET.SubElement(addr, "CountryCode").text = addr_data.get("country", "")
            
            # Activity
            activity = ET.SubElement(seller, "ActivityData")
            act_data = seller_data.get("activity_data", {})
            ET.SubElement(activity, "NumberOfActivities").text = str(act_data.get("transactions_count", 0))
            ET.SubElement(activity, "Consideration").text = str(act_data.get("total_consideration_eur", 0))
            ET.SubElement(activity, "FeesAmount").text = str(act_data.get("fees_deducted_eur", 0))
        
        # Summary
        summary = ET.SubElement(root, "Summary")
        ET.SubElement(summary, "TotalSellers").text = str(report.total_sellers)
        ET.SubElement(summary, "TotalTransactions").text = str(report.total_transactions)
        ET.SubElement(summary, "TotalAmount").text = str(report.total_amount_eur)
        
        return ET.tostring(root, encoding='unicode', xml_declaration=True)


__all__ = [
    'VATScheme',
    'TransactionType',
    'EUCountry',
    'EU_VAT_RATES',
    'VATRegistration',
    'VATTransaction',
    'OSSDeclaration',
    'DAC7Report',
    'EUVATCalculator',
    'ViDAComplianceChecker',
    'DAC7Reporter'
]
