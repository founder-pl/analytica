"""
ANALYTICA Integrations - Polish Accounting Systems
===================================================

Integrations with Polish accounting and invoicing systems:
- iFirma (ifirma.pl)
- Fakturownia (fakturownia.pl)
- inFakt (infakt.pl)
- wFirma (wfirma.pl)
"""

from typing import Any, Dict, List, Optional, Union
from dataclasses import dataclass, field
from datetime import datetime, date
from decimal import Decimal
from enum import Enum
import hashlib
import hmac
import json
import base64
from abc import ABC, abstractmethod

import httpx


# ============================================================
# BASE CLASSES
# ============================================================

class InvoiceType(Enum):
    SALES = "sales"
    PURCHASE = "purchase"
    PROFORMA = "proforma"
    CORRECTION = "correction"
    RECEIPT = "receipt"


class PaymentStatus(Enum):
    PAID = "paid"
    UNPAID = "unpaid"
    PARTIAL = "partial"
    OVERDUE = "overdue"


@dataclass
class Invoice:
    """Universal invoice model"""
    id: str
    number: str
    issue_date: date
    sale_date: date
    due_date: date
    buyer_name: str
    buyer_nip: Optional[str]
    buyer_address: str
    seller_name: str
    seller_nip: str
    net_amount: Decimal
    vat_amount: Decimal
    gross_amount: Decimal
    currency: str = "PLN"
    payment_status: PaymentStatus = PaymentStatus.UNPAID
    invoice_type: InvoiceType = InvoiceType.SALES
    items: List[Dict] = field(default_factory=list)
    source_system: str = ""
    raw_data: Dict = field(default_factory=dict)


@dataclass
class Contractor:
    """Contractor/Client model"""
    id: str
    name: str
    nip: Optional[str]
    address: str
    city: str
    postal_code: str
    country: str = "PL"
    email: Optional[str] = None
    phone: Optional[str] = None


@dataclass
class BankAccount:
    """Bank account model"""
    account_number: str
    bank_name: str
    swift: Optional[str] = None
    currency: str = "PLN"


class PolishAccountingClient(ABC):
    """Base class for Polish accounting system clients"""
    
    def __init__(self, timeout: float = 30.0):
        self.timeout = timeout
        self._client: Optional[httpx.Client] = None
    
    def _get_client(self) -> httpx.Client:
        if self._client is None:
            self._client = httpx.Client(timeout=self.timeout)
        return self._client
    
    @abstractmethod
    def authenticate(self) -> bool:
        """Authenticate with the service"""
        pass
    
    @abstractmethod
    def get_invoices(self, date_from: date = None, date_to: date = None) -> List[Invoice]:
        """Get invoices from the system"""
        pass
    
    @abstractmethod
    def get_invoice(self, invoice_id: str) -> Invoice:
        """Get single invoice by ID"""
        pass
    
    @abstractmethod
    def create_invoice(self, invoice: Invoice) -> str:
        """Create new invoice, returns invoice ID"""
        pass
    
    @abstractmethod
    def get_contractors(self) -> List[Contractor]:
        """Get contractors/clients list"""
        pass
    
    def close(self):
        if self._client:
            self._client.close()
            self._client = None


# ============================================================
# iFIRMA INTEGRATION
# ============================================================

