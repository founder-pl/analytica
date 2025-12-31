"""
ANALYTICA Compliance - KSeF Integration
========================================

Krajowy System e-Faktur (KSeF) - obowiązkowy od 1 lutego 2026

Funkcjonalności:
- Generowanie faktur ustrukturyzowanych (FA)
- Wysyłanie do KSeF API
- Pobieranie UPO (Urzędowe Poświadczenie Odbioru)
- Walidacja zgodności ze schematem FA(2)
- Obsługa tokenów autoryzacyjnych
- Tryb awaryjny (offline)

Dokumentacja: https://www.podatki.gov.pl/ksef/
Schema: FA(2) - Faktura ustrukturyzowana v2
"""

from typing import Any, Dict, List, Optional, Union, Tuple
from dataclasses import dataclass, field
from datetime import datetime, date
from decimal import Decimal
from enum import Enum
import xml.etree.ElementTree as ET
import hashlib
import base64
import json
import re
from abc import ABC, abstractmethod

import httpx


# ============================================================
# ENUMS & CONSTANTS
# ============================================================

class KSeFEnvironment(Enum):
    """KSeF environments"""
    PRODUCTION = "https://ksef.mf.gov.pl/api"
    TEST = "https://ksef-test.mf.gov.pl/api"
    DEMO = "https://ksef-demo.mf.gov.pl/api"


class InvoiceType(Enum):
    """Typy faktur KSeF"""
    VAT = "VAT"                    # Faktura VAT
    VAT_CORRECTION = "KOR"         # Faktura korygująca
    VAT_ADVANCE = "ZAL"            # Faktura zaliczkowa
    VAT_SETTLEMENT = "ROZ"         # Faktura rozliczeniowa
    VAT_RR = "RR"                  # Faktura VAT RR (rolnik ryczałtowy)
    VAT_MP = "MP"                  # Metoda kasowa


class PaymentMethod(Enum):
    """Metody płatności"""
    TRANSFER = "1"      # Przelew
    CASH = "2"          # Gotówka
    CARD = "3"          # Karta
    CHECK = "4"         # Czek
    CREDIT = "5"        # Kredyt
    COMPENSATION = "6"  # Kompensata
    OTHER = "7"         # Inna


class VATRate(Enum):
    """Stawki VAT"""
    VAT_23 = "23"
    VAT_8 = "8"
    VAT_5 = "5"
    VAT_0 = "0"
    ZW = "zw"           # Zwolniony
    NP = "np"           # Nie podlega
    OO = "oo"           # Odwrotne obciążenie


# ============================================================
# DATA MODELS
# ============================================================

@dataclass
class KSeFAddress:
    """Adres w formacie KSeF"""
    country_code: str = "PL"
    postal_code: str = ""
    city: str = ""
    street: str = ""
    building_number: str = ""
    apartment_number: str = ""
    
    def to_xml_dict(self) -> Dict:
        return {
            "KodKraju": self.country_code,
            "AdresL1": f"{self.street} {self.building_number}",
            "AdresL2": f"{self.postal_code} {self.city}"
        }


@dataclass
class KSeFParty:
    """Podmiot w KSeF (sprzedawca/nabywca)"""
    nip: str
    name: str
    address: KSeFAddress
    email: Optional[str] = None
    phone: Optional[str] = None
    
    def validate(self) -> List[str]:
        """Walidacja danych podmiotu"""
        errors = []
        if not self.nip or len(self.nip) != 10:
            errors.append("NIP musi mieć 10 cyfr")
        if not self.name:
            errors.append("Nazwa jest wymagana")
        if not self.address.city:
            errors.append("Miasto jest wymagane")
        return errors


