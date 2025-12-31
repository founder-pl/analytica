"""
ANALYTICA Integrations - ERP Systems
=====================================

Enterprise Resource Planning system integrations:
- SAP Business One / S/4HANA
- Comarch ERP Optima / XL
- Sage Symfonia / 50
- Insert GT / Nexo
- Enova365
"""

from typing import Any, Dict, List, Optional, Union
from dataclasses import dataclass, field
from datetime import datetime, date
from decimal import Decimal
from abc import ABC, abstractmethod
from enum import Enum
import json
import base64
import hashlib
import xml.etree.ElementTree as ET

import httpx


# ============================================================
# DATA MODELS
# ============================================================

class DocumentType(Enum):
    """ERP document types"""
    INVOICE_SALES = "invoice_sales"
    INVOICE_PURCHASE = "invoice_purchase"
    ORDER_SALES = "order_sales"
    ORDER_PURCHASE = "order_purchase"
    DELIVERY = "delivery"
    RECEIPT = "receipt"
    PAYMENT = "payment"
    JOURNAL = "journal"


@dataclass
class ERPDocument:
    """Universal ERP document model"""
    id: str
    document_type: DocumentType
    number: str
    date: date
    due_date: Optional[date]
    partner_id: str
    partner_name: str
    net_amount: Decimal
    vat_amount: Decimal
    gross_amount: Decimal
    currency: str = "PLN"
    status: str = "draft"
    lines: List[Dict] = field(default_factory=list)
    metadata: Dict = field(default_factory=dict)
    source_system: str = ""


@dataclass
class ERPPartner:
    """Business partner / contractor"""
    id: str
    code: str
    name: str
    nip: Optional[str]
    address: str
    city: str
    postal_code: str
    country: str = "PL"
    email: Optional[str] = None
    phone: Optional[str] = None
    partner_type: str = "customer"  # customer, supplier, both


@dataclass
class ERPProduct:
    """Product / service item"""
    id: str
    code: str
    name: str
    unit: str
    net_price: Decimal
    vat_rate: Decimal
    category: Optional[str] = None
    stock_quantity: Optional[Decimal] = None


@dataclass
class ERPAccount:
    """Chart of accounts entry"""
    id: str
    code: str
    name: str
    account_type: str  # asset, liability, equity, income, expense
    parent_code: Optional[str] = None
    balance: Decimal = Decimal("0")


# ============================================================
# BASE ERP CLIENT
# ============================================================

class ERPClient(ABC):
    """Base class for ERP clients"""
    
    def __init__(self, timeout: float = 60.0):
        self.timeout = timeout
        self._client: Optional[httpx.Client] = None
    
    def _get_client(self) -> httpx.Client:
        if self._client is None:
            self._client = httpx.Client(timeout=self.timeout)
        return self._client
    
    @abstractmethod
    def authenticate(self) -> bool:
        """Authenticate with ERP system"""
        pass
    
    @abstractmethod
    def get_documents(
        self, 
        doc_type: DocumentType,
        date_from: date = None,
        date_to: date = None
    ) -> List[ERPDocument]:
        """Get documents from ERP"""
        pass
    
    @abstractmethod
    def get_partners(self) -> List[ERPPartner]:
        """Get business partners"""
        pass
    
    @abstractmethod
    def get_products(self) -> List[ERPProduct]:
        """Get products / services"""
        pass
    
    @abstractmethod
    def create_document(self, document: ERPDocument) -> str:
        """Create document in ERP, returns document ID"""
        pass
    
    def close(self):
        if self._client:
            self._client.close()
            self._client = None


# ============================================================
# SAP BUSINESS ONE INTEGRATION
# ============================================================

