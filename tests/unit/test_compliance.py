"""
ANALYTICA Tests - Compliance Module
====================================

Testy dla modułów zgodności z regulacjami:
- KSeF
- E-Doręczenia
- CSRD/ESG
- CBAM
- ViDA/VAT
"""

import pytest
from datetime import date
from decimal import Decimal
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent.parent / "src"))


# ============================================================
# KSeF TESTS
# ============================================================

@pytest.mark.unit
class TestKSeF:
    """Testy modułu KSeF"""
    
    def test_create_simple_invoice(self):
        """Test tworzenia prostej faktury"""
        from compliance.ksef import create_simple_invoice, VATRate
        
        invoice = create_simple_invoice(
            seller_nip="1234567890",
            seller_name="Test Sp. z o.o.",
            buyer_nip="0987654321",
            buyer_name="Kupujący S.A.",
            items=[
                {"name": "Usługa consultingowa", "quantity": 10, "unit_price": 200, "vat": "23"},
                {"name": "Szkolenie", "quantity": 1, "unit_price": 5000, "vat": "23"}
            ]
        )
        
        assert invoice is not None
        assert invoice.seller.nip == "1234567890"
        assert invoice.buyer.nip == "0987654321"
        assert len(invoice.lines) == 2
        
        # Sprawdź obliczenia
        invoice.calculate_totals()
        assert invoice.total_net == Decimal("7000.00")
    
    def test_invoice_validation(self):
        """Test walidacji faktury"""
        from compliance.ksef import (
            KSeFInvoice, KSeFParty, KSeFAddress, KSeFInvoiceLine, VATRate
        )
        
        # Faktura bez pozycji - powinna być nieważna
        invoice = KSeFInvoice(
            invoice_number="FV/2024/001",
            issue_date=date.today(),
            sale_date=date.today(),
            seller=KSeFParty(
                nip="1234567890",
                name="Sprzedawca",
                address=KSeFAddress(city="Warszawa")
            ),
            buyer=KSeFParty(
                nip="0987654321",
                name="Kupujący",
                address=KSeFAddress(city="Kraków")
            ),
            lines=[]  # Brak pozycji
        )
        
        errors = invoice.validate()
        assert len(errors) > 0
        assert any("pozycję" in e.lower() for e in errors)
    
    def test_invoice_line_calculation(self):
        """Test obliczania pozycji faktury"""
        from compliance.ksef import KSeFInvoiceLine, VATRate
        
        line = KSeFInvoiceLine.calculate(
            line_number=1,
            name="Produkt",
            quantity=Decimal("5"),
            unit="szt",
            unit_price_net=Decimal("100"),
            vat_rate=VATRate.VAT_23
        )
        
        assert line.net_amount == Decimal("500.00")
        assert line.vat_amount == Decimal("115.00")
        assert line.gross_amount == Decimal("615.00")
    
    def test_xml_generation(self):
        """Test generowania XML faktury"""
        from compliance.ksef import create_simple_invoice, KSeFXMLGenerator
        
        invoice = create_simple_invoice(
            seller_nip="1234567890",
            seller_name="Test",
            buyer_nip="0987654321",
            buyer_name="Kupujący",
            items=[{"name": "Test", "quantity": 1, "unit_price": 100}]
        )
        invoice.calculate_totals()
        
        generator = KSeFXMLGenerator()
        xml = generator.generate(invoice)
        
        assert xml is not None
        assert "<?xml" in xml
        assert "Faktura" in xml
        assert "1234567890" in xml


# ============================================================
# E-DORĘCZENIA TESTS
# ============================================================

