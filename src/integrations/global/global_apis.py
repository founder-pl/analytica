"""
ANALYTICA Integrations - Global APIs
=====================================

International payment and accounting APIs:
- Stripe (payments)
- PayPal (payments)
- QuickBooks (accounting)
- Xero (accounting)
- Wise (transfers)
"""

from typing import Any, Dict, List, Optional
from dataclasses import dataclass, field
from datetime import datetime, date
from decimal import Decimal
from abc import ABC, abstractmethod

import httpx


# ============================================================
# DATA MODELS
# ============================================================

@dataclass
class Payment:
    """Universal payment model"""
    id: str
    amount: Decimal
    currency: str
    status: str  # pending, completed, failed, refunded
    customer_id: Optional[str] = None
    customer_email: Optional[str] = None
    description: Optional[str] = None
    created_at: Optional[datetime] = None
    metadata: Dict = field(default_factory=dict)
    source_system: str = ""


@dataclass
class Customer:
    """Customer model"""
    id: str
    email: str
    name: Optional[str] = None
    phone: Optional[str] = None
    address: Dict = field(default_factory=dict)
    metadata: Dict = field(default_factory=dict)


@dataclass
class Invoice:
    """Invoice model for accounting systems"""
    id: str
    number: str
    customer_id: str
    customer_name: str
    amount: Decimal
    currency: str
    status: str  # draft, sent, paid, overdue
    issue_date: date
    due_date: date
    line_items: List[Dict] = field(default_factory=list)
    source_system: str = ""


# ============================================================
# STRIPE INTEGRATION
# ============================================================

class StripeClient:
    """
    Stripe API Client
    
    Documentation: https://stripe.com/docs/api
    """
    
    BASE_URL = "https://api.stripe.com/v1"
    
    def __init__(self, api_key: str):
        self.api_key = api_key
        self._client = None
    
    def _get_client(self) -> httpx.Client:
        if self._client is None:
            self._client = httpx.Client(
                timeout=30.0,
                auth=(self.api_key, "")
            )
        return self._client
    
    def create_payment_intent(
        self,
        amount: int,  # Amount in cents
        currency: str = "pln",
        customer_id: str = None,
        description: str = None,
        metadata: Dict = None
    ) -> Payment:
        """Create payment intent"""
        data = {
            "amount": amount,
            "currency": currency.lower(),
        }
        
        if customer_id:
            data["customer"] = customer_id
        if description:
            data["description"] = description
        if metadata:
            for k, v in metadata.items():
                data[f"metadata[{k}]"] = v
        
        response = self._get_client().post(
            f"{self.BASE_URL}/payment_intents",
            data=data
        )
        response.raise_for_status()
        
        return self._parse_payment(response.json())
    
    def get_payment(self, payment_id: str) -> Payment:
        """Get payment by ID"""
        response = self._get_client().get(
            f"{self.BASE_URL}/payment_intents/{payment_id}"
        )
        response.raise_for_status()
        
        return self._parse_payment(response.json())
    
    def list_payments(
        self,
        limit: int = 100,
        created_after: datetime = None,
        customer_id: str = None
    ) -> List[Payment]:
        """List payments"""
        params = {"limit": min(limit, 100)}
        
        if created_after:
            params["created[gte]"] = int(created_after.timestamp())
        if customer_id:
            params["customer"] = customer_id
        
        response = self._get_client().get(
            f"{self.BASE_URL}/payment_intents",
            params=params
        )
        response.raise_for_status()
        
        return [self._parse_payment(p) for p in response.json()["data"]]
    
    def refund_payment(self, payment_id: str, amount: int = None) -> Dict:
        """Refund a payment"""
        data = {"payment_intent": payment_id}
        if amount:
            data["amount"] = amount
        
        response = self._get_client().post(
            f"{self.BASE_URL}/refunds",
            data=data
        )
        response.raise_for_status()
        
        return response.json()
    
    def create_customer(
        self,
        email: str,
        name: str = None,
        phone: str = None,
        metadata: Dict = None
    ) -> Customer:
        """Create customer"""
        data = {"email": email}
        
        if name:
            data["name"] = name
        if phone:
            data["phone"] = phone
        if metadata:
            for k, v in metadata.items():
                data[f"metadata[{k}]"] = v
        
        response = self._get_client().post(
            f"{self.BASE_URL}/customers",
            data=data
        )
        response.raise_for_status()
        
        return self._parse_customer(response.json())
    
    def get_balance(self) -> Dict[str, Decimal]:
        """Get account balance"""
        response = self._get_client().get(f"{self.BASE_URL}/balance")
        response.raise_for_status()
        
        data = response.json()
        balances = {}
        
        for item in data.get("available", []):
            balances[item["currency"]] = Decimal(str(item["amount"])) / 100
        
        return balances
    
    def _parse_payment(self, data: Dict) -> Payment:
        return Payment(
            id=data["id"],
            amount=Decimal(str(data["amount"])) / 100,
            currency=data["currency"].upper(),
            status=data["status"],
            customer_id=data.get("customer"),
            description=data.get("description"),
            created_at=datetime.fromtimestamp(data["created"]),
            metadata=data.get("metadata", {}),
            source_system="stripe"
        )
    
    def _parse_customer(self, data: Dict) -> Customer:
        return Customer(
            id=data["id"],
            email=data.get("email", ""),
            name=data.get("name"),
            phone=data.get("phone"),
            metadata=data.get("metadata", {})
        )
    
    def close(self):
        if self._client:
            self._client.close()
            self._client = None