class SAPBusinessOneClient(ERPClient):
    """
    SAP Business One Service Layer API Client
    
    Documentation: https://help.sap.com/docs/SAP_BUSINESS_ONE
    
    Authentication: Session-based with username/password
    """
    
    def __init__(
        self,
        server_url: str,
        company_db: str,
        username: str,
        password: str
    ):
        super().__init__()
        self.server_url = server_url.rstrip('/')
        self.company_db = company_db
        self.username = username
        self.password = password
        self.session_id: Optional[str] = None
    
    def authenticate(self) -> bool:
        """Login to SAP B1 Service Layer"""
        try:
            response = self._get_client().post(
                f"{self.server_url}/b1s/v1/Login",
                json={
                    "CompanyDB": self.company_db,
                    "UserName": self.username,
                    "Password": self.password
                },
                headers={"Content-Type": "application/json"}
            )
            response.raise_for_status()
            
            # Session ID is in cookies
            self.session_id = response.cookies.get("B1SESSION")
            return True
        except Exception:
            return False
    
    def _auth_headers(self) -> Dict[str, str]:
        return {
            "Cookie": f"B1SESSION={self.session_id}",
            "Content-Type": "application/json"
        }
    
    def get_documents(
        self, 
        doc_type: DocumentType,
        date_from: date = None,
        date_to: date = None
    ) -> List[ERPDocument]:
        """Get documents from SAP B1"""
        # Map document types to SAP endpoints
        endpoint_map = {
            DocumentType.INVOICE_SALES: "Invoices",
            DocumentType.INVOICE_PURCHASE: "PurchaseInvoices",
            DocumentType.ORDER_SALES: "Orders",
            DocumentType.ORDER_PURCHASE: "PurchaseOrders",
            DocumentType.DELIVERY: "DeliveryNotes",
        }
        
        endpoint = endpoint_map.get(doc_type)
        if not endpoint:
            return []
        
        # Build filter
        filters = []
        if date_from:
            filters.append(f"DocDate ge '{date_from.isoformat()}'")
        if date_to:
            filters.append(f"DocDate le '{date_to.isoformat()}'")
        
        url = f"{self.server_url}/b1s/v1/{endpoint}"
        if filters:
            url += f"?$filter={' and '.join(filters)}"
        
        response = self._get_client().get(url, headers=self._auth_headers())
        response.raise_for_status()
        
        documents = []
        for item in response.json().get("value", []):
            documents.append(self._parse_sap_document(item, doc_type))
        
        return documents
    
    def get_partners(self) -> List[ERPPartner]:
        """Get business partners from SAP B1"""
        response = self._get_client().get(
            f"{self.server_url}/b1s/v1/BusinessPartners",
            headers=self._auth_headers()
        )
        response.raise_for_status()
        
        partners = []
        for bp in response.json().get("value", []):
            partners.append(ERPPartner(
                id=bp.get("CardCode", ""),
                code=bp.get("CardCode", ""),
                name=bp.get("CardName", ""),
                nip=bp.get("FederalTaxID"),
                address=bp.get("Address", ""),
                city=bp.get("City", ""),
                postal_code=bp.get("ZipCode", ""),
                country=bp.get("Country", "PL"),
                email=bp.get("EmailAddress"),
                phone=bp.get("Phone1"),
                partner_type="customer" if bp.get("CardType") == "cCustomer" else "supplier"
            ))
        
        return partners
    
    def get_products(self) -> List[ERPProduct]:
        """Get items from SAP B1"""
        response = self._get_client().get(
            f"{self.server_url}/b1s/v1/Items",
            headers=self._auth_headers()
        )
        response.raise_for_status()
        
        products = []
        for item in response.json().get("value", []):
            products.append(ERPProduct(
                id=item.get("ItemCode", ""),
                code=item.get("ItemCode", ""),
                name=item.get("ItemName", ""),
                unit=item.get("InventoryUOM", "szt"),
                net_price=Decimal(str(item.get("AvgStdPrice", 0))),
                vat_rate=Decimal("0.23"),
                stock_quantity=Decimal(str(item.get("QuantityOnStock", 0)))
            ))
        
        return products
    
    def create_document(self, document: ERPDocument) -> str:
        """Create document in SAP B1"""
        endpoint_map = {
            DocumentType.INVOICE_SALES: "Invoices",
            DocumentType.ORDER_SALES: "Orders",
        }
        
        endpoint = endpoint_map.get(document.document_type)
        if not endpoint:
            raise ValueError(f"Unsupported document type: {document.document_type}")
        
        payload = {
            "CardCode": document.partner_id,
            "DocDate": document.date.isoformat(),
            "DocDueDate": document.due_date.isoformat() if document.due_date else None,
            "DocumentLines": [
                {
                    "ItemCode": line.get("item_code"),
                    "Quantity": line.get("quantity"),
                    "UnitPrice": float(line.get("unit_price", 0))
                }
                for line in document.lines
            ]
        }
        
        response = self._get_client().post(
            f"{self.server_url}/b1s/v1/{endpoint}",
            json=payload,
            headers=self._auth_headers()
        )
        response.raise_for_status()
        
        return str(response.json().get("DocEntry", ""))
    
    def _parse_sap_document(self, data: Dict, doc_type: DocumentType) -> ERPDocument:
        """Parse SAP B1 document to ERPDocument"""
        return ERPDocument(
            id=str(data.get("DocEntry", "")),
            document_type=doc_type,
            number=str(data.get("DocNum", "")),
            date=datetime.strptime(data.get("DocDate", "2024-01-01"), "%Y-%m-%d").date(),
            due_date=datetime.strptime(data.get("DocDueDate", "2024-01-01"), "%Y-%m-%d").date() if data.get("DocDueDate") else None,
            partner_id=data.get("CardCode", ""),
            partner_name=data.get("CardName", ""),
            net_amount=Decimal(str(data.get("DocTotal", 0))) - Decimal(str(data.get("VatSum", 0))),
            vat_amount=Decimal(str(data.get("VatSum", 0))),
            gross_amount=Decimal(str(data.get("DocTotal", 0))),
            currency=data.get("DocCurrency", "PLN"),
            source_system="sap_b1"
        )