@dataclass
class KSeFInvoiceLine:
    """Pozycja faktury KSeF"""
    line_number: int
    name: str
    quantity: Decimal
    unit: str
    unit_price_net: Decimal
    vat_rate: VATRate
    net_amount: Decimal
    vat_amount: Decimal
    gross_amount: Decimal
    pkwiu: Optional[str] = None  # PKWiU (Polish Classification)
    cn: Optional[str] = None     # Combined Nomenclature (EU)
    gtu: Optional[str] = None    # Grupa Towarowa (GTU_01 - GTU_13)
    
    @classmethod
    def calculate(
        cls,
        line_number: int,
        name: str,
        quantity: Decimal,
        unit: str,
        unit_price_net: Decimal,
        vat_rate: VATRate,
        **kwargs
    ) -> 'KSeFInvoiceLine':
        """Automatyczne obliczenie kwot"""
        net_amount = quantity * unit_price_net
        
        if vat_rate in (VATRate.ZW, VATRate.NP, VATRate.OO):
            vat_amount = Decimal("0")
        else:
            vat_percent = Decimal(vat_rate.value) / 100
            vat_amount = net_amount * vat_percent
        
        gross_amount = net_amount + vat_amount
        
        return cls(
            line_number=line_number,
            name=name,
            quantity=quantity,
            unit=unit,
            unit_price_net=unit_price_net,
            vat_rate=vat_rate,
            net_amount=net_amount.quantize(Decimal("0.01")),
            vat_amount=vat_amount.quantize(Decimal("0.01")),
            gross_amount=gross_amount.quantize(Decimal("0.01")),
            **kwargs
        )


@dataclass
class KSeFInvoice:
    """Faktura ustrukturyzowana KSeF"""
    # Identyfikacja
    invoice_number: str
    issue_date: date
    sale_date: date
    
    # Strony
    seller: KSeFParty
    buyer: KSeFParty
    
    # Pozycje
    lines: List[KSeFInvoiceLine]
    
    # Sumy
    total_net: Decimal = Decimal("0")
    total_vat: Decimal = Decimal("0")
    total_gross: Decimal = Decimal("0")
    
    # Płatność
    payment_method: PaymentMethod = PaymentMethod.TRANSFER
    payment_due_date: Optional[date] = None
    bank_account: Optional[str] = None
    
    # Typ i dodatkowe
    invoice_type: InvoiceType = InvoiceType.VAT
    currency: str = "PLN"
    notes: Optional[str] = None
    
    # KSeF metadata
    ksef_reference_number: Optional[str] = None
    ksef_session_id: Optional[str] = None
    ksef_timestamp: Optional[datetime] = None
    
    # Korekta
    original_invoice_number: Optional[str] = None
    original_ksef_number: Optional[str] = None
    correction_reason: Optional[str] = None
    
    # GTU i procedury
    gtu_codes: List[str] = field(default_factory=list)
    procedure_codes: List[str] = field(default_factory=list)  # SW, EE, TP, etc.
    
    def calculate_totals(self):
        """Przelicz sumy z pozycji"""
        self.total_net = sum(line.net_amount for line in self.lines)
        self.total_vat = sum(line.vat_amount for line in self.lines)
        self.total_gross = sum(line.gross_amount for line in self.lines)
    
    def validate(self) -> List[str]:
        """Pełna walidacja faktury"""
        errors = []
        
        # Walidacja stron
        errors.extend([f"Sprzedawca: {e}" for e in self.seller.validate()])
        errors.extend([f"Nabywca: {e}" for e in self.buyer.validate()])
        
        # Walidacja dat
        if self.issue_date < self.sale_date:
            errors.append("Data wystawienia nie może być wcześniejsza niż data sprzedaży")
        
        # Walidacja pozycji
        if not self.lines:
            errors.append("Faktura musi mieć co najmniej jedną pozycję")
        
        for i, line in enumerate(self.lines):
            if line.quantity <= 0:
                errors.append(f"Pozycja {i+1}: ilość musi być większa od 0")
            if line.unit_price_net < 0:
                errors.append(f"Pozycja {i+1}: cena nie może być ujemna")
        
        # Walidacja sum
        calculated_net = sum(line.net_amount for line in self.lines)
        if abs(calculated_net - self.total_net) > Decimal("0.01"):
            errors.append("Suma netto nie zgadza się z pozycjami")
        
        # Walidacja korekty
        if self.invoice_type == InvoiceType.VAT_CORRECTION:
            if not self.original_invoice_number:
                errors.append("Korekta wymaga numeru faktury pierwotnej")
            if not self.correction_reason:
                errors.append("Korekta wymaga podania przyczyny")
        
        return errors


@dataclass
class KSeFResponse:
    """Odpowiedź z KSeF API"""
    success: bool
    ksef_reference_number: Optional[str] = None
    timestamp: Optional[datetime] = None
    session_id: Optional[str] = None
    upo: Optional[bytes] = None  # UPO - PDF
    errors: List[str] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)
    raw_response: Dict = field(default_factory=dict)


# ============================================================
# XML GENERATOR
# ============================================================