# ============================================================
# PAYPAL INTEGRATION
# ============================================================

class PayPalClient:
    """
    PayPal REST API Client
    
    Documentation: https://developer.paypal.com/docs/api/overview/
    """
    
    SANDBOX_URL = "https://api-m.sandbox.paypal.com"
    LIVE_URL = "https://api-m.paypal.com"
    
    def __init__(
        self,
        client_id: str,
        client_secret: str,
        sandbox: bool = True
    ):
        self.client_id = client_id
        self.client_secret = client_secret
        self.base_url = self.SANDBOX_URL if sandbox else self.LIVE_URL
        self.access_token: Optional[str] = None
        self._client = None
    
    def _get_client(self) -> httpx.Client:
        if self._client is None:
            self._client = httpx.Client(timeout=30.0)
        return self._client
    
    def authenticate(self) -> bool:
        """Get OAuth2 access token"""
        try:
            response = self._get_client().post(
                f"{self.base_url}/v1/oauth2/token",
                auth=(self.client_id, self.client_secret),
                data={"grant_type": "client_credentials"}
            )
            response.raise_for_status()
            
            self.access_token = response.json()["access_token"]
            return True
        except Exception:
            return False
    
    def _auth_headers(self) -> Dict[str, str]:
        return {
            "Authorization": f"Bearer {self.access_token}",
            "Content-Type": "application/json"
        }
    
    def create_order(
        self,
        amount: Decimal,
        currency: str = "PLN",
        description: str = None
    ) -> Dict:
        """Create payment order"""
        payload = {
            "intent": "CAPTURE",
            "purchase_units": [{
                "amount": {
                    "currency_code": currency,
                    "value": str(amount)
                },
                "description": description
            }]
        }
        
        response = self._get_client().post(
            f"{self.base_url}/v2/checkout/orders",
            json=payload,
            headers=self._auth_headers()
        )
        response.raise_for_status()
        
        return response.json()
    
    def capture_order(self, order_id: str) -> Payment:
        """Capture payment for order"""
        response = self._get_client().post(
            f"{self.base_url}/v2/checkout/orders/{order_id}/capture",
            headers=self._auth_headers()
        )
        response.raise_for_status()
        
        data = response.json()
        capture = data["purchase_units"][0]["payments"]["captures"][0]
        
        return Payment(
            id=capture["id"],
            amount=Decimal(capture["amount"]["value"]),
            currency=capture["amount"]["currency_code"],
            status=capture["status"].lower(),
            created_at=datetime.fromisoformat(capture["create_time"].replace("Z", "+00:00")),
            source_system="paypal"
        )
    
    def get_transactions(
        self,
        start_date: date,
        end_date: date
    ) -> List[Dict]:
        """Get transaction history"""
        params = {
            "start_date": f"{start_date}T00:00:00Z",
            "end_date": f"{end_date}T23:59:59Z",
            "fields": "all"
        }
        
        response = self._get_client().get(
            f"{self.base_url}/v1/reporting/transactions",
            params=params,
            headers=self._auth_headers()
        )
        response.raise_for_status()
        
        return response.json().get("transaction_details", [])
    
    def close(self):
        if self._client:
            self._client.close()
            self._client = None


