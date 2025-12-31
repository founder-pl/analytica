# ANALYTICA Compliance Module

## Przegląd

Moduł Compliance zapewnia pełne wsparcie dla regulacji prawnych wchodzących w życie w Polsce i Unii Europejskiej w latach 2025-2030.

## 📅 Harmonogram Regulacji

```
2025-01-01  ├── CSRD (duże spółki giełdowe >500 pracowników)
            ├── ViDA - Single VAT Registration
            └── Platform Economy (ViDA)

2026-01-01  ├── E-Doręczenia (obowiązkowe dla firm)
            ├── CBAM (pełne wdrożenie - certyfikaty)
            └── CSRD (duże przedsiębiorstwa >250 pracowników)

2026-02-01  └── KSeF (obowiązkowy w Polsce)

2027-01-01  └── CSRD (MŚP giełdowe)

2028-01-01  └── ViDA - E-fakturowanie wewnątrzunijne

2030-01-01  └── ViDA - Pełne wdrożenie
```

---

## 🇵🇱 KSeF - Krajowy System e-Faktur

### Opis
Obowiązkowy system e-fakturowania w Polsce od 1 lutego 2026. Wszystkie faktury VAT muszą być wystawiane przez KSeF.

### Funkcjonalności
- Generowanie faktur w formacie FA(2)
- Wysyłanie do KSeF API
- Pobieranie UPO (Urzędowe Poświadczenie Odbioru)
- Walidacja zgodności ze schematem
- Tryb awaryjny (offline)
- Obsługa korekt

### Użycie

```python
from analytica.compliance import (
    KSeFClient, KSeFEnvironment,
    create_simple_invoice
)

# Tworzenie faktury
invoice = create_simple_invoice(
    seller_nip="1234567890",
    seller_name="Moja Firma Sp. z o.o.",
    buyer_nip="0987654321",
    buyer_name="Klient S.A.",
    items=[
        {"name": "Usługa consultingowa", "quantity": 10, "unit_price": 200, "vat": "23"},
        {"name": "Licencja software", "quantity": 1, "unit_price": 5000, "vat": "23"}
    ]
)

# Wysyłanie do KSeF
with KSeFClient(
    nip="1234567890",
    token="your-ksef-token",
    environment=KSeFEnvironment.TEST
) as client:
    response = client.send_invoice(invoice)
    
    if response.success:
        print(f"KSeF Reference: {response.ksef_reference_number}")
        
        # Pobierz UPO
        upo_pdf = client.get_upo(response.ksef_reference_number)
```

### Typy faktur
- `VAT` - Faktura VAT
- `VAT_CORRECTION` - Faktura korygująca
- `VAT_ADVANCE` - Faktura zaliczkowa
- `VAT_RR` - Faktura VAT RR (rolnik ryczałtowy)

---

## 📧 E-Doręczenia

### Opis
System doręczeń elektronicznych obowiązkowy dla podmiotów publicznych i firm od 1 stycznia 2026.

### Funkcjonalności
- Wysyłanie dokumentów przez e-Doręczenia
- Odbieranie korespondencji
- Wyszukiwanie adresów ADE w BAE
- Potwierdzenia doręczeń z podpisem kwalifikowanym
- Integracja z KSeF (wysyłanie faktur)

### Użycie

```python
from analytica.compliance import (
    EDoreczeniaClient, EDoreczeniaDocument,
    EDoreczeniaMessage, EDoreczeniaAddress,
    RecipientType
)

# Klient e-Doręczeń
client = EDoreczeniaClient(
    ade="AE:PL-12345-67890-12345-12",
    api_key="your-api-key"
)

# Wyszukaj adresata
recipient = client.lookup_recipient(nip="0987654321")

# Wyślij fakturę
response = client.send_invoice(
    recipient_ade=recipient.ade,
    recipient_name=recipient.name,
    invoice_pdf=invoice_bytes,
    invoice_number="FV/2024/001",
    ksef_number="1234567890-20240115-ABC123"  # Opcjonalnie
)

# Sprawdź zgodność
from analytica.compliance import EDoreczeniaComplianceChecker

check = EDoreczeniaComplianceChecker.check_compliance(
    entity_type="KRS",
    has_ade=True,
    ade_active=True
)
print(check["recommendations"])
```

---

## 🌱 ESG / CSRD - Raportowanie Zrównoważonego Rozwoju

### Opis
Corporate Sustainability Reporting Directive - obowiązkowe raportowanie ESG według standardów ESRS.

### Terminy
- 2025: Duże spółki giełdowe (>500 pracowników)
- 2026: Duże przedsiębiorstwa (>250 pracowników, >40M EUR)
- 2027: MŚP giełdowe

### Funkcjonalności
- Obliczanie emisji GHG (Scope 1, 2, 3)
- Metryki środowiskowe (energia, woda, odpady)
- Metryki społeczne (pracownicy, BHP, różnorodność)
- Metryki zarządcze (zarząd, etyka)
- Generowanie raportów ESG
- Scoring ESG