class KSeFXMLGenerator:
    """Generator XML faktur w formacie FA(2) KSeF"""
    
    NAMESPACE = "http://crd.gov.pl/wzor/2023/06/29/12648/"
    XSI_NAMESPACE = "http://www.w3.org/2001/XMLSchema-instance"
    
    def generate(self, invoice: KSeFInvoice) -> str:
        """Generuj XML faktury"""
        # Root element
        root = ET.Element("Faktura")
        root.set("xmlns", self.NAMESPACE)
        root.set("xmlns:xsi", self.XSI_NAMESPACE)
        
        # Nagłówek
        naglowek = ET.SubElement(root, "Naglowek")
        ET.SubElement(naglowek, "KodFormularza").text = "FA"
        ET.SubElement(naglowek, "WariantFormularza").text = "2"
        ET.SubElement(naglowek, "DataWytworzeniaFa").text = datetime.now().isoformat()
        ET.SubElement(naglowek, "SystemInfo").text = "ANALYTICA"
        
        # Podmiot1 - Sprzedawca
        podmiot1 = ET.SubElement(root, "Podmiot1")
        self._add_party(podmiot1, invoice.seller, "Sprzedawca")
        
        # Podmiot2 - Nabywca
        podmiot2 = ET.SubElement(root, "Podmiot2")
        self._add_party(podmiot2, invoice.buyer, "Nabywca")
        
        # Fa - dane faktury
        fa = ET.SubElement(root, "Fa")
        ET.SubElement(fa, "KodWaluty").text = invoice.currency
        ET.SubElement(fa, "P_1").text = invoice.issue_date.isoformat()
        ET.SubElement(fa, "P_1M").text = invoice.issue_date.strftime("%Y-%m")
        ET.SubElement(fa, "P_2").text = invoice.invoice_number
        
        if invoice.sale_date != invoice.issue_date:
            ET.SubElement(fa, "P_6").text = invoice.sale_date.isoformat()
        
        # Typ faktury
        if invoice.invoice_type == InvoiceType.VAT_CORRECTION:
            ET.SubElement(fa, "RodzajFaktury").text = "KOR"
            if invoice.original_ksef_number:
                ET.SubElement(fa, "NrFaKorygowanej").text = invoice.original_invoice_number
                ET.SubElement(fa, "NrKSeFKorygowanej").text = invoice.original_ksef_number
            ET.SubElement(fa, "PrzyczynaKorekty").text = invoice.correction_reason
        
        # Pozycje
        for line in invoice.lines:
            self._add_invoice_line(fa, line)
        
        # Podsumowanie VAT
        self._add_vat_summary(fa, invoice)
        
        # Płatność
        platnosc = ET.SubElement(fa, "Platnosc")
        ET.SubElement(platnosc, "TerminPlatnosci").text = (
            invoice.payment_due_date.isoformat() 
            if invoice.payment_due_date 
            else invoice.issue_date.isoformat()
        )
        ET.SubElement(platnosc, "FormaPlatnosci").text = invoice.payment_method.value
        
        if invoice.bank_account:
            ET.SubElement(platnosc, "RachunekBankowy").text = invoice.bank_account
        
        # GTU
        if invoice.gtu_codes:
            oznaczenia = ET.SubElement(fa, "FaWiersz", {"typ": "G"})
            for gtu in invoice.gtu_codes:
                ET.SubElement(oznaczenia, gtu).text = "1"
        
        # Procedury
        if invoice.procedure_codes:
            procedury = ET.SubElement(fa, "Procedura")
            for proc in invoice.procedure_codes:
                ET.SubElement(procedury, proc).text = "1"
        
        # Uwagi
        if invoice.notes:
            ET.SubElement(fa, "DodatkowyOpis").text = invoice.notes
        
        return ET.tostring(root, encoding="unicode", xml_declaration=True)
    
    def _add_party(self, parent: ET.Element, party: KSeFParty, role: str):
        """Dodaj dane podmiotu"""
        dane = ET.SubElement(parent, f"Dane{role}")
        ET.SubElement(dane, "NIP").text = party.nip
        ET.SubElement(dane, "Nazwa").text = party.name
        
        adres = ET.SubElement(dane, "Adres")
        for key, value in party.address.to_xml_dict().items():
            ET.SubElement(adres, key).text = value
        
        if party.email:
            ET.SubElement(dane, "Email").text = party.email
        if party.phone:
            ET.SubElement(dane, "Telefon").text = party.phone
    
    def _add_invoice_line(self, parent: ET.Element, line: KSeFInvoiceLine):
        """Dodaj pozycję faktury"""
        wiersz = ET.SubElement(parent, "FaWiersz")
        
        ET.SubElement(wiersz, "NrWierszaFa").text = str(line.line_number)
        ET.SubElement(wiersz, "P_7").text = line.name
        ET.SubElement(wiersz, "P_8A").text = line.unit
        ET.SubElement(wiersz, "P_8B").text = str(line.quantity)
        ET.SubElement(wiersz, "P_9A").text = str(line.unit_price_net)
        ET.SubElement(wiersz, "P_11").text = str(line.net_amount)
        ET.SubElement(wiersz, "P_12").text = line.vat_rate.value
        
        if line.pkwiu:
            ET.SubElement(wiersz, "PKWiU").text = line.pkwiu
        if line.cn:
            ET.SubElement(wiersz, "CN").text = line.cn
        if line.gtu:
            ET.SubElement(wiersz, line.gtu).text = "1"
    
    def _add_vat_summary(self, parent: ET.Element, invoice: KSeFInvoice):
        """Dodaj podsumowanie VAT"""
        # Grupuj według stawki
        by_rate: Dict[str, Dict[str, Decimal]] = {}
        
        for line in invoice.lines:
            rate = line.vat_rate.value
            if rate not in by_rate:
                by_rate[rate] = {"net": Decimal("0"), "vat": Decimal("0")}
            by_rate[rate]["net"] += line.net_amount
            by_rate[rate]["vat"] += line.vat_amount
        
        # Sumy według stawek
        for rate, amounts in by_rate.items():
            if rate == "23":
                ET.SubElement(parent, "P_13_1").text = str(amounts["net"])
                ET.SubElement(parent, "P_14_1").text = str(amounts["vat"])
            elif rate == "8":
                ET.SubElement(parent, "P_13_2").text = str(amounts["net"])
                ET.SubElement(parent, "P_14_2").text = str(amounts["vat"])
            elif rate == "5":
                ET.SubElement(parent, "P_13_3").text = str(amounts["net"])
                ET.SubElement(parent, "P_14_3").text = str(amounts["vat"])
            elif rate == "0":
                ET.SubElement(parent, "P_13_6").text = str(amounts["net"])
            elif rate == "zw":
                ET.SubElement(parent, "P_13_7").text = str(amounts["net"])
        
        # Suma końcowa
        ET.SubElement(parent, "P_15").text = str(invoice.total_gross)


