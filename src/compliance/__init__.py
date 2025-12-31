"""
ANALYTICA Compliance Module
============================

Moduły zgodności z regulacjami prawnymi 2025-2030:

POLSKA:
- KSeF - Krajowy System e-Faktur (obowiązkowy od 02.2026)
- E-Doręczenia - system doręczeń elektronicznych (od 01.2026)

UNIA EUROPEJSKA:
- CSRD/ESG - raportowanie zrównoważonego rozwoju (2025-2027)
- CBAM - mechanizm węglowy na granicach (przejściowy 2023-2025, pełny od 2026)
- ViDA - VAT in Digital Age (2025-2030)
- DAC7/DAC8 - wymiana informacji podatkowych platform

Planowane (do dodania):
- NIS2 - cyberbezpieczeństwo (2024-2025)
- DORA - odporność cyfrowa sektora finansowego (2025)
- AI Act - regulacje AI (2025-2026)
"""

# KSeF - Polski system e-faktur
from .ksef import (
    KSeFEnvironment,
    InvoiceType,
    PaymentMethod,
    VATRate,
    KSeFAddress,
    KSeFParty,
    KSeFInvoiceLine,
    KSeFInvoice,
    KSeFResponse,
    KSeFXMLGenerator,
    KSeFClient,
    create_simple_invoice,
)

# E-Doręczenia - Doręczenia elektroniczne
from .edoreczenia import (
    EDoreczeniaEnvironment,
    DocumentType,
    DeliveryStatus,
    RecipientType,
    EDoreczeniaAddress,
    EDoreczeniaDocument,
    EDoreczeniaMessage,
    EDoreczeniaDeliveryConfirmation,
    EDoreczeniaResponse,
    BAEClient,
    EDoreczeniaClient,
    EDoreczeniaComplianceChecker,
)

# ESG/CSRD - Raportowanie zrównoważonego rozwoju
from .esg_csrd import (
    ESGCategory,
    ESRSStandard,
    EmissionScope,
    CSRDEntitySize,
    GHGEmission,
    EnergyConsumption,
    WaterConsumption,
    WasteGeneration,
    EnvironmentalData,
    WorkforceMetrics,
    HealthSafetyMetrics,
    SocialData,
    BoardComposition,
    EthicsCompliance,
    GovernanceData,
    ESGReport,
    CSRDComplianceChecker,
    CarbonCalculator,
    ESGReportGenerator,
)

# CBAM - Carbon Border Adjustment Mechanism
from .cbam import (
    CBAMProduct,
    CBAMPhase,
    CBAM_CN_CODES,
    DEFAULT_EMISSION_FACTORS,
    CBAMImport,
    CBAMQuarterlyReport,
    CBAMCertificate,
    CBAMAnnualDeclaration,
    CBAMCalculator,
    CBAMComplianceChecker,
    CBAMReportGenerator,
)

# ViDA & VAT - Zmiany VAT w UE
from .vida_vat import (
    VATScheme,
    TransactionType,
    EUCountry,
    EU_VAT_RATES,
    VATRegistration,
    VATTransaction,
    OSSDeclaration,
    DAC7Report,
    EUVATCalculator,
    ViDAComplianceChecker,
    DAC7Reporter,
)


# ============================================================
# UNIFIED COMPLIANCE CHECKER
# ============================================================

