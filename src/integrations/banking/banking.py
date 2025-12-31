"""
ANALYTICA Integrations - Banking
================================

Banking integrations supporting:
- MT940 SWIFT format parsing
- PSD2 Open Banking API
- Polish banks (mBank, ING, PKO BP, Santander, Millennium)
"""

from typing import Any, Dict, List, Optional, Tuple
from dataclasses import dataclass, field
from datetime import datetime, date
from decimal import Decimal
from enum import Enum
from abc import ABC, abstractmethod
import re
import hashlib

import httpx


# ============================================================
# DATA MODELS
# ============================================================

class TransactionType(Enum):
    CREDIT = "credit"  # Money in
    DEBIT = "debit"    # Money out
    TRANSFER = "transfer"
    PAYMENT = "payment"
    FEE = "fee"
    INTEREST = "interest"
    OTHER = "other"


@dataclass
class BankTransaction:
    """Bank transaction model"""
    id: str
    date: date
    value_date: date
    amount: Decimal
    currency: str
    transaction_type: TransactionType
    description: str
    reference: str
    counterparty_name: Optional[str] = None
    counterparty_account: Optional[str] = None
    balance_after: Optional[Decimal] = None
    raw_data: Dict = field(default_factory=dict)
    source: str = ""


@dataclass
class BankStatement:
    """Bank statement model"""
    account_number: str
    bank_code: str
    statement_number: str
    opening_balance: Decimal
    closing_balance: Decimal
    opening_date: date
    closing_date: date
    currency: str
    transactions: List[BankTransaction] = field(default_factory=list)
    raw_content: str = ""


@dataclass
class BankAccount:
    """Bank account model for PSD2"""
    iban: str
    bban: Optional[str]
    currency: str
    account_type: str
    name: Optional[str]
    balance: Optional[Decimal] = None
    bank_name: str = ""


# ============================================================
# MT940 PARSER
# ============================================================