# ============================================================
# QUICKBOOKS INTEGRATION
# ============================================================

class QuickBooksClient:
    """
    QuickBooks Online API Client
    
    Documentation: https://developer.intuit.com/app/developer/qbo/docs/api/accounting/
    """
    
    BASE_URL = "https://quickbooks.api.intuit.com/v3"
    SANDBOX_URL = "https://sandbox-quickbooks.api.intuit.com/v3"
    
    def __init__(
        self,
        client_id: str,
        client_secret: str,
        access_token: str,
        refresh_token: str,
        realm_id: str,
        sandbox: bool = False
    ):
        self.client_id = client_id
        self.client_secret = client_secret
        self.access_token = access_token
        self.refresh_token = refresh_token
        self.realm_id = realm_id
        self.base_url = self.SANDBOX_URL if sandbox else self.BASE_URL
        self._client = None
    
    def _get_client(self) -> httpx.Client:
        if self._client is None:
            self._client = httpx.Client(timeout=30.0)
        return self._client
    
    def _auth_headers(self) -> Dict[str, str]:
        return {
            "Authorization": f"Bearer {self.access_token}",
            "Accept": "application/json",
            "Content-Type": "application/json"
        }
    
    def _api_url(self, endpoint: str) -> str:
        return f"{self.base_url}/company/{self.realm_id}/{endpoint}"
    
    def get_invoices(self, limit: int = 100) -> List[Invoice]:
        """Get invoices"""
        query = f"SELECT * FROM Invoice MAXRESULTS {limit}"
        
        response = self._get_client().get(
            self._api_url("query"),
            params={"query": query},
            headers=self._auth_headers()
        )
        response.raise_for_status()
        
        invoices = response.json().get("QueryResponse", {}).get("Invoice", [])
        return [self._parse_invoice(inv) for inv in invoices]
    
    def create_invoice(
        self,
        customer_id: str,
        line_items: List[Dict],
        due_date: date = None
    ) -> Invoice:
        """Create invoice"""
        payload = {
            "CustomerRef": {"value": customer_id},
            "Line": [
                {
                    "Amount": item["amount"],
                    "DetailType": "SalesItemLineDetail",
                    "SalesItemLineDetail": {
                        "ItemRef": {"value": item.get("item_id", "1")},
                        "Qty": item.get("quantity", 1),
                        "UnitPrice": item.get("unit_price", item["amount"])
                    }
                }
                for item in line_items
            ]
        }
        
        if due_date:
            payload["DueDate"] = due_date.isoformat()
        
        response = self._get_client().post(
            self._api_url("invoice"),
            json=payload,
            headers=self._auth_headers()
        )
        response.raise_for_status()
        
        return self._parse_invoice(response.json()["Invoice"])
    
    def get_customers(self, limit: int = 100) -> List[Customer]:
        """Get customers"""
        query = f"SELECT * FROM Customer MAXRESULTS {limit}"
        
        response = self._get_client().get(
            self._api_url("query"),
            params={"query": query},
            headers=self._auth_headers()
        )
        response.raise_for_status()
        
        customers = response.json().get("QueryResponse", {}).get("Customer", [])
        return [self._parse_customer(c) for c in customers]
    
    def get_profit_and_loss(
        self,
        start_date: date,
        end_date: date
    ) -> Dict:
        """Get Profit and Loss report"""
        response = self._get_client().get(
            self._api_url("reports/ProfitAndLoss"),
            params={
                "start_date": start_date.isoformat(),
                "end_date": end_date.isoformat()
            },
            headers=self._auth_headers()
        )
        response.raise_for_status()
        
        return response.json()
    
    def get_balance_sheet(self, as_of_date: date = None) -> Dict:
        """Get Balance Sheet report"""
        params = {}
        if as_of_date:
            params["date"] = as_of_date.isoformat()
        
        response = self._get_client().get(
            self._api_url("reports/BalanceSheet"),
            params=params,
            headers=self._auth_headers()
        )
        response.raise_for_status()
        
        return response.json()
    
    def _parse_invoice(self, data: Dict) -> Invoice:
        return Invoice(
            id=data["Id"],
            number=data.get("DocNumber", ""),
            customer_id=data["CustomerRef"]["value"],
            customer_name=data["CustomerRef"].get("name", ""),
            amount=Decimal(str(data.get("TotalAmt", 0))),
            currency=data.get("CurrencyRef", {}).get("value", "USD"),
            status="paid" if data.get("Balance", 0) == 0 else "sent",
            issue_date=datetime.strptime(data.get("TxnDate", "2024-01-01"), "%Y-%m-%d").date(),
            due_date=datetime.strptime(data.get("DueDate", "2024-01-01"), "%Y-%m-%d").date(),
            source_system="quickbooks"
        )
    
    def _parse_customer(self, data: Dict) -> Customer:
        return Customer(
            id=data["Id"],
            email=data.get("PrimaryEmailAddr", {}).get("Address", ""),
            name=data.get("DisplayName", ""),
            phone=data.get("PrimaryPhone", {}).get("FreeFormNumber")
        )
    
    def close(self):
        if self._client:
            self._client.close()
            self._client = None