@pytest.mark.unit
class TestEDoreczenia:
    """Testy modułu E-Doręczeń"""
    
    def test_address_validation(self):
        """Test walidacji adresu ADE"""
        from compliance.edoreczenia import EDoreczeniaAddress, RecipientType
        
        # Prawidłowy adres
        valid_address = EDoreczeniaAddress(
            ade="AE:PL-12345-67890-12345-12",
            name="Test Company",
            recipient_type=RecipientType.LEGAL_ENTITY,
            nip="1234567890"
        )
        
        errors = valid_address.validate()
        assert len(errors) == 0
        
        # Nieprawidłowy adres
        invalid_address = EDoreczeniaAddress(
            ade="INVALID",
            name="",
            recipient_type=RecipientType.LEGAL_ENTITY
        )
        
        errors = invalid_address.validate()
        assert len(errors) > 0
    
    def test_compliance_checker(self):
        """Test sprawdzania zgodności e-Doręczeń"""
        from compliance.edoreczenia import EDoreczeniaComplianceChecker
        
        # Podmiot bez ADE
        result = EDoreczeniaComplianceChecker.check_compliance(
            entity_type="KRS",
            has_ade=False
        )
        
        assert result["mandatory"] == True
        assert result["compliant"] == False
        assert len(result["recommendations"]) > 0
        
        # Podmiot z aktywnym ADE
        result = EDoreczeniaComplianceChecker.check_compliance(
            entity_type="KRS",
            has_ade=True,
            ade_active=True
        )
        
        assert result["compliant"] == True
    
    def test_document_from_bytes(self):
        """Test tworzenia dokumentu z bajtów"""
        from compliance.edoreczenia import EDoreczeniaDocument, DocumentType
        
        content = b"%PDF-1.4 test content"
        
        doc = EDoreczeniaDocument(
            title="Test Document",
            content=content,
            content_type="application/pdf",
            document_type=DocumentType.INVOICE
        )
        
        assert doc.get_hash() is not None
        assert len(doc.get_hash()) == 64  # SHA-256


# ============================================================
# ESG/CSRD TESTS
# ============================================================

@pytest.mark.unit
class TestESGCSRD:
    """Testy modułu ESG/CSRD"""
    
    def test_entity_size_determination(self):
        """Test określania wielkości podmiotu"""
        from compliance.esg_csrd import CSRDComplianceChecker, CSRDEntitySize
        
        # Duża spółka
        size = CSRDComplianceChecker.determine_entity_size(
            employees=300,
            revenue_eur=Decimal("50000000"),
            assets_eur=Decimal("25000000")
        )
        assert size == CSRDEntitySize.LARGE
        
        # MŚP
        size = CSRDComplianceChecker.determine_entity_size(
            employees=50,
            revenue_eur=Decimal("5000000"),
            assets_eur=Decimal("2000000")
        )
        assert size == CSRDEntitySize.SME
    
    def test_carbon_calculator_scope1(self):
        """Test kalkulatora CO2 - Scope 1"""
        from compliance.esg_csrd import CarbonCalculator, EmissionScope
        
        emission = CarbonCalculator.calculate_scope1(
            natural_gas_kwh=Decimal("100000"),
            heating_oil_kwh=Decimal("50000"),
            company_vehicles_km={"petrol": Decimal("50000")}
        )
        
        assert emission.scope == EmissionScope.SCOPE_1
        assert emission.amount_tonnes_co2e > 0
    
    def test_carbon_calculator_scope2(self):
        """Test kalkulatora CO2 - Scope 2"""
        from compliance.esg_csrd import CarbonCalculator, EmissionScope
        
        emission = CarbonCalculator.calculate_scope2(
            electricity_kwh=Decimal("500000"),
            country="pl",
            renewable_percentage=Decimal("20")
        )
        
        assert emission.scope == EmissionScope.SCOPE_2
        assert emission.amount_tonnes_co2e > 0
    
    def test_esg_report_score(self):
        """Test obliczania score ESG"""
        from compliance.esg_csrd import (
            ESGReport, EnvironmentalData, SocialData, GovernanceData,
            GHGEmission, EmissionScope, CSRDEntitySize
        )
        
        report = ESGReport(
            company_name="Test Company",
            reporting_year=2024,
            entity_size=CSRDEntitySize.LARGE,
            environmental=EnvironmentalData(
                emissions=[
                    GHGEmission(
                        scope=EmissionScope.SCOPE_1,
                        amount_tonnes_co2e=Decimal("1000"),
                        year=2024,
                        source="Test",
                        verified=True
                    )
                ],
                science_based_targets=True,
                net_zero_target_year=2050
            ),
            social=SocialData(human_rights_policy=True),
            governance=GovernanceData()
        )
        
        scores = report.get_esg_score()
        
        assert "E" in scores
        assert "S" in scores
        assert "G" in scores
        assert "Total" in scores
        assert scores["E"] > Decimal("50")  # Bonus za verified + SBT + net zero