class IFirmaClient(PolishAccountingClient):
    """
    iFirma API Client
    
    Documentation: https://www.ifirma.pl/api
    
    Authentication: HMAC-SHA1 signature
    """
    
    BASE_URL = "https://www.ifirma.pl/iapi"
    
    def __init__(self, api_key: str, username: str, key_name: str = "faktura"):
        super().__init__()
        self.api_key = api_key
        self.username = username
        self.key_name = key_name  # faktura, abonent, wydatek
    
    def _sign_request(self, url: str, content: str = "") -> Dict[str, str]:
        """Generate HMAC-SHA1 signature for request"""
        message = f"{url}{self.username}{self.key_name}{content}"
        
        signature = hmac.new(
            self.api_key.encode('utf-8'),
            message.encode('utf-8'),
            hashlib.sha1
        ).hexdigest()
        
        return {
            "Authentication": f"IAPIS user={self.username}, hmac-sha1={signature}"
        }
    
    def authenticate(self) -> bool:
        """Test authentication"""
        try:
            self.get_invoices(
                date_from=date.today(),
                date_to=date.today()
            )
            return True
        except Exception:
            return False
    
    def get_invoices(
        self, 
        date_from: date = None, 
        date_to: date = None,
        invoice_type: str = "faktury"
    ) -> List[Invoice]:
        """
        Get invoices from iFirma
        
        Types: faktury, proforma, rachunki
        """
        url = f"{self.BASE_URL}/{invoice_type}.json"
        
        params = {}
        if date_from:
            params["dataOd"] = date_from.strftime("%Y-%m-%d")
        if date_to:
            params["dataDo"] = date_to.strftime("%Y-%m-%d")
        
        headers = self._sign_request(url)
        
        response = self._get_client().get(url, params=params, headers=headers)
        response.raise_for_status()
        
        data = response.json()
        
        return [self._parse_invoice(inv) for inv in data.get("response", {}).get("Rachunki", [])]
    
    def get_invoice(self, invoice_id: str) -> Invoice:
        """Get single invoice"""
        url = f"{self.BASE_URL}/fakturakraj/{invoice_id}.json"
        headers = self._sign_request(url)
        
        response = self._get_client().get(url, headers=headers)
        response.raise_for_status()
        
        return self._parse_invoice(response.json().get("response", {}))
    
    def create_invoice(self, invoice: Invoice) -> str:
        """Create new invoice in iFirma"""
        url = f"{self.BASE_URL}/fakturakraj.json"
        
        payload = {
            "Zapizdok": True,
            "LiczOd": "BRT",
            "DataWystawienia": invoice.issue_date.strftime("%Y-%m-%d"),
            "DataSprzedazy": invoice.sale_date.strftime("%Y-%m-%d"),
            "TerminPlatnosci": invoice.due_date.strftime("%Y-%m-%d"),
            "SposowZaplaty": "PRZ",
            "NumerKontaBankowego": "",
            "Kontrahent": {
                "Nazwa": invoice.buyer_name,
                "NIP": invoice.buyer_nip or "",
                "Ulica": invoice.buyer_address,
                "KodPocztowy": "",
                "Miejscowosc": "",
                "Kraj": "PL"
            },
            "Pozycje": [
                {
                    "NazwaPelna": item.get("name", ""),
                    "Ilosc": item.get("quantity", 1),
                    "JednMiary": item.get("unit", "szt"),
                    "CenaJednostkowa": float(item.get("unit_price", 0)),
                    "StawkaVat": item.get("vat_rate", 0.23)
                }
                for item in invoice.items
            ]
        }
        
        content = json.dumps(payload)
        headers = self._sign_request(url, content)
        headers["Content-Type"] = "application/json"
        
        response = self._get_client().post(url, content=content, headers=headers)
        response.raise_for_status()
        
        result = response.json()
        return result.get("response", {}).get("Identyfikator", "")
    
    def get_contractors(self) -> List[Contractor]:
        """Get contractors list"""
        url = f"{self.BASE_URL}/kontrahenci.json"
        headers = self._sign_request(url)
        
        response = self._get_client().get(url, headers=headers)
        response.raise_for_status()
        
        data = response.json()
        
        return [
            Contractor(
                id=str(k.get("Id", "")),
                name=k.get("Nazwa", ""),
                nip=k.get("NIP"),
                address=k.get("Ulica", ""),
                city=k.get("Miejscowosc", ""),
                postal_code=k.get("KodPocztowy", ""),
                country=k.get("Kraj", "PL")
            )
            for k in data.get("response", {}).get("Kontrahenci", [])
        ]
    
    def get_expenses(self, date_from: date = None, date_to: date = None) -> List[Dict]:
        """Get expenses (wydatki)"""
        url = f"{self.BASE_URL}/wydatki.json"
        
        params = {}
        if date_from:
            params["dataOd"] = date_from.strftime("%Y-%m-%d")
        if date_to:
            params["dataDo"] = date_to.strftime("%Y-%m-%d")
        
        # Use wydatek key for expenses
        old_key = self.key_name
        self.key_name = "wydatek"
        headers = self._sign_request(url)
        self.key_name = old_key
        
        response = self._get_client().get(url, params=params, headers=headers)
        response.raise_for_status()
        
        return response.json().get("response", {}).get("Wydatki", [])
    
    def _parse_invoice(self, data: Dict) -> Invoice:
        """Parse iFirma invoice response to Invoice model"""
        return Invoice(
            id=str(data.get("Id", "")),
            number=data.get("NumerPelny", ""),
            issue_date=datetime.strptime(data.get("DataWystawienia", "2024-01-01"), "%Y-%m-%d").date(),
            sale_date=datetime.strptime(data.get("DataSprzedazy", "2024-01-01"), "%Y-%m-%d").date(),
            due_date=datetime.strptime(data.get("TerminPlatnosci", "2024-01-01"), "%Y-%m-%d").date(),
            buyer_name=data.get("Kontrahent", {}).get("Nazwa", ""),
            buyer_nip=data.get("Kontrahent", {}).get("NIP"),
            buyer_address=data.get("Kontrahent", {}).get("Ulica", ""),
            seller_name="",  # Would come from config
            seller_nip="",
            net_amount=Decimal(str(data.get("Netto", 0))),
            vat_amount=Decimal(str(data.get("Vat", 0))),
            gross_amount=Decimal(str(data.get("Brutto", 0))),
            currency=data.get("Waluta", "PLN"),
            source_system="ifirma",
            raw_data=data
        )