# ============================================================
# COMARCH ERP OPTIMA INTEGRATION
# ============================================================

class ComarchOptimaClient(ERPClient):
    """
    Comarch ERP Optima API Client
    
    Uses SOAP/XML API for older versions or REST API for newer
    """
    
    def __init__(
        self,
        server_url: str,
        api_key: str,
        company_id: str
    ):
        super().__init__()
        self.server_url = server_url.rstrip('/')
        self.api_key = api_key
        self.company_id = company_id
    
    def _auth_headers(self) -> Dict[str, str]:
        return {
            "Authorization": f"Bearer {self.api_key}",
            "X-Company-ID": self.company_id,
            "Content-Type": "application/json"
        }
    
    def authenticate(self) -> bool:
        """Test authentication"""
        try:
            response = self._get_client().get(
                f"{self.server_url}/api/v1/info",
                headers=self._auth_headers()
            )
            return response.status_code == 200
        except Exception:
            return False
    
    def get_documents(
        self, 
        doc_type: DocumentType,
        date_from: date = None,
        date_to: date = None
    ) -> List[ERPDocument]:
        """Get documents from Comarch Optima"""
        endpoint_map = {
            DocumentType.INVOICE_SALES: "faktury/sprzedaz",
            DocumentType.INVOICE_PURCHASE: "faktury/zakup",
            DocumentType.ORDER_SALES: "zamowienia/sprzedaz",
        }
        
        endpoint = endpoint_map.get(doc_type, "dokumenty")
        
        params = {}
        if date_from:
            params["dataOd"] = date_from.isoformat()
        if date_to:
            params["dataDo"] = date_to.isoformat()
        
        response = self._get_client().get(
            f"{self.server_url}/api/v1/{endpoint}",
            params=params,
            headers=self._auth_headers()
        )
        response.raise_for_status()
        
        documents = []
        for item in response.json().get("items", []):
            documents.append(self._parse_optima_document(item, doc_type))
        
        return documents
    
    def get_partners(self) -> List[ERPPartner]:
        """Get contractors from Comarch Optima"""
        response = self._get_client().get(
            f"{self.server_url}/api/v1/kontrahenci",
            headers=self._auth_headers()
        )
        response.raise_for_status()
        
        partners = []
        for k in response.json().get("items", []):
            partners.append(ERPPartner(
                id=str(k.get("id", "")),
                code=k.get("kod", ""),
                name=k.get("nazwa", ""),
                nip=k.get("nip"),
                address=k.get("ulica", ""),
                city=k.get("miasto", ""),
                postal_code=k.get("kodPocztowy", ""),
                email=k.get("email"),
                phone=k.get("telefon")
            ))
        
        return partners
    
    def get_products(self) -> List[ERPProduct]:
        """Get products from Comarch Optima"""
        response = self._get_client().get(
            f"{self.server_url}/api/v1/towary",
            headers=self._auth_headers()
        )
        response.raise_for_status()
        
        products = []
        for t in response.json().get("items", []):
            products.append(ERPProduct(
                id=str(t.get("id", "")),
                code=t.get("kod", ""),
                name=t.get("nazwa", ""),
                unit=t.get("jednostka", "szt"),
                net_price=Decimal(str(t.get("cenaNetto", 0))),
                vat_rate=Decimal(str(t.get("stawkaVat", 23))) / 100,
                stock_quantity=Decimal(str(t.get("stanMagazynowy", 0)))
            ))
        
        return products
    
    def create_document(self, document: ERPDocument) -> str:
        """Create document in Comarch Optima"""
        payload = {
            "kontrahentId": document.partner_id,
            "dataWystawienia": document.date.isoformat(),
            "dataSprzedazy": document.date.isoformat(),
            "terminPlatnosci": document.due_date.isoformat() if document.due_date else None,
            "pozycje": [
                {
                    "towarId": line.get("product_id"),
                    "ilosc": line.get("quantity"),
                    "cenaNetto": float(line.get("unit_price", 0))
                }
                for line in document.lines
            ]
        }
        
        response = self._get_client().post(
            f"{self.server_url}/api/v1/faktury/sprzedaz",
            json=payload,
            headers=self._auth_headers()
        )
        response.raise_for_status()
        
        return str(response.json().get("id", ""))
    
    def _parse_optima_document(self, data: Dict, doc_type: DocumentType) -> ERPDocument:
        """Parse Comarch Optima document"""
        return ERPDocument(
            id=str(data.get("id", "")),
            document_type=doc_type,
            number=data.get("numer", ""),
            date=datetime.strptime(data.get("dataWystawienia", "2024-01-01"), "%Y-%m-%d").date(),
            due_date=datetime.strptime(data.get("terminPlatnosci", "2024-01-01"), "%Y-%m-%d").date() if data.get("terminPlatnosci") else None,
            partner_id=str(data.get("kontrahentId", "")),
            partner_name=data.get("kontrahentNazwa", ""),
            net_amount=Decimal(str(data.get("wartoscNetto", 0))),
            vat_amount=Decimal(str(data.get("wartoscVat", 0))),
            gross_amount=Decimal(str(data.get("wartoscBrutto", 0))),
            source_system="comarch_optima"
        )