### Użycie

```python
from analytica.compliance import (
    CSRDComplianceChecker, CarbonCalculator,
    ESGReport, EnvironmentalData, SocialData, GovernanceData,
    GHGEmission, EmissionScope, CSRDEntitySize
)
from decimal import Decimal

# Określ wielkość podmiotu
size = CSRDComplianceChecker.determine_entity_size(
    employees=300,
    revenue_eur=Decimal("50000000"),
    assets_eur=Decimal("25000000"),
    is_listed=False
)
print(f"Kategoria: {size}")  # CSRDEntitySize.LARGE

# Sprawdź zgodność
compliance = CSRDComplianceChecker.check_compliance(
    entity_size=size,
    has_report=False
)
print(compliance["recommendations"])

# Oblicz emisje CO2
scope1 = CarbonCalculator.calculate_scope1(
    natural_gas_kwh=Decimal("100000"),
    company_vehicles_km={"petrol": Decimal("50000")}
)

scope2 = CarbonCalculator.calculate_scope2(
    electricity_kwh=Decimal("500000"),
    country="pl",
    renewable_percentage=Decimal("20")
)

print(f"Scope 1: {scope1.amount_tonnes_co2e} tCO2e")
print(f"Scope 2: {scope2.amount_tonnes_co2e} tCO2e")

# Utwórz raport ESG
report = ESGReport(
    company_name="Moja Firma",
    reporting_year=2024,
    entity_size=size,
    environmental=EnvironmentalData(
        emissions=[scope1, scope2],
        science_based_targets=True,
        net_zero_target_year=2050
    ),
    social=SocialData(human_rights_policy=True),
    governance=GovernanceData()
)

# Score ESG
scores = report.get_esg_score()
print(f"ESG Score: E={scores['E']}, S={scores['S']}, G={scores['G']}")
```

---

## 🏭 CBAM - Carbon Border Adjustment Mechanism

### Opis
Mechanizm dostosowywania cen na granicach z uwzględnieniem emisji CO2 dla importów spoza UE.

### Produkty objęte
- Cement (CN 2523)
- Żelazo i stal (CN 72xx, 73xx)
- Aluminium (CN 76xx)
- Nawozy (CN 28xx, 31xx)
- Energia elektryczna (CN 2716)
- Wodór (CN 2804)

### Fazy
- 2023-2025: Okres przejściowy (raportowanie kwartalne)
- Od 2026: Pełne wdrożenie (certyfikaty CBAM)

### Użycie

```python
from analytica.compliance import (
    CBAMCalculator, CBAMComplianceChecker,
    CBAMImport, CBAMQuarterlyReport, CBAMProduct
)
from decimal import Decimal
from datetime import date

# Sprawdź czy produkt jest objęty CBAM
is_cbam = CBAMCalculator.is_cbam_product("7208")  # Stal
print(f"Objęty CBAM: {is_cbam}")

# Oblicz emisje dla importu
emissions = CBAMCalculator.calculate_import_emissions(
    cn_code="7208",
    quantity_tonnes=Decimal("100"),
    country_of_origin="CN"
)
print(f"Emisje: {emissions['emissions_tco2']} tCO2")

# Oblicz zobowiązanie CBAM
liability = CBAMCalculator.calculate_cbam_liability(
    emissions_tco2=Decimal("185"),  # 100t stali * 1.85 tCO2/t
    carbon_price_paid_eur=Decimal("1000"),  # Cena CO2 w Chinach
    free_allocation_tco2=Decimal("20")  # Darmowe przydziały EU ETS
)
print(f"Netto do zapłaty: {liability['net_liability_eur']} EUR")
print(f"Certyfikaty: {liability['certificates_required']}")

# Utwórz raport kwartalny
report = CBAMQuarterlyReport(
    year=2024,
    quarter=4,
    importer_name="Moja Firma",
    importer_eori="PL123456789000000",
    imports=[
        CBAMImport(
            import_id="IMP-001",
            import_date=date(2024, 10, 15),
            cn_code="7208",
            product_category=CBAMProduct.IRON_STEEL,
            description="Blacha stalowa",
            quantity_tonnes=Decimal("100"),
            country_of_origin="CN",
            customs_value_eur=Decimal("50000")
        )
    ]
)
report.calculate_totals()

# Sprawdź zgodność raportowania
compliance = CBAMComplianceChecker.check_quarterly_report_compliance(
    year=2024,
    quarter=4,
    report_submitted=False
)
print(compliance["recommendations"])
```

---

## 💶 ViDA - VAT in the Digital Age

### Opis
Reforma VAT w UE obejmująca e-fakturowanie, uproszczoną rejestrację VAT i odpowiedzialność platform.

### Komponenty
- **DRR** - Digital Reporting Requirements (e-fakturowanie)
- **SVR** - Single VAT Registration
- **Platform Economy** - Odpowiedzialność platform
- **DAC7/DAC8** - Wymiana informacji podatkowych