# ============================================================
# CBAM TESTS
# ============================================================

@pytest.mark.unit
class TestCBAM:
    """Testy modułu CBAM"""
    
    def test_cbam_product_detection(self):
        """Test wykrywania produktów CBAM"""
        from compliance.cbam import CBAMCalculator, CBAMProduct
        
        # Stal - objęta CBAM
        assert CBAMCalculator.is_cbam_product("7208") == True
        assert CBAMCalculator.get_product_category("7208") == CBAMProduct.IRON_STEEL
        
        # Aluminium - objęte CBAM
        assert CBAMCalculator.is_cbam_product("7601") == True
        assert CBAMCalculator.get_product_category("7601") == CBAMProduct.ALUMINIUM
        
        # Tekstylia - nie objęte
        assert CBAMCalculator.is_cbam_product("6201") == False
    
    def test_cbam_import_emissions(self):
        """Test obliczania emisji dla importu"""
        from compliance.cbam import CBAMCalculator
        
        result = CBAMCalculator.calculate_import_emissions(
            cn_code="7208",
            quantity_tonnes=Decimal("100"),
            country_of_origin="CN"
        )
        
        assert result["covered"] == True
        assert result["product_category"] == "iron_steel"
        assert result["emissions_tco2"] > 0
    
    def test_cbam_liability_calculation(self):
        """Test obliczania zobowiązania CBAM"""
        from compliance.cbam import CBAMCalculator
        
        result = CBAMCalculator.calculate_cbam_liability(
            emissions_tco2=Decimal("100"),
            carbon_price_paid_eur=Decimal("1000"),
            free_allocation_tco2=Decimal("10"),
            eu_ets_price=Decimal("80")
        )
        
        assert result["total_emissions_tco2"] == 100
        assert result["net_emissions_tco2"] == 90  # 100 - 10
        assert result["gross_liability_eur"] == 7200  # 90 * 80
        assert result["net_liability_eur"] == 6200  # 7200 - 1000
    
    def test_cbam_compliance_checker(self):
        """Test sprawdzania zgodności CBAM"""
        from compliance.cbam import CBAMComplianceChecker, CBAMPhase
        
        phase = CBAMComplianceChecker.get_current_phase()
        assert phase in [CBAMPhase.TRANSITIONAL, CBAMPhase.FULL]
        
        # Sprawdź raport kwartalny
        result = CBAMComplianceChecker.check_quarterly_report_compliance(
            year=2024,
            quarter=3,
            report_submitted=False
        )
        
        assert "deadline" in result
        assert "is_overdue" in result
        assert "recommendations" in result


# ============================================================
# ViDA/VAT TESTS
# ============================================================