# ============================================================
# SAGE SYMFONIA INTEGRATION
# ============================================================

class SageSymphoniaClient(ERPClient):
    """
    Sage Symfonia API Client
    
    Uses REST API for modern versions
    """
    
    def __init__(
        self,
        server_url: str,
        client_id: str,
        client_secret: str
    ):
        super().__init__()
        self.server_url = server_url.rstrip('/')
        self.client_id = client_id
        self.client_secret = client_secret
        self.access_token: Optional[str] = None
    
    def authenticate(self) -> bool:
        """Get OAuth2 token"""
        try:
            response = self._get_client().post(
                f"{self.server_url}/oauth/token",
                data={
                    "grant_type": "client_credentials",
                    "client_id": self.client_id,
                    "client_secret": self.client_secret
                }
            )
            response.raise_for_status()
            
            self.access_token = response.json().get("access_token")
            return True
        except Exception:
            return False
    
    def _auth_headers(self) -> Dict[str, str]:
        return {
            "Authorization": f"Bearer {self.access_token}",
            "Content-Type": "application/json"
        }
    
    def get_documents(
        self, 
        doc_type: DocumentType,
        date_from: date = None,
        date_to: date = None
    ) -> List[ERPDocument]:
        """Get documents from Sage Symfonia"""
        endpoint_map = {
            DocumentType.INVOICE_SALES: "invoices/sales",
            DocumentType.INVOICE_PURCHASE: "invoices/purchase",
        }
        
        endpoint = endpoint_map.get(doc_type, "documents")
        
        params = {}
        if date_from:
            params["dateFrom"] = date_from.isoformat()
        if date_to:
            params["dateTo"] = date_to.isoformat()
        
        response = self._get_client().get(
            f"{self.server_url}/api/v1/{endpoint}",
            params=params,
            headers=self._auth_headers()
        )
        response.raise_for_status()
        
        return [self._parse_sage_document(d, doc_type) for d in response.json().get("data", [])]
    
    def get_partners(self) -> List[ERPPartner]:
        """Get partners from Sage Symfonia"""
        response = self._get_client().get(
            f"{self.server_url}/api/v1/partners",
            headers=self._auth_headers()
        )
        response.raise_for_status()
        
        return [
            ERPPartner(
                id=str(p.get("id", "")),
                code=p.get("code", ""),
                name=p.get("name", ""),
                nip=p.get("taxId"),
                address=p.get("street", ""),
                city=p.get("city", ""),
                postal_code=p.get("postalCode", ""),
                email=p.get("email"),
                phone=p.get("phone")
            )
            for p in response.json().get("data", [])
        ]
    
    def get_products(self) -> List[ERPProduct]:
        """Get products from Sage Symfonia"""
        response = self._get_client().get(
            f"{self.server_url}/api/v1/products",
            headers=self._auth_headers()
        )
        response.raise_for_status()
        
        return [
            ERPProduct(
                id=str(p.get("id", "")),
                code=p.get("code", ""),
                name=p.get("name", ""),
                unit=p.get("unit", "szt"),
                net_price=Decimal(str(p.get("netPrice", 0))),
                vat_rate=Decimal(str(p.get("vatRate", 23))) / 100
            )
            for p in response.json().get("data", [])
        ]
    
    def create_document(self, document: ERPDocument) -> str:
        """Create document in Sage Symfonia"""
        payload = {
            "partnerId": document.partner_id,
            "date": document.date.isoformat(),
            "dueDate": document.due_date.isoformat() if document.due_date else None,
            "lines": document.lines
        }
        
        response = self._get_client().post(
            f"{self.server_url}/api/v1/invoices/sales",
            json=payload,
            headers=self._auth_headers()
        )
        response.raise_for_status()
        
        return str(response.json().get("id", ""))
    
    def _parse_sage_document(self, data: Dict, doc_type: DocumentType) -> ERPDocument:
        """Parse Sage Symfonia document"""
        return ERPDocument(
            id=str(data.get("id", "")),
            document_type=doc_type,
            number=data.get("number", ""),
            date=datetime.strptime(data.get("date", "2024-01-01"), "%Y-%m-%d").date(),
            due_date=datetime.strptime(data.get("dueDate", "2024-01-01"), "%Y-%m-%d").date() if data.get("dueDate") else None,
            partner_id=str(data.get("partnerId", "")),
            partner_name=data.get("partnerName", ""),
            net_amount=Decimal(str(data.get("netAmount", 0))),
            vat_amount=Decimal(str(data.get("vatAmount", 0))),
            gross_amount=Decimal(str(data.get("grossAmount", 0))),
            source_system="sage_symfonia"
        )