# ============================================================
# KSeF API CLIENT
# ============================================================

class KSeFClient:
    """
    Klient KSeF API
    
    Obsługuje:
    - Autoryzację tokenem
    - Wysyłanie faktur
    - Pobieranie UPO
    - Pobieranie faktur
    - Tryb awaryjny
    """
    
    def __init__(
        self,
        nip: str,
        token: str,
        environment: KSeFEnvironment = KSeFEnvironment.TEST,
        timeout: float = 30.0
    ):
        self.nip = nip
        self.token = token
        self.environment = environment
        self.base_url = environment.value
        self.timeout = timeout
        self._client: Optional[httpx.Client] = None
        self._session_token: Optional[str] = None
        self._session_reference: Optional[str] = None
        self._xml_generator = KSeFXMLGenerator()
    
    def _get_client(self) -> httpx.Client:
        if self._client is None:
            self._client = httpx.Client(timeout=self.timeout)
        return self._client
    
    def _auth_headers(self) -> Dict[str, str]:
        headers = {
            "Content-Type": "application/json",
            "Accept": "application/json"
        }
        if self._session_token:
            headers["SessionToken"] = self._session_token
        return headers
    
    # ----------------------------------------------------------
    # SESSION MANAGEMENT
    # ----------------------------------------------------------
    
    def init_session(self) -> bool:
        """Inicjalizacja sesji interaktywnej"""
        try:
            # Krok 1: Inicjalizacja
            init_response = self._get_client().post(
                f"{self.base_url}/online/Session/InitSigned",
                headers={"Content-Type": "application/json"},
                json={
                    "Context": {
                        "Challenge": self._generate_challenge(),
                        "Identifier": {
                            "Type": "onip",
                            "Identifier": self.nip
                        }
                    }
                }
            )
            init_response.raise_for_status()
            init_data = init_response.json()
            
            self._session_reference = init_data.get("ReferenceNumber")
            
            # Krok 2: Autoryzacja tokenem
            auth_response = self._get_client().post(
                f"{self.base_url}/online/Session/AuthoriseToken",
                headers={"Content-Type": "application/json"},
                json={
                    "ReferenceNumber": self._session_reference,
                    "Token": self.token
                }
            )
            auth_response.raise_for_status()
            auth_data = auth_response.json()
            
            self._session_token = auth_data.get("SessionToken", {}).get("Token")
            
            return self._session_token is not None
            
        except Exception as e:
            print(f"Session init error: {e}")
            return False
    
    def terminate_session(self) -> bool:
        """Zakończenie sesji"""
        if not self._session_token:
            return True
        
        try:
            response = self._get_client().get(
                f"{self.base_url}/online/Session/Terminate",
                headers=self._auth_headers()
            )
            response.raise_for_status()
            
            self._session_token = None
            self._session_reference = None
            return True
            
        except Exception:
            return False
    
    # ----------------------------------------------------------
    # INVOICE OPERATIONS
    # ----------------------------------------------------------
    
    def send_invoice(self, invoice: KSeFInvoice) -> KSeFResponse:
        """Wyślij fakturę do KSeF"""
        # Walidacja
        errors = invoice.validate()
        if errors:
            return KSeFResponse(success=False, errors=errors)
        
        # Generuj XML
        xml_content = self._xml_generator.generate(invoice)
        
        # Oblicz hash
        xml_hash = self._calculate_hash(xml_content)
        
        try:
            # Wyślij
            response = self._get_client().put(
                f"{self.base_url}/online/Invoice/Send",
                headers={
                    **self._auth_headers(),
                    "Content-Type": "application/octet-stream"
                },
                content=xml_content.encode('utf-8')
            )
            response.raise_for_status()
            
            data = response.json()
            
            return KSeFResponse(
                success=True,
                ksef_reference_number=data.get("ElementReferenceNumber"),
                timestamp=datetime.fromisoformat(data.get("Timestamp", "").replace("Z", "+00:00")) if data.get("Timestamp") else None,
                session_id=self._session_reference,
                raw_response=data
            )
            
        except httpx.HTTPStatusError as e:
            return KSeFResponse(
                success=False,
                errors=[f"HTTP {e.response.status_code}: {e.response.text}"]
            )
        except Exception as e:
            return KSeFResponse(success=False, errors=[str(e)])
    
    def get_invoice_status(self, ksef_reference: str) -> Dict:
        """Pobierz status faktury"""
        response = self._get_client().get(
            f"{self.base_url}/online/Invoice/Status/{ksef_reference}",
            headers=self._auth_headers()
        )
        response.raise_for_status()
        return response.json()
    
    def get_invoice(self, ksef_number: str) -> Optional[str]:
        """Pobierz fakturę z KSeF (XML)"""
        response = self._get_client().get(
            f"{self.base_url}/online/Invoice/Get/{ksef_number}",
            headers=self._auth_headers()
        )
        response.raise_for_status()
        return response.text
    
    def get_upo(self, ksef_reference: str) -> Optional[bytes]:
        """Pobierz UPO (Urzędowe Poświadczenie Odbioru)"""
        response = self._get_client().get(
            f"{self.base_url}/online/Invoice/UPO/{ksef_reference}",
            headers={**self._auth_headers(), "Accept": "application/pdf"}
        )
        response.raise_for_status()
        return response.content
    
    # ----------------------------------------------------------
    # BATCH OPERATIONS
    # ----------------------------------------------------------
    
    def send_batch(self, invoices: List[KSeFInvoice]) -> List[KSeFResponse]:
        """Wyślij partię faktur"""
        results = []
        
        for invoice in invoices:
            result = self.send_invoice(invoice)
            results.append(result)
            
            # Rate limiting
            if result.success:
                import time
                time.sleep(0.5)  # KSeF rate limit
        
        return results
    
    def query_invoices(
        self,
        date_from: date,
        date_to: date,
        subject_type: str = "subject1"  # subject1=sprzedawca, subject2=nabywca
    ) -> List[Dict]:
        """Pobierz listę faktur z KSeF"""
        response = self._get_client().post(
            f"{self.base_url}/online/Query/Invoice/Sync",
            headers=self._auth_headers(),
            json={
                "QueryCriteria": {
                    "SubjectType": subject_type,
                    "Type": "incremental",
                    "AcquisitionTimestampThresholdFrom": f"{date_from}T00:00:00",
                    "AcquisitionTimestampThresholdTo": f"{date_to}T23:59:59"
                }
            }
        )
        response.raise_for_status()
        
        return response.json().get("InvoiceHeaderList", [])
    
    # ----------------------------------------------------------
    # OFFLINE/EMERGENCY MODE
    # ----------------------------------------------------------
    
    def generate_offline_invoice(self, invoice: KSeFInvoice) -> Tuple[str, str]:
        """
        Generuj fakturę w trybie awaryjnym (offline)
        
        Zwraca: (xml_content, offline_reference)
        """
        # W trybie offline generujemy unikalny numer referencyjny
        offline_ref = f"OFF-{self.nip}-{datetime.now().strftime('%Y%m%d%H%M%S')}"
        
        xml_content = self._xml_generator.generate(invoice)
        
        return xml_content, offline_ref
    
    def send_offline_invoices(self, offline_invoices: List[Tuple[str, str]]) -> List[KSeFResponse]:
        """
        Wyślij faktury z trybu awaryjnego po przywróceniu połączenia
        
        Args:
            offline_invoices: Lista (xml_content, offline_reference)
        """
        results = []
        
        for xml_content, offline_ref in offline_invoices:
            try:
                response = self._get_client().put(
                    f"{self.base_url}/online/Invoice/Send",
                    headers={
                        **self._auth_headers(),
                        "Content-Type": "application/octet-stream",
                        "X-Offline-Reference": offline_ref
                    },
                    content=xml_content.encode('utf-8')
                )
                response.raise_for_status()
                
                data = response.json()
                results.append(KSeFResponse(
                    success=True,
                    ksef_reference_number=data.get("ElementReferenceNumber"),
                    raw_response=data
                ))
                
            except Exception as e:
                results.append(KSeFResponse(
                    success=False,
                    errors=[f"Offline invoice {offline_ref}: {str(e)}"]
                ))
        
        return results
    
    # ----------------------------------------------------------
    # HELPERS
    # ----------------------------------------------------------
    
    def _generate_challenge(self) -> str:
        """Generuj challenge dla sesji"""
        import secrets
        return secrets.token_hex(16)
    
    def _calculate_hash(self, content: str) -> str:
        """Oblicz SHA-256 hash"""
        return hashlib.sha256(content.encode('utf-8')).hexdigest()
    
    def close(self):
        """Zamknij połączenie"""
        self.terminate_session()
        if self._client:
            self._client.close()
            self._client = None
    
    def __enter__(self):
        self.init_session()
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()