# ============================================================
# XERO INTEGRATION
# ============================================================

class XeroClient:
    """
    Xero Accounting API Client
    
    Documentation: https://developer.xero.com/documentation/api/
    """
    
    BASE_URL = "https://api.xero.com/api.xro/2.0"
    
    def __init__(
        self,
        client_id: str,
        client_secret: str,
        access_token: str,
        tenant_id: str
    ):
        self.client_id = client_id
        self.client_secret = client_secret
        self.access_token = access_token
        self.tenant_id = tenant_id
        self._client = None
    
    def _get_client(self) -> httpx.Client:
        if self._client is None:
            self._client = httpx.Client(timeout=30.0)
        return self._client
    
    def _auth_headers(self) -> Dict[str, str]:
        return {
            "Authorization": f"Bearer {self.access_token}",
            "Xero-Tenant-Id": self.tenant_id,
            "Accept": "application/json",
            "Content-Type": "application/json"
        }
    
    def get_invoices(self, status: str = None) -> List[Invoice]:
        """Get invoices"""
        params = {}
        if status:
            params["where"] = f'Status=="{status}"'
        
        response = self._get_client().get(
            f"{self.BASE_URL}/Invoices",
            params=params,
            headers=self._auth_headers()
        )
        response.raise_for_status()
        
        invoices = response.json().get("Invoices", [])
        return [self._parse_invoice(inv) for inv in invoices]
    
    def create_invoice(
        self,
        contact_id: str,
        line_items: List[Dict],
        due_date: date = None
    ) -> Invoice:
        """Create invoice"""
        payload = {
            "Type": "ACCREC",
            "Contact": {"ContactID": contact_id},
            "LineItems": [
                {
                    "Description": item.get("description", ""),
                    "Quantity": item.get("quantity", 1),
                    "UnitAmount": item.get("unit_price", 0),
                    "AccountCode": item.get("account_code", "200")
                }
                for item in line_items
            ]
        }
        
        if due_date:
            payload["DueDate"] = due_date.isoformat()
        
        response = self._get_client().post(
            f"{self.BASE_URL}/Invoices",
            json={"Invoices": [payload]},
            headers=self._auth_headers()
        )
        response.raise_for_status()
        
        return self._parse_invoice(response.json()["Invoices"][0])
    
    def get_contacts(self) -> List[Customer]:
        """Get contacts"""
        response = self._get_client().get(
            f"{self.BASE_URL}/Contacts",
            headers=self._auth_headers()
        )
        response.raise_for_status()
        
        contacts = response.json().get("Contacts", [])
        return [
            Customer(
                id=c["ContactID"],
                email=c.get("EmailAddress", ""),
                name=c.get("Name", ""),
                phone=c.get("Phones", [{}])[0].get("PhoneNumber") if c.get("Phones") else None
            )
            for c in contacts
        ]
    
    def get_bank_transactions(
        self,
        date_from: date = None,
        date_to: date = None
    ) -> List[Dict]:
        """Get bank transactions"""
        params = {}
        if date_from:
            params["where"] = f'Date >= DateTime({date_from.year}, {date_from.month}, {date_from.day})'
        
        response = self._get_client().get(
            f"{self.BASE_URL}/BankTransactions",
            params=params,
            headers=self._auth_headers()
        )
        response.raise_for_status()
        
        return response.json().get("BankTransactions", [])
    
    def _parse_invoice(self, data: Dict) -> Invoice:
        return Invoice(
            id=data["InvoiceID"],
            number=data.get("InvoiceNumber", ""),
            customer_id=data["Contact"]["ContactID"],
            customer_name=data["Contact"].get("Name", ""),
            amount=Decimal(str(data.get("Total", 0))),
            currency=data.get("CurrencyCode", "USD"),
            status=data.get("Status", "").lower(),
            issue_date=datetime.strptime(data.get("Date", "2024-01-01T00:00:00")[:10], "%Y-%m-%d").date(),
            due_date=datetime.strptime(data.get("DueDate", "2024-01-01T00:00:00")[:10], "%Y-%m-%d").date(),
            source_system="xero"
        )
    
    def close(self):
        if self._client:
            self._client.close()
            self._client = None