@pytest.mark.unit
class TestViDAVAT:
    """Testy modułu ViDA/VAT"""
    
    def test_vat_rates(self):
        """Test stawek VAT UE"""
        from compliance.vida_vat import EUVATCalculator, EUCountry
        
        assert EUVATCalculator.get_vat_rate(EUCountry.PL) == Decimal("23")
        assert EUVATCalculator.get_vat_rate(EUCountry.DE) == Decimal("19")
        assert EUVATCalculator.get_vat_rate(EUCountry.HU) == Decimal("27")
    
    def test_vat_calculation_domestic(self):
        """Test obliczania VAT - transakcja krajowa"""
        from compliance.vida_vat import EUVATCalculator, EUCountry
        
        result = EUVATCalculator.calculate_vat(
            net_amount=Decimal("1000"),
            seller_country=EUCountry.PL,
            buyer_country="PL",
            is_b2c=True
        )
        
        assert result["vat_rate"] == 23
        assert result["vat_amount"] == 230
        assert result["gross_amount"] == 1230
        assert result["scheme"] == "standard"
    
    def test_vat_calculation_intra_eu_b2b(self):
        """Test obliczania VAT - WDT B2B"""
        from compliance.vida_vat import EUVATCalculator, EUCountry
        
        result = EUVATCalculator.calculate_vat(
            net_amount=Decimal("1000"),
            seller_country=EUCountry.PL,
            buyer_country="DE",
            is_b2c=False,
            buyer_vat_number="DE123456789"
        )
        
        assert result["vat_rate"] == 0
        assert result["reverse_charge"] == True
        assert result["scheme"] == "reverse_charge"
    
    def test_vat_calculation_export(self):
        """Test obliczania VAT - eksport"""
        from compliance.vida_vat import EUVATCalculator, EUCountry
        
        result = EUVATCalculator.calculate_vat(
            net_amount=Decimal("1000"),
            seller_country=EUCountry.PL,
            buyer_country="US",  # Spoza UE
            is_b2c=True
        )
        
        assert result["vat_rate"] == 0
        assert result["scheme"] == "export"
    
    def test_oss_requirement(self):
        """Test sprawdzania wymogu OSS"""
        from compliance.vida_vat import EUVATCalculator, EUCountry
        
        # Poniżej progu
        result = EUVATCalculator.check_oss_requirement(
            seller_country=EUCountry.PL,
            annual_b2c_sales_other_eu=Decimal("5000")
        )
        assert result["oss_recommended"] == False
        
        # Powyżej progu
        result = EUVATCalculator.check_oss_requirement(
            seller_country=EUCountry.PL,
            annual_b2c_sales_other_eu=Decimal("15000")
        )
        assert result["oss_recommended"] == True
    
    def test_ioss_eligibility(self):
        """Test kwalifikacji IOSS"""
        from compliance.vida_vat import EUVATCalculator
        
        # Kwalifikuje się
        result = EUVATCalculator.check_ioss_eligibility(
            goods_value_eur=Decimal("100"),
            origin_country="CN"
        )
        assert result["eligible"] == True
        
        # Nie kwalifikuje się - za drogo
        result = EUVATCalculator.check_ioss_eligibility(
            goods_value_eur=Decimal("200"),
            origin_country="CN"
        )
        assert result["eligible"] == False
        
        # Nie kwalifikuje się - z UE
        result = EUVATCalculator.check_ioss_eligibility(
            goods_value_eur=Decimal("100"),
            origin_country="DE"
        )
        assert result["eligible"] == False
    
    def test_vida_compliance_checker(self):
        """Test sprawdzania zgodności ViDA"""
        from compliance.vida_vat import ViDAComplianceChecker
        
        result = ViDAComplianceChecker.check_e_invoicing_readiness(
            has_einvoicing_system=False,
            ksef_ready=False,
            peppol_ready=False
        )
        
        assert result["readiness_score"] == 0
        assert len(result["recommendations"]) > 0
        
        result = ViDAComplianceChecker.check_e_invoicing_readiness(
            has_einvoicing_system=True,
            ksef_ready=True,
            peppol_ready=True,
            structured_invoice_format="UBL"
        )
        
        assert result["readiness_score"] == 100


# ============================================================
# UNIFIED COMPLIANCE TESTS
# ============================================================

@pytest.mark.unit
class TestUnifiedCompliance:
    """Testy zunifikowanego sprawdzacza zgodności"""
    
    def test_compliance_checker_all(self):
        """Test sprawdzania wszystkich regulacji"""
        from compliance import ComplianceChecker
        
        checker = ComplianceChecker(
            company_name="Test Sp. z o.o.",
            nip="1234567890",
            country="PL",
            employees=100,
            revenue_eur=5000000
        )
        
        results = checker.check_all()
        
        assert results["company"] == "Test Sp. z o.o."
        assert "regulations" in results
        assert "ksef" in results["regulations"]
        assert "csrd" in results["regulations"]
        assert "cbam" in results["regulations"]
        assert "vida" in results["regulations"]
    
    def test_compliance_timeline(self):
        """Test harmonogramu wdrożeń"""
        from compliance import ComplianceChecker
        
        checker = ComplianceChecker(
            company_name="Test",
            nip="1234567890"
        )
        
        timeline = checker.get_timeline()
        
        assert len(timeline) > 0
        assert all("date" in item for item in timeline)
        assert all("regulation" in item for item in timeline)
        assert all("status" in item for item in timeline)
        
        # Powinien być posortowany
        dates = [item["date"] for item in timeline]
        assert dates == sorted(dates)


# ============================================================
# RUN TESTS
# ============================================================

if __name__ == "__main__":
    pytest.main([__file__, "-v"])