# ============================================================
# HELPER FUNCTIONS
# ============================================================

def create_simple_invoice(
    seller_nip: str,
    seller_name: str,
    buyer_nip: str,
    buyer_name: str,
    items: List[Dict],
    invoice_number: str = None
) -> KSeFInvoice:
    """
    Szybkie tworzenie prostej faktury
    
    items: [{"name": "...", "quantity": 1, "unit_price": 100, "vat": "23"}, ...]
    """
    if not invoice_number:
        invoice_number = f"FV/{datetime.now().strftime('%Y/%m/%d/%H%M%S')}"
    
    seller = KSeFParty(
        nip=seller_nip,
        name=seller_name,
        address=KSeFAddress()
    )
    
    buyer = KSeFParty(
        nip=buyer_nip,
        name=buyer_name,
        address=KSeFAddress()
    )
    
    lines = []
    for i, item in enumerate(items, 1):
        vat_rate = VATRate(item.get("vat", "23"))
        line = KSeFInvoiceLine.calculate(
            line_number=i,
            name=item["name"],
            quantity=Decimal(str(item.get("quantity", 1))),
            unit=item.get("unit", "szt"),
            unit_price_net=Decimal(str(item["unit_price"])),
            vat_rate=vat_rate,
            gtu=item.get("gtu")
        )
        lines.append(line)
    
    invoice = KSeFInvoice(
        invoice_number=invoice_number,
        issue_date=date.today(),
        sale_date=date.today(),
        seller=seller,
        buyer=buyer,
        lines=lines
    )
    invoice.calculate_totals()
    
    return invoice


__all__ = [
    'KSeFEnvironment',
    'InvoiceType',
    'PaymentMethod',
    'VATRate',
    'KSeFAddress',
    'KSeFParty',
    'KSeFInvoiceLine',
    'KSeFInvoice',
    'KSeFResponse',
    'KSeFXMLGenerator',
    'KSeFClient',
    'create_simple_invoice'
]