class ComplianceChecker:
    """
    Zunifikowany sprawdzacz zgodności
    
    Agreguje wszystkie moduły compliance w jeden interfejs
    """
    
    def __init__(
        self,
        company_name: str,
        nip: str,
        country: str = "PL",
        employees: int = 0,
        revenue_eur: float = 0,
        is_listed: bool = False
    ):
        self.company_name = company_name
        self.nip = nip
        self.country = country
        self.employees = employees
        self.revenue_eur = revenue_eur
        self.is_listed = is_listed
    
    def check_all(self) -> dict:
        """Sprawdź wszystkie regulacje"""
        from datetime import date
        from decimal import Decimal
        
        results = {
            "company": self.company_name,
            "check_date": date.today().isoformat(),
            "regulations": {}
        }
        
        # KSeF
        results["regulations"]["ksef"] = {
            "name": "Krajowy System e-Faktur",
            "mandatory_from": "2026-02-01",
            "status": "PREPARE",
            "priority": "HIGH" if self.country == "PL" else "N/A"
        }
        
        # E-Doręczenia
        if self.country == "PL":
            ed_check = EDoreczeniaComplianceChecker.check_compliance(
                entity_type="KRS",  # Assumption
                has_ade=False
            )
            results["regulations"]["edoreczenia"] = {
                "name": "E-Doręczenia",
                **ed_check
            }
        
        # CSRD
        csrd_size = CSRDComplianceChecker.determine_entity_size(
            employees=self.employees,
            revenue_eur=Decimal(str(self.revenue_eur)),
            assets_eur=Decimal(str(self.revenue_eur * 0.5)),  # Estimate
            is_listed=self.is_listed
        )
        csrd_check = CSRDComplianceChecker.check_compliance(csrd_size)
        results["regulations"]["csrd"] = {
            "name": "CSRD / ESG Reporting",
            **csrd_check
        }
        
        # CBAM
        results["regulations"]["cbam"] = {
            "name": "Carbon Border Adjustment Mechanism",
            "phase": CBAMComplianceChecker.get_current_phase().value,
            "applicable": "Check imports",
            "quarterly_reporting": True
        }
        
        # ViDA
        vida_check = ViDAComplianceChecker.check_e_invoicing_readiness(
            has_einvoicing_system=False,
            ksef_ready=False
        )
        results["regulations"]["vida"] = {
            "name": "VAT in Digital Age",
            **vida_check
        }
        
        return results
    
    def get_timeline(self) -> list:
        """Pobierz harmonogram wdrożeń"""
        from datetime import date
        
        timeline = [
            {
                "date": "2025-01-01",
                "regulation": "CSRD",
                "description": "Raportowanie ESG dla dużych spółek giełdowych",
                "action": "Przygotuj pierwszy raport ESG za 2024"
            },
            {
                "date": "2026-01-01",
                "regulation": "E-Doręczenia",
                "description": "Obowiązkowe e-Doręczenia dla firm",
                "action": "Zarejestruj adres ADE w BAE"
            },
            {
                "date": "2026-01-01",
                "regulation": "CBAM",
                "description": "Pełne wdrożenie CBAM - certyfikaty",
                "action": "Przygotuj zakup certyfikatów CBAM"
            },
            {
                "date": "2026-02-01",
                "regulation": "KSeF",
                "description": "Obowiązkowy KSeF w Polsce",
                "action": "Wdróż integrację z KSeF"
            },
            {
                "date": "2026-01-01",
                "regulation": "CSRD",
                "description": "Raportowanie ESG dla dużych przedsiębiorstw",
                "action": "Raport za 2025 wg ESRS"
            },
            {
                "date": "2028-01-01",
                "regulation": "ViDA",
                "description": "E-fakturowanie wewnątrzunijne",
                "action": "Przygotuj systemy na e-fakturowanie UE"
            },
        ]
        
        today = date.today()
        
        # Dodaj status
        for item in timeline:
            item_date = date.fromisoformat(item["date"])
            if item_date <= today:
                item["status"] = "ACTIVE"
            elif (item_date - today).days <= 365:
                item["status"] = "UPCOMING"
            else:
                item["status"] = "FUTURE"
        
        return sorted(timeline, key=lambda x: x["date"])


__all__ = [
    # KSeF
    'KSeFEnvironment', 'InvoiceType', 'PaymentMethod', 'VATRate',
    'KSeFAddress', 'KSeFParty', 'KSeFInvoiceLine', 'KSeFInvoice',
    'KSeFResponse', 'KSeFXMLGenerator', 'KSeFClient', 'create_simple_invoice',
    
    # E-Doręczenia
    'EDoreczeniaEnvironment', 'DocumentType', 'DeliveryStatus', 'RecipientType',
    'EDoreczeniaAddress', 'EDoreczeniaDocument', 'EDoreczeniaMessage',
    'EDoreczeniaDeliveryConfirmation', 'EDoreczeniaResponse',
    'BAEClient', 'EDoreczeniaClient', 'EDoreczeniaComplianceChecker',
    
    # ESG/CSRD
    'ESGCategory', 'ESRSStandard', 'EmissionScope', 'CSRDEntitySize',
    'GHGEmission', 'EnergyConsumption', 'WaterConsumption', 'WasteGeneration',
    'EnvironmentalData', 'WorkforceMetrics', 'HealthSafetyMetrics', 'SocialData',
    'BoardComposition', 'EthicsCompliance', 'GovernanceData', 'ESGReport',
    'CSRDComplianceChecker', 'CarbonCalculator', 'ESGReportGenerator',
    
    # CBAM
    'CBAMProduct', 'CBAMPhase', 'CBAM_CN_CODES', 'DEFAULT_EMISSION_FACTORS',
    'CBAMImport', 'CBAMQuarterlyReport', 'CBAMCertificate', 'CBAMAnnualDeclaration',
    'CBAMCalculator', 'CBAMComplianceChecker', 'CBAMReportGenerator',
    
    # ViDA
    'VATScheme', 'TransactionType', 'EUCountry', 'EU_VAT_RATES',
    'VATRegistration', 'VATTransaction', 'OSSDeclaration', 'DAC7Report',
    'EUVATCalculator', 'ViDAComplianceChecker', 'DAC7Reporter',
    
    # Unified
    'ComplianceChecker',
]