# ============================================================
# FACTORY
# ============================================================

def create_payment_client(
    provider: str,
    credentials: Dict[str, str]
):
    """
    Factory function to create payment client
    
    Providers: stripe, paypal
    """
    clients = {
        "stripe": lambda: StripeClient(
            api_key=credentials["api_key"]
        ),
        "paypal": lambda: PayPalClient(
            client_id=credentials["client_id"],
            client_secret=credentials["client_secret"],
            sandbox=credentials.get("sandbox", True)
        )
    }
    
    if provider.lower() not in clients:
        raise ValueError(f"Unknown provider: {provider}")
    
    return clients[provider.lower()]()


def create_accounting_client(
    provider: str,
    credentials: Dict[str, str]
):
    """
    Factory function to create accounting client
    
    Providers: quickbooks, xero
    """
    clients = {
        "quickbooks": lambda: QuickBooksClient(**credentials),
        "xero": lambda: XeroClient(**credentials)
    }
    
    if provider.lower() not in clients:
        raise ValueError(f"Unknown provider: {provider}")
    
    return clients[provider.lower()]()


__all__ = [
    'Payment',
    'Customer',
    'Invoice',
    'StripeClient',
    'PayPalClient',
    'QuickBooksClient',
    'XeroClient',
    'create_payment_client',
    'create_accounting_client'
]