### Użycie

```python
from analytica.compliance import (
    EUVATCalculator, ViDAComplianceChecker,
    EUCountry, DAC7Reporter
)
from decimal import Decimal

# Oblicz VAT dla transakcji
result = EUVATCalculator.calculate_vat(
    net_amount=Decimal("1000"),
    seller_country=EUCountry.PL,
    buyer_country="DE",
    is_b2c=False,
    buyer_vat_number="DE123456789"
)
print(f"VAT: {result['vat_amount']} EUR")
print(f"Schemat: {result['scheme']}")  # reverse_charge

# Sprawdź wymóg OSS
oss_check = EUVATCalculator.check_oss_requirement(
    seller_country=EUCountry.PL,
    annual_b2c_sales_other_eu=Decimal("15000")
)
print(f"OSS wymagany: {oss_check['oss_recommended']}")

# Sprawdź gotowość ViDA
readiness = ViDAComplianceChecker.check_e_invoicing_readiness(
    has_einvoicing_system=True,
    ksef_ready=True,
    peppol_ready=False,
    structured_invoice_format="UBL"
)
print(f"Gotowość: {readiness['readiness_score']}%")

# Sprawdź obowiązki platformy
platform_check = ViDAComplianceChecker.check_platform_obligations(
    is_platform=True,
    facilitates_sales=True,
    sellers_count=50,
    annual_gmv_eur=Decimal("5000000")
)
print(f"DAC7 wymagany: {platform_check['dac7_obligations']['reporting_required']}")
```

---

## 🔧 Zunifikowany Compliance Checker

### Użycie

```python
from analytica.compliance import ComplianceChecker

# Utwórz checker dla firmy
checker = ComplianceChecker(
    company_name="Moja Firma Sp. z o.o.",
    nip="1234567890",
    country="PL",
    employees=150,
    revenue_eur=10000000,
    is_listed=False
)

# Sprawdź wszystkie regulacje
results = checker.check_all()
for reg_name, reg_data in results["regulations"].items():
    print(f"\n{reg_name.upper()}:")
    print(f"  Status: {reg_data.get('status', 'N/A')}")
    if 'recommendations' in reg_data:
        for rec in reg_data['recommendations'][:2]:
            print(f"  - {rec}")

# Pobierz harmonogram
timeline = checker.get_timeline()
for item in timeline[:5]:
    print(f"{item['date']} [{item['status']}] {item['regulation']}: {item['description']}")
```

---

## 📊 Tabela Stawek VAT UE

| Kraj | Stawka |
|------|--------|
| 🇦🇹 Austria | 20% |
| 🇧🇪 Belgia | 21% |
| 🇧🇬 Bułgaria | 20% |
| 🇭🇷 Chorwacja | 25% |
| 🇨🇾 Cypr | 19% |
| 🇨🇿 Czechy | 21% |
| 🇩🇰 Dania | 25% |
| 🇪🇪 Estonia | 22% |
| 🇫🇮 Finlandia | 24% |
| 🇫🇷 Francja | 20% |
| 🇩🇪 Niemcy | 19% |
| 🇬🇷 Grecja | 24% |
| 🇭🇺 Węgry | 27% |
| 🇮🇪 Irlandia | 23% |
| 🇮🇹 Włochy | 22% |
| 🇱🇻 Łotwa | 21% |
| 🇱🇹 Litwa | 21% |
| 🇱🇺 Luksemburg | 17% |
| 🇲🇹 Malta | 18% |
| 🇳🇱 Holandia | 21% |
| 🇵🇱 Polska | 23% |
| 🇵🇹 Portugalia | 23% |
| 🇷🇴 Rumunia | 19% |
| 🇸🇰 Słowacja | 20% |
| 🇸🇮 Słowenia | 22% |
| 🇪🇸 Hiszpania | 21% |
| 🇸🇪 Szwecja | 25% |

---

## 🧪 Testowanie

```bash
# Wszystkie testy compliance
pytest tests/unit/test_compliance.py -v

# Testy KSeF
pytest tests/unit/test_compliance.py::TestKSeF -v

# Testy CBAM
pytest tests/unit/test_compliance.py::TestCBAM -v
```

---

## 📚 Dokumentacja zewnętrzna

- [KSeF - Ministerstwo Finansów](https://www.podatki.gov.pl/ksef/)
- [E-Doręczenia](https://www.gov.pl/web/e-doreczenia)
- [CSRD - Komisja Europejska](https://finance.ec.europa.eu/capital-markets-union-and-financial-markets/company-reporting-and-auditing/company-reporting/corporate-sustainability-reporting_en)
- [CBAM - EU Taxation](https://taxation-customs.ec.europa.eu/carbon-border-adjustment-mechanism_en)
- [ViDA - VAT in Digital Age](https://taxation-customs.ec.europa.eu/vat-digital-age_en)