# ============================================================
# FAKTUROWNIA INTEGRATION
# ============================================================

class FakturowniaClient(PolishAccountingClient):
    """
    Fakturownia API Client
    
    Documentation: https://app.fakturownia.pl/api
    
    Authentication: API token in URL
    """
    
    def __init__(self, api_token: str, account_prefix: str):
        super().__init__()
        self.api_token = api_token
        self.account_prefix = account_prefix
        self.base_url = f"https://{account_prefix}.fakturownia.pl"
    
    def authenticate(self) -> bool:
        """Test authentication"""
        try:
            self.get_invoices()
            return True
        except Exception:
            return False
    
    def get_invoices(
        self, 
        date_from: date = None, 
        date_to: date = None,
        page: int = 1,
        per_page: int = 25
    ) -> List[Invoice]:
        """Get invoices from Fakturownia"""
        url = f"{self.base_url}/invoices.json"
        
        params = {
            "api_token": self.api_token,
            "page": page,
            "per_page": per_page
        }
        
        if date_from:
            params["date_from"] = date_from.strftime("%Y-%m-%d")
        if date_to:
            params["date_to"] = date_to.strftime("%Y-%m-%d")
        
        response = self._get_client().get(url, params=params)
        response.raise_for_status()
        
        return [self._parse_invoice(inv) for inv in response.json()]
    
    def get_invoice(self, invoice_id: str) -> Invoice:
        """Get single invoice"""
        url = f"{self.base_url}/invoices/{invoice_id}.json"
        params = {"api_token": self.api_token}
        
        response = self._get_client().get(url, params=params)
        response.raise_for_status()
        
        return self._parse_invoice(response.json())
    
    def create_invoice(self, invoice: Invoice) -> str:
        """Create new invoice in Fakturownia"""
        url = f"{self.base_url}/invoices.json"
        
        payload = {
            "api_token": self.api_token,
            "invoice": {
                "kind": "vat",
                "number": None,  # Auto-generated
                "sell_date": invoice.sale_date.strftime("%Y-%m-%d"),
                "issue_date": invoice.issue_date.strftime("%Y-%m-%d"),
                "payment_to": invoice.due_date.strftime("%Y-%m-%d"),
                "buyer_name": invoice.buyer_name,
                "buyer_tax_no": invoice.buyer_nip or "",
                "buyer_street": invoice.buyer_address,
                "positions": [
                    {
                        "name": item.get("name", ""),
                        "quantity": item.get("quantity", 1),
                        "unit_net_price": float(item.get("unit_price", 0)),
                        "tax": item.get("vat_rate", 23)
                    }
                    for item in invoice.items
                ]
            }
        }
        
        response = self._get_client().post(url, json=payload)
        response.raise_for_status()
        
        return str(response.json().get("id", ""))
    
    def get_contractors(self) -> List[Contractor]:
        """Get clients from Fakturownia"""
        url = f"{self.base_url}/clients.json"
        params = {"api_token": self.api_token}
        
        response = self._get_client().get(url, params=params)
        response.raise_for_status()
        
        return [
            Contractor(
                id=str(c.get("id", "")),
                name=c.get("name", ""),
                nip=c.get("tax_no"),
                address=c.get("street", ""),
                city=c.get("city", ""),
                postal_code=c.get("post_code", ""),
                country=c.get("country", "PL"),
                email=c.get("email"),
                phone=c.get("phone")
            )
            for c in response.json()
        ]
    
    def get_products(self) -> List[Dict]:
        """Get products list"""
        url = f"{self.base_url}/products.json"
        params = {"api_token": self.api_token}
        
        response = self._get_client().get(url, params=params)
        response.raise_for_status()
        
        return response.json()
    
    def get_warehouses(self) -> List[Dict]:
        """Get warehouses"""
        url = f"{self.base_url}/warehouses.json"
        params = {"api_token": self.api_token}
        
        response = self._get_client().get(url, params=params)
        response.raise_for_status()
        
        return response.json()
    
    def _parse_invoice(self, data: Dict) -> Invoice:
        """Parse Fakturownia invoice to Invoice model"""
        return Invoice(
            id=str(data.get("id", "")),
            number=data.get("number", ""),
            issue_date=datetime.strptime(data.get("issue_date", "2024-01-01"), "%Y-%m-%d").date(),
            sale_date=datetime.strptime(data.get("sell_date", "2024-01-01"), "%Y-%m-%d").date(),
            due_date=datetime.strptime(data.get("payment_to", "2024-01-01"), "%Y-%m-%d").date(),
            buyer_name=data.get("buyer_name", ""),
            buyer_nip=data.get("buyer_tax_no"),
            buyer_address=data.get("buyer_street", ""),
            seller_name=data.get("seller_name", ""),
            seller_nip=data.get("seller_tax_no", ""),
            net_amount=Decimal(str(data.get("price_net", 0))),
            vat_amount=Decimal(str(data.get("price_tax", 0))),
            gross_amount=Decimal(str(data.get("price_gross", 0))),
            currency=data.get("currency", "PLN"),
            payment_status=self._parse_payment_status(data.get("status", "")),
            source_system="fakturownia",
            raw_data=data
        )
    
    def _parse_payment_status(self, status: str) -> PaymentStatus:
        """Parse payment status"""
        status_map = {
            "paid": PaymentStatus.PAID,
            "unpaid": PaymentStatus.UNPAID,
            "partial": PaymentStatus.PARTIAL
        }
        return status_map.get(status.lower(), PaymentStatus.UNPAID)