class MT940Parser:
    """
    MT940 SWIFT Bank Statement Parser
    
    Parses standard MT940 format used by most banks.
    
    Tags:
        :20: Transaction Reference
        :25: Account Identification
        :28C: Statement Number
        :60F: Opening Balance
        :61: Statement Line (Transaction)
        :86: Information to Account Owner
        :62F: Closing Balance
    """
    
    # Tag patterns
    TAG_PATTERN = re.compile(r':(\d{2}[A-Z]?):(.+?)(?=:\d{2}|$)', re.DOTALL)
    
    # Transaction line pattern (tag 61)
    # YYMMDD[MMDD]2a[1!a]15d1!a3!c16x[//16x][34x]
    TRANSACTION_PATTERN = re.compile(
        r'(?P<date>\d{6})'
        r'(?P<entry_date>\d{4})?'
        r'(?P<dc>[CD]R?)'
        r'(?P<funds_code>[A-Z])?'
        r'(?P<amount>[\d,]+)'
        r'(?P<type>[A-Z]{4})'
        r'(?P<reference>[^\n/]+)?'
        r'(?://(?P<bank_reference>[^\n]+))?'
    )
    
    # Balance pattern (tags 60F, 62F)
    BALANCE_PATTERN = re.compile(
        r'(?P<dc>[CD])'
        r'(?P<date>\d{6})'
        r'(?P<currency>[A-Z]{3})'
        r'(?P<amount>[\d,]+)'
    )
    
    def parse(self, content: str) -> List[BankStatement]:
        """Parse MT940 content to list of statements"""
        statements = []
        
        # Split into individual messages
        messages = self._split_messages(content)
        
        for message in messages:
            statement = self._parse_message(message)
            if statement:
                statements.append(statement)
        
        return statements
    
    def parse_file(self, filepath: str) -> List[BankStatement]:
        """Parse MT940 file"""
        with open(filepath, 'r', encoding='utf-8', errors='replace') as f:
            content = f.read()
        return self.parse(content)
    
    def _split_messages(self, content: str) -> List[str]:
        """Split content into individual MT940 messages"""
        # Messages typically start with {1: or :20:
        messages = []
        
        # Try SWIFT envelope format first
        swift_pattern = re.compile(r'\{1:.*?\}.*?\{4:(.*?)-\}', re.DOTALL)
        matches = swift_pattern.findall(content)
        
        if matches:
            messages = matches
        else:
            # Fallback: split by :20: tag
            parts = re.split(r'(?=:20:)', content)
            messages = [p for p in parts if p.strip() and ':20:' in p]
        
        return messages
    
    def _parse_message(self, message: str) -> Optional[BankStatement]:
        """Parse single MT940 message"""
        tags = self._extract_tags(message)
        
        if not tags:
            return None
        
        # Extract basic info
        account = tags.get('25', '').strip()
        statement_num = tags.get('28C', '').strip()
        
        # Parse balances
        opening = self._parse_balance(tags.get('60F', ''))
        closing = self._parse_balance(tags.get('62F', ''))
        
        if not opening or not closing:
            return None
        
        # Parse transactions
        transactions = self._parse_transactions(tags, message)
        
        return BankStatement(
            account_number=account,
            bank_code=self._extract_bank_code(account),
            statement_number=statement_num,
            opening_balance=opening['amount'],
            closing_balance=closing['amount'],
            opening_date=opening['date'],
            closing_date=closing['date'],
            currency=opening['currency'],
            transactions=transactions,
            raw_content=message
        )
    
    def _extract_tags(self, message: str) -> Dict[str, str]:
        """Extract tags from message"""
        tags = {}
        for match in self.TAG_PATTERN.finditer(message):
            tag = match.group(1)
            value = match.group(2).strip()
            
            # Handle multiple 61 tags
            if tag == '61':
                if '61' not in tags:
                    tags['61'] = []
                tags['61'].append(value)
            else:
                tags[tag] = value
        
        return tags
    
    def _parse_balance(self, balance_str: str) -> Optional[Dict]:
        """Parse balance string"""
        if not balance_str:
            return None
        
        match = self.BALANCE_PATTERN.match(balance_str.replace('\n', ''))
        if not match:
            return None
        
        dc = match.group('dc')
        date_str = match.group('date')
        currency = match.group('currency')
        amount_str = match.group('amount').replace(',', '.')
        
        amount = Decimal(amount_str)
        if dc == 'D':
            amount = -amount
        
        return {
            'amount': amount,
            'currency': currency,
            'date': datetime.strptime(date_str, '%y%m%d').date()
        }
    
    def _parse_transactions(self, tags: Dict, message: str) -> List[BankTransaction]:
        """Parse transaction lines"""
        transactions = []
        
        transaction_lines = tags.get('61', [])
        if not isinstance(transaction_lines, list):
            transaction_lines = [transaction_lines]
        
        # Get corresponding :86: tags (descriptions)
        descriptions = re.findall(r':86:([^:]+?)(?=:(?:61|62|86):|$)', message, re.DOTALL)
        
        for i, line in enumerate(transaction_lines):
            tx = self._parse_transaction_line(line)
            if tx:
                # Add description if available
                if i < len(descriptions):
                    tx.description = descriptions[i].strip().replace('\n', ' ')
                transactions.append(tx)
        
        return transactions
    
    def _parse_transaction_line(self, line: str) -> Optional[BankTransaction]:
        """Parse single transaction line (tag 61)"""
        line = line.replace('\n', '')
        match = self.TRANSACTION_PATTERN.match(line)
        
        if not match:
            return None
        
        date_str = match.group('date')
        dc = match.group('dc')
        amount_str = match.group('amount').replace(',', '.')
        tx_type = match.group('type')
        reference = match.group('reference') or ""
        bank_ref = match.group('bank_reference') or ""
        
        amount = Decimal(amount_str)
        tx_date = datetime.strptime(date_str, '%y%m%d').date()
        
        # Determine credit/debit
        is_credit = dc.startswith('C')
        if not is_credit:
            amount = -amount
        
        return BankTransaction(
            id=hashlib.md5(f"{date_str}{amount_str}{reference}".encode()).hexdigest()[:12],
            date=tx_date,
            value_date=tx_date,
            amount=amount,
            currency="",  # Set from statement
            transaction_type=TransactionType.CREDIT if is_credit else TransactionType.DEBIT,
            description="",
            reference=reference.strip(),
            raw_data={"line": line, "type_code": tx_type, "bank_ref": bank_ref},
            source="mt940"
        )
    
    def _extract_bank_code(self, account: str) -> str:
        """Extract bank code from account"""
        # Polish IBAN: PL + 2 check digits + 8 bank code + 16 account
        if account.startswith('PL') and len(account) >= 10:
            return account[4:12]
        return ""