# ============================================================
# ENOVA365 INTEGRATION
# ============================================================

class Enova365Client(ERPClient):
    """
    Enova365 API Client
    
    Modern Polish ERP system with REST API
    """
    
    def __init__(self, server_url: str, api_key: str, tenant_id: str):
        super().__init__()
        self.server_url = server_url.rstrip('/')
        self.api_key = api_key
        self.tenant_id = tenant_id
    
    def _auth_headers(self) -> Dict[str, str]:
        return {
            "X-API-Key": self.api_key,
            "X-Tenant-ID": self.tenant_id,
            "Content-Type": "application/json"
        }
    
    def authenticate(self) -> bool:
        try:
            response = self._get_client().get(
                f"{self.server_url}/api/info",
                headers=self._auth_headers()
            )
            return response.status_code == 200
        except Exception:
            return False
    
    def get_documents(self, doc_type: DocumentType, date_from: date = None, date_to: date = None) -> List[ERPDocument]:
        params = {}
        if date_from:
            params["from"] = date_from.isoformat()
        if date_to:
            params["to"] = date_to.isoformat()
        
        response = self._get_client().get(
            f"{self.server_url}/api/documents",
            params=params,
            headers=self._auth_headers()
        )
        response.raise_for_status()
        
        return [self._parse_enova_document(d, doc_type) for d in response.json()]
    
    def get_partners(self) -> List[ERPPartner]:
        response = self._get_client().get(
            f"{self.server_url}/api/contractors",
            headers=self._auth_headers()
        )
        response.raise_for_status()
        
        return [
            ERPPartner(
                id=str(c["id"]),
                code=c.get("code", ""),
                name=c.get("name", ""),
                nip=c.get("nip"),
                address=c.get("address", ""),
                city=c.get("city", ""),
                postal_code=c.get("postalCode", "")
            )
            for c in response.json()
        ]
    
    def get_products(self) -> List[ERPProduct]:
        response = self._get_client().get(
            f"{self.server_url}/api/items",
            headers=self._auth_headers()
        )
        response.raise_for_status()
        
        return [
            ERPProduct(
                id=str(p["id"]),
                code=p.get("code", ""),
                name=p.get("name", ""),
                unit=p.get("unit", "szt"),
                net_price=Decimal(str(p.get("price", 0))),
                vat_rate=Decimal("0.23")
            )
            for p in response.json()
        ]
    
    def create_document(self, document: ERPDocument) -> str:
        response = self._get_client().post(
            f"{self.server_url}/api/documents",
            json={
                "type": document.document_type.value,
                "contractorId": document.partner_id,
                "date": document.date.isoformat(),
                "items": document.lines
            },
            headers=self._auth_headers()
        )
        response.raise_for_status()
        return str(response.json().get("id", ""))
    
    def _parse_enova_document(self, data: Dict, doc_type: DocumentType) -> ERPDocument:
        return ERPDocument(
            id=str(data.get("id", "")),
            document_type=doc_type,
            number=data.get("number", ""),
            date=datetime.strptime(data.get("date", "2024-01-01"), "%Y-%m-%d").date(),
            due_date=None,
            partner_id=str(data.get("contractorId", "")),
            partner_name=data.get("contractorName", ""),
            net_amount=Decimal(str(data.get("netValue", 0))),
            vat_amount=Decimal(str(data.get("vatValue", 0))),
            gross_amount=Decimal(str(data.get("grossValue", 0))),
            source_system="enova365"
        )