# ============================================================
# inFakt INTEGRATION
# ============================================================

class InFaktClient(PolishAccountingClient):
    """
    inFakt API Client
    
    Documentation: https://www.infakt.pl/developers/
    
    Authentication: API key in header
    """
    
    BASE_URL = "https://api.infakt.pl/v3"
    
    def __init__(self, api_key: str):
        super().__init__()
        self.api_key = api_key
    
    def _get_headers(self) -> Dict[str, str]:
        return {
            "X-inFakt-ApiKey": self.api_key,
            "Content-Type": "application/json"
        }
    
    def authenticate(self) -> bool:
        """Test authentication"""
        try:
            url = f"{self.BASE_URL}/invoices.json"
            response = self._get_client().get(url, headers=self._get_headers())
            return response.status_code == 200
        except Exception:
            return False
    
    def get_invoices(
        self, 
        date_from: date = None, 
        date_to: date = None,
        page: int = 1
    ) -> List[Invoice]:
        """Get invoices from inFakt"""
        url = f"{self.BASE_URL}/invoices.json"
        
        params = {"page": page}
        if date_from:
            params["q[invoice_date_gteq]"] = date_from.strftime("%Y-%m-%d")
        if date_to:
            params["q[invoice_date_lteq]"] = date_to.strftime("%Y-%m-%d")
        
        response = self._get_client().get(url, params=params, headers=self._get_headers())
        response.raise_for_status()
        
        return [self._parse_invoice(inv) for inv in response.json()]
    
    def get_invoice(self, invoice_id: str) -> Invoice:
        """Get single invoice"""
        url = f"{self.BASE_URL}/invoices/{invoice_id}.json"
        
        response = self._get_client().get(url, headers=self._get_headers())
        response.raise_for_status()
        
        return self._parse_invoice(response.json())
    
    def create_invoice(self, invoice: Invoice) -> str:
        """Create new invoice in inFakt"""
        url = f"{self.BASE_URL}/invoices.json"
        
        payload = {
            "invoice": {
                "client_id": None,  # Would need to be resolved
                "invoice_date": invoice.issue_date.strftime("%Y-%m-%d"),
                "sale_date": invoice.sale_date.strftime("%Y-%m-%d"),
                "payment_date": invoice.due_date.strftime("%Y-%m-%d"),
                "services": [
                    {
                        "name": item.get("name", ""),
                        "quantity": item.get("quantity", 1),
                        "unit_net_price": float(item.get("unit_price", 0)),
                        "tax_symbol": str(int(item.get("vat_rate", 0.23) * 100))
                    }
                    for item in invoice.items
                ]
            }
        }
        
        response = self._get_client().post(url, json=payload, headers=self._get_headers())
        response.raise_for_status()
        
        return str(response.json().get("id", ""))
    
    def get_contractors(self) -> List[Contractor]:
        """Get clients from inFakt"""
        url = f"{self.BASE_URL}/clients.json"
        
        response = self._get_client().get(url, headers=self._get_headers())
        response.raise_for_status()
        
        return [
            Contractor(
                id=str(c.get("id", "")),
                name=c.get("name", ""),
                nip=c.get("nip"),
                address=c.get("street", ""),
                city=c.get("city", ""),
                postal_code=c.get("postal_code", ""),
                country=c.get("country", "PL"),
                email=c.get("email"),
                phone=c.get("phone_number")
            )
            for c in response.json()
        ]
    
    def get_bank_accounts(self) -> List[BankAccount]:
        """Get bank accounts"""
        url = f"{self.BASE_URL}/bank_accounts.json"
        
        response = self._get_client().get(url, headers=self._get_headers())
        response.raise_for_status()
        
        return [
            BankAccount(
                account_number=acc.get("bank_account", ""),
                bank_name=acc.get("bank_name", ""),
                currency="PLN"
            )
            for acc in response.json()
        ]
    
    def _parse_invoice(self, data: Dict) -> Invoice:
        """Parse inFakt invoice to Invoice model"""
        return Invoice(
            id=str(data.get("id", "")),
            number=data.get("number", ""),
            issue_date=datetime.strptime(data.get("invoice_date", "2024-01-01"), "%Y-%m-%d").date(),
            sale_date=datetime.strptime(data.get("sale_date", "2024-01-01"), "%Y-%m-%d").date(),
            due_date=datetime.strptime(data.get("payment_date", "2024-01-01"), "%Y-%m-%d").date(),
            buyer_name=data.get("client", {}).get("name", ""),
            buyer_nip=data.get("client", {}).get("nip"),
            buyer_address=data.get("client", {}).get("street", ""),
            seller_name="",
            seller_nip="",
            net_amount=Decimal(str(data.get("net_price", 0))),
            vat_amount=Decimal(str(data.get("tax_price", 0))),
            gross_amount=Decimal(str(data.get("gross_price", 0))),
            currency=data.get("currency", "PLN"),
            source_system="infakt",
            raw_data=data
        )


# ============================================================
# FACTORY & HELPERS
# ============================================================

def create_polish_client(
    system: str,
    credentials: Dict[str, str]
) -> PolishAccountingClient:
    """
    Factory function to create Polish accounting client
    
    Args:
        system: ifirma, fakturownia, infakt, wfirma
        credentials: System-specific credentials
    
    Returns:
        Configured client instance
    """
    clients = {
        "ifirma": lambda: IFirmaClient(
            api_key=credentials["api_key"],
            username=credentials["username"],
            key_name=credentials.get("key_name", "faktura")
        ),
        "fakturownia": lambda: FakturowniaClient(
            api_token=credentials["api_token"],
            account_prefix=credentials["account_prefix"]
        ),
        "infakt": lambda: InFaktClient(
            api_key=credentials["api_key"]
        )
    }
    
    if system.lower() not in clients:
        raise ValueError(f"Unknown system: {system}. Supported: {list(clients.keys())}")
    
    return clients[system.lower()]()


__all__ = [
    'Invoice',
    'InvoiceType',
    'PaymentStatus',
    'Contractor',
    'BankAccount',
    'PolishAccountingClient',
    'IFirmaClient',
    'FakturowniaClient',
    'InFaktClient',
    'create_polish_client'
]