# ============================================================
# PSD2 OPEN BANKING
# ============================================================

class PSD2Client(ABC):
    """Base class for PSD2 Open Banking clients"""
    
    def __init__(self, client_id: str, client_secret: str, redirect_uri: str):
        self.client_id = client_id
        self.client_secret = client_secret
        self.redirect_uri = redirect_uri
        self.access_token: Optional[str] = None
        self.refresh_token: Optional[str] = None
        self._client: Optional[httpx.Client] = None
    
    def _get_client(self) -> httpx.Client:
        if self._client is None:
            self._client = httpx.Client(timeout=30.0)
        return self._client
    
    @abstractmethod
    def get_authorization_url(self, scope: str = "accounts") -> str:
        """Get OAuth2 authorization URL"""
        pass
    
    @abstractmethod
    def exchange_code(self, code: str) -> Dict[str, str]:
        """Exchange authorization code for tokens"""
        pass
    
    @abstractmethod
    def get_accounts(self) -> List[BankAccount]:
        """Get list of accounts"""
        pass
    
    @abstractmethod
    def get_transactions(
        self, 
        account_id: str,
        date_from: date = None,
        date_to: date = None
    ) -> List[BankTransaction]:
        """Get transactions for account"""
        pass
    
    @abstractmethod
    def get_balance(self, account_id: str) -> Dict[str, Decimal]:
        """Get account balance"""
        pass
    
    def close(self):
        if self._client:
            self._client.close()
            self._client = None


# ============================================================
# POLISH BANKS - PSD2 IMPLEMENTATIONS
# ============================================================