# ============================================================
# FACTORY
# ============================================================

def create_erp_client(
    system: str,
    credentials: Dict[str, str]
) -> ERPClient:
    """
    Factory function to create ERP client
    
    Supported systems: sap_b1, comarch_optima, sage_symfonia, enova365
    """
    clients = {
        "sap_b1": lambda: SAPBusinessOneClient(
            server_url=credentials["server_url"],
            company_db=credentials["company_db"],
            username=credentials["username"],
            password=credentials["password"]
        ),
        "comarch_optima": lambda: ComarchOptimaClient(
            server_url=credentials["server_url"],
            api_key=credentials["api_key"],
            company_id=credentials["company_id"]
        ),
        "sage_symfonia": lambda: SageSymphoniaClient(
            server_url=credentials["server_url"],
            client_id=credentials["client_id"],
            client_secret=credentials["client_secret"]
        ),
        "enova365": lambda: Enova365Client(
            server_url=credentials["server_url"],
            api_key=credentials["api_key"],
            tenant_id=credentials["tenant_id"]
        )
    }
    
    if system.lower() not in clients:
        raise ValueError(f"Unknown ERP system: {system}. Supported: {list(clients.keys())}")
    
    return clients[system.lower()]()


__all__ = [
    'DocumentType',
    'ERPDocument',
    'ERPPartner',
    'ERPProduct',
    'ERPAccount',
    'ERPClient',
    'SAPBusinessOneClient',
    'ComarchOptimaClient',
    'SageSymphoniaClient',
    'Enova365Client',
    'create_erp_client'
]