class MBankPSD2Client(PSD2Client):
    """
    mBank PSD2 API Client
    
    Documentation: https://developer.mbank.pl
    """
    
    AUTH_URL = "https://online.mbank.pl/oauth2/authorize"
    TOKEN_URL = "https://api.mbank.pl/oauth2/token"
    API_URL = "https://api.mbank.pl/pl/accounts/v1"
    
    def get_authorization_url(self, scope: str = "accounts") -> str:
        params = {
            "response_type": "code",
            "client_id": self.client_id,
            "redirect_uri": self.redirect_uri,
            "scope": scope,
            "state": hashlib.md5(str(datetime.now()).encode()).hexdigest()
        }
        query = "&".join(f"{k}={v}" for k, v in params.items())
        return f"{self.AUTH_URL}?{query}"
    
    def exchange_code(self, code: str) -> Dict[str, str]:
        response = self._get_client().post(
            self.TOKEN_URL,
            data={
                "grant_type": "authorization_code",
                "code": code,
                "redirect_uri": self.redirect_uri,
                "client_id": self.client_id,
                "client_secret": self.client_secret
            }
        )
        response.raise_for_status()
        
        data = response.json()
        self.access_token = data.get("access_token")
        self.refresh_token = data.get("refresh_token")
        
        return data
    
    def _auth_headers(self) -> Dict[str, str]:
        return {
            "Authorization": f"Bearer {self.access_token}",
            "Content-Type": "application/json"
        }
    
    def get_accounts(self) -> List[BankAccount]:
        response = self._get_client().get(
            f"{self.API_URL}/accounts",
            headers=self._auth_headers()
        )
        response.raise_for_status()
        
        return [
            BankAccount(
                iban=acc.get("iban", ""),
                bban=acc.get("bban"),
                currency=acc.get("currency", "PLN"),
                account_type=acc.get("accountType", ""),
                name=acc.get("name"),
                bank_name="mBank"
            )
            for acc in response.json().get("accounts", [])
        ]
    
    def get_transactions(
        self, 
        account_id: str,
        date_from: date = None,
        date_to: date = None
    ) -> List[BankTransaction]:
        params = {}
        if date_from:
            params["dateFrom"] = date_from.isoformat()
        if date_to:
            params["dateTo"] = date_to.isoformat()
        
        response = self._get_client().get(
            f"{self.API_URL}/accounts/{account_id}/transactions",
            params=params,
            headers=self._auth_headers()
        )
        response.raise_for_status()
        
        return [
            self._parse_transaction(tx)
            for tx in response.json().get("transactions", {}).get("booked", [])
        ]
    
    def get_balance(self, account_id: str) -> Dict[str, Decimal]:
        response = self._get_client().get(
            f"{self.API_URL}/accounts/{account_id}/balances",
            headers=self._auth_headers()
        )
        response.raise_for_status()
        
        balances = {}
        for bal in response.json().get("balances", []):
            bal_type = bal.get("balanceType", "available")
            amount = Decimal(str(bal.get("balanceAmount", {}).get("amount", 0)))
            balances[bal_type] = amount
        
        return balances
    
    def _parse_transaction(self, data: Dict) -> BankTransaction:
        amount = Decimal(str(data.get("transactionAmount", {}).get("amount", 0)))
        
        return BankTransaction(
            id=data.get("transactionId", ""),
            date=datetime.strptime(data.get("bookingDate", "2024-01-01"), "%Y-%m-%d").date(),
            value_date=datetime.strptime(data.get("valueDate", "2024-01-01"), "%Y-%m-%d").date(),
            amount=amount,
            currency=data.get("transactionAmount", {}).get("currency", "PLN"),
            transaction_type=TransactionType.CREDIT if amount > 0 else TransactionType.DEBIT,
            description=data.get("remittanceInformationUnstructured", ""),
            reference=data.get("endToEndId", ""),
            counterparty_name=data.get("creditorName") or data.get("debtorName"),
            counterparty_account=data.get("creditorAccount", {}).get("iban") or 
                                data.get("debtorAccount", {}).get("iban"),
            raw_data=data,
            source="mbank_psd2"
        )


class INGPolskaPSD2Client(PSD2Client):
    """
    ING Bank Śląski PSD2 API Client
    
    Documentation: https://developer.ing.pl
    """
    
    AUTH_URL = "https://login.ing.pl/oauth2/authorize"
    TOKEN_URL = "https://api.ing.pl/oauth2/token"
    API_URL = "https://api.ing.pl/openbanking/v1"
    
    def get_authorization_url(self, scope: str = "accounts") -> str:
        params = {
            "response_type": "code",
            "client_id": self.client_id,
            "redirect_uri": self.redirect_uri,
            "scope": scope
        }
        query = "&".join(f"{k}={v}" for k, v in params.items())
        return f"{self.AUTH_URL}?{query}"
    
    def exchange_code(self, code: str) -> Dict[str, str]:
        response = self._get_client().post(
            self.TOKEN_URL,
            data={
                "grant_type": "authorization_code",
                "code": code,
                "redirect_uri": self.redirect_uri,
                "client_id": self.client_id,
                "client_secret": self.client_secret
            }
        )
        response.raise_for_status()
        
        data = response.json()
        self.access_token = data.get("access_token")
        self.refresh_token = data.get("refresh_token")
        
        return data
    
    def _auth_headers(self) -> Dict[str, str]:
        return {
            "Authorization": f"Bearer {self.access_token}",
            "Content-Type": "application/json"
        }
    
    def get_accounts(self) -> List[BankAccount]:
        response = self._get_client().get(
            f"{self.API_URL}/accounts",
            headers=self._auth_headers()
        )
        response.raise_for_status()
        
        return [
            BankAccount(
                iban=acc.get("iban", ""),
                bban=acc.get("bban"),
                currency=acc.get("currency", "PLN"),
                account_type=acc.get("product", ""),
                name=acc.get("name"),
                bank_name="ING Bank Śląski"
            )
            for acc in response.json().get("accounts", [])
        ]
    
    def get_transactions(
        self, 
        account_id: str,
        date_from: date = None,
        date_to: date = None
    ) -> List[BankTransaction]:
        params = {}
        if date_from:
            params["dateFrom"] = date_from.isoformat()
        if date_to:
            params["dateTo"] = date_to.isoformat()
        
        response = self._get_client().get(
            f"{self.API_URL}/accounts/{account_id}/transactions",
            params=params,
            headers=self._auth_headers()
        )
        response.raise_for_status()
        
        transactions = []
        for tx in response.json().get("transactions", {}).get("booked", []):
            transactions.append(self._parse_transaction(tx))
        
        return transactions
    
    def get_balance(self, account_id: str) -> Dict[str, Decimal]:
        response = self._get_client().get(
            f"{self.API_URL}/accounts/{account_id}/balances",
            headers=self._auth_headers()
        )
        response.raise_for_status()
        
        balances = {}
        for bal in response.json().get("balances", []):
            bal_type = bal.get("balanceType", "available")
            amount = Decimal(str(bal.get("balanceAmount", {}).get("amount", 0)))
            balances[bal_type] = amount
        
        return balances
    
    def _parse_transaction(self, data: Dict) -> BankTransaction:
        amount = Decimal(str(data.get("transactionAmount", {}).get("amount", 0)))
        
        return BankTransaction(
            id=data.get("transactionId", ""),
            date=datetime.strptime(data.get("bookingDate", "2024-01-01"), "%Y-%m-%d").date(),
            value_date=datetime.strptime(data.get("valueDate", "2024-01-01"), "%Y-%m-%d").date(),
            amount=amount,
            currency=data.get("transactionAmount", {}).get("currency", "PLN"),
            transaction_type=TransactionType.CREDIT if amount > 0 else TransactionType.DEBIT,
            description=data.get("remittanceInformationUnstructured", ""),
            reference=data.get("endToEndId", ""),
            counterparty_name=data.get("creditorName") or data.get("debtorName"),
            counterparty_account=data.get("creditorAccount", {}).get("iban"),
            raw_data=data,
            source="ing_psd2"
        )


# ============================================================
# FACTORY
# ============================================================

def create_bank_client(
    bank: str,
    credentials: Dict[str, str]
) -> PSD2Client:
    """
    Factory to create bank client
    
    Supported banks: mbank, ing, pko, santander, millennium
    """
    clients = {
        "mbank": MBankPSD2Client,
        "ing": INGPolskaPSD2Client,
        # Add more banks...
    }
    
    if bank.lower() not in clients:
        raise ValueError(f"Unsupported bank: {bank}. Supported: {list(clients.keys())}")
    
    return clients[bank.lower()](
        client_id=credentials["client_id"],
        client_secret=credentials["client_secret"],
        redirect_uri=credentials["redirect_uri"]
    )


def parse_mt940(content: str) -> List[BankStatement]:
    """Quick function to parse MT940 content"""
    parser = MT940Parser()
    return parser.parse(content)


def parse_mt940_file(filepath: str) -> List[BankStatement]:
    """Quick function to parse MT940 file"""
    parser = MT940Parser()
    return parser.parse_file(filepath)


__all__ = [
    'BankTransaction',
    'BankStatement',
    'BankAccount',
    'TransactionType',
    'MT940Parser',
    'PSD2Client',
    'MBankPSD2Client',
    'INGPolskaPSD2Client',
    'create_bank_client',
    'parse_mt940',
    'parse_mt940_file'
]
