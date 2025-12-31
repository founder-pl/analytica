"""
ANALYTICA Integrations - Global APIs
=====================================

Public API integrations for business data:
- GUS REGON (Polish business registry)
- KRS (National Court Register)
- CEIDG (Polish sole proprietors registry)
- VIES (EU VAT validation)
- NBP (National Bank of Poland - exchange rates)
- GeoIP (Location services)
"""

from typing import Any, Dict, List, Optional, Union
from dataclasses import dataclass, field
from datetime import datetime, date
from decimal import Decimal
from abc import ABC, abstractmethod
import xml.etree.ElementTree as ET
import json
import re

import httpx


# ============================================================
# DATA MODELS
# ============================================================

@dataclass
class CompanyInfo:
    """Company information from registry"""
    nip: str
    regon: str
    name: str
    short_name: Optional[str] = None
    address: str = ""
    city: str = ""
    postal_code: str = ""
    voivodeship: str = ""
    county: str = ""
    commune: str = ""
    legal_form: str = ""
    pkd_main: str = ""
    pkd_codes: List[str] = field(default_factory=list)
    start_date: Optional[date] = None
    status: str = "active"
    krs: Optional[str] = None
    email: Optional[str] = None
    phone: Optional[str] = None
    website: Optional[str] = None
    source: str = ""


@dataclass
class VATStatus:
    """VAT registration status"""
    vat_number: str
    country_code: str
    valid: bool
    name: str = ""
    address: str = ""
    request_date: date = None
    request_identifier: str = ""


@dataclass
class ExchangeRate:
    """Currency exchange rate"""
    currency: str
    code: str
    mid: Decimal
    bid: Optional[Decimal] = None
    ask: Optional[Decimal] = None
    effective_date: date = None
    table_no: str = ""


@dataclass
class KRSEntry:
    """KRS (National Court Register) entry"""
    krs_number: str
    name: str
    nip: Optional[str]
    regon: Optional[str]
    legal_form: str
    address: str
    share_capital: Optional[Decimal] = None
    registration_date: Optional[date] = None
    court: str = ""
    department: str = ""
    representatives: List[Dict] = field(default_factory=list)
    shareholders: List[Dict] = field(default_factory=list)


# ============================================================
# GUS REGON API
# ============================================================

class GUSRegonClient:
    """
    GUS REGON API Client
    
    Access to Polish Central Statistical Office business registry.
    Documentation: https://api.stat.gov.pl/Home/RegonApi
    
    Provides:
    - Company search by NIP, REGON, KRS
    - Full company details
    - PKD codes
    """
    
    WSDL_PROD = "https://wyszukiwarkaregon.stat.gov.pl/wsBIR/UslugaBIRzewnPubl.svc"
    WSDL_TEST = "https://wyszukiwarkaregontest.stat.gov.pl/wsBIR/UslugaBIRzewnPubl.svc"
    
    def __init__(self, api_key: str, test_mode: bool = False):
        self.api_key = api_key
        self.base_url = self.WSDL_TEST if test_mode else self.WSDL_PROD
        self.session_id: Optional[str] = None
        self._client = httpx.Client(timeout=30.0)
    
    def login(self) -> bool:
        """Login and get session ID"""
        envelope = f'''<?xml version="1.0" encoding="utf-8"?>
        <soap:Envelope xmlns:soap="http://www.w3.org/2003/05/soap-envelope"
                       xmlns:ns="http://CIS/BIR/PUBL/2014/07">
            <soap:Header xmlns:wsa="http://www.w3.org/2005/08/addressing">
                <wsa:Action>http://CIS/BIR/PUBL/2014/07/IUslugaBIRzewnPubl/Zaloguj</wsa:Action>
                <wsa:To>{self.base_url}</wsa:To>
            </soap:Header>
            <soap:Body>
                <ns:Zaloguj>
                    <ns:pKluczUzytkownika>{self.api_key}</ns:pKluczUzytkownika>
                </ns:Zaloguj>
            </soap:Body>
        </soap:Envelope>'''
        
        response = self._client.post(
            self.base_url,
            content=envelope,
            headers={"Content-Type": "application/soap+xml; charset=utf-8"}
        )
        
        if response.status_code == 200:
            # Parse session ID from response
            root = ET.fromstring(response.text)
            session_elem = root.find('.//{http://CIS/BIR/PUBL/2014/07}ZalogujResult')
            if session_elem is not None and session_elem.text:
                self.session_id = session_elem.text
                return True
        
        return False
    
    def search_by_nip(self, nip: str) -> Optional[CompanyInfo]:
        """Search company by NIP"""
        nip = re.sub(r'\D', '', nip)  # Remove non-digits
        
        envelope = f'''<?xml version="1.0" encoding="utf-8"?>
        <soap:Envelope xmlns:soap="http://www.w3.org/2003/05/soap-envelope"
                       xmlns:ns="http://CIS/BIR/PUBL/2014/07">
            <soap:Header xmlns:wsa="http://www.w3.org/2005/08/addressing">
                <wsa:Action>http://CIS/BIR/PUBL/2014/07/IUslugaBIRzewnPubl/DaneSzukajPodmioty</wsa:Action>
                <wsa:To>{self.base_url}</wsa:To>
            </soap:Header>
            <soap:Body>
                <ns:DaneSzukajPodmioty>
                    <ns:pParametryWyszukiwania>
                        <ns:Nip>{nip}</ns:Nip>
                    </ns:pParametryWyszukiwania>
                </ns:DaneSzukajPodmioty>
            </soap:Body>
        </soap:Envelope>'''
        
        response = self._client.post(
            self.base_url,
            content=envelope,
            headers={
                "Content-Type": "application/soap+xml; charset=utf-8",
                "sid": self.session_id or ""
            }
        )
        
        if response.status_code == 200:
            return self._parse_company_response(response.text)
        
        return None
    
    def search_by_regon(self, regon: str) -> Optional[CompanyInfo]:
        """Search company by REGON"""
        regon = re.sub(r'\D', '', regon)
        
        envelope = f'''<?xml version="1.0" encoding="utf-8"?>
        <soap:Envelope xmlns:soap="http://www.w3.org/2003/05/soap-envelope"
                       xmlns:ns="http://CIS/BIR/PUBL/2014/07">
            <soap:Header xmlns:wsa="http://www.w3.org/2005/08/addressing">
                <wsa:Action>http://CIS/BIR/PUBL/2014/07/IUslugaBIRzewnPubl/DaneSzukajPodmioty</wsa:Action>
                <wsa:To>{self.base_url}</wsa:To>
            </soap:Header>
            <soap:Body>
                <ns:DaneSzukajPodmioty>
                    <ns:pParametryWyszukiwania>
                        <ns:Regon>{regon}</ns:Regon>
                    </ns:pParametryWyszukiwania>
                </ns:DaneSzukajPodmioty>
            </soap:Body>
        </soap:Envelope>'''
        
        response = self._client.post(
            self.base_url,
            content=envelope,
            headers={
                "Content-Type": "application/soap+xml; charset=utf-8",
                "sid": self.session_id or ""
            }
        )
        
        if response.status_code == 200:
            return self._parse_company_response(response.text)
        
        return None
    
    def _parse_company_response(self, xml_response: str) -> Optional[CompanyInfo]:
        """Parse SOAP response to CompanyInfo"""
        try:
            root = ET.fromstring(xml_response)
            result = root.find('.//{http://CIS/BIR/PUBL/2014/07}DaneSzukajPodmiotyResult')
            
            if result is None or not result.text:
                return None
            
            # Parse inner XML
            data_root = ET.fromstring(result.text)
            dane = data_root.find('.//dane')
            
            if dane is None:
                return None
            
            return CompanyInfo(
                nip=dane.findtext('Nip', ''),
                regon=dane.findtext('Regon', ''),
                name=dane.findtext('Nazwa', ''),
                address=f"{dane.findtext('Ulica', '')} {dane.findtext('NrNieruchomosci', '')}",
                city=dane.findtext('Miejscowosc', ''),
                postal_code=dane.findtext('KodPocztowy', ''),
                voivodeship=dane.findtext('Wojewodztwo', ''),
                pkd_main=dane.findtext('PKD', ''),
                source="gus_regon"
            )
        except Exception:
            return None
    
    def logout(self):
        """End session"""
        if self.session_id:
            envelope = f'''<?xml version="1.0" encoding="utf-8"?>
            <soap:Envelope xmlns:soap="http://www.w3.org/2003/05/soap-envelope"
                           xmlns:ns="http://CIS/BIR/PUBL/2014/07">
                <soap:Header xmlns:wsa="http://www.w3.org/2005/08/addressing">
                    <wsa:Action>http://CIS/BIR/PUBL/2014/07/IUslugaBIRzewnPubl/Wyloguj</wsa:Action>
                    <wsa:To>{self.base_url}</wsa:To>
                </soap:Header>
                <soap:Body>
                    <ns:Wyloguj>
                        <ns:pIdentyfikatorSesji>{self.session_id}</ns:pIdentyfikatorSesji>
                    </ns:Wyloguj>
                </soap:Body>
            </soap:Envelope>'''
            
            self._client.post(
                self.base_url,
                content=envelope,
                headers={"Content-Type": "application/soap+xml; charset=utf-8"}
            )
            self.session_id = None
    
    def close(self):
        self.logout()
        self._client.close()


# ============================================================
# CEIDG API (Polish Sole Proprietors Registry)
# ============================================================

class CEIDGClient:
    """
    CEIDG API Client
    
    Polish Central Registration and Information on Business registry.
    For sole proprietors (jednoosobowa działalność gospodarcza).
    
    Documentation: https://datastore.ceidg.gov.pl/
    """
    
    BASE_URL = "https://dane.biznes.gov.pl/api/ceidg/v2"
    
    def __init__(self, api_token: str):
        self.api_token = api_token
        self._client = httpx.Client(timeout=30.0)
    
    def _headers(self) -> Dict[str, str]:
        return {
            "Authorization": f"Bearer {self.api_token}",
            "Accept": "application/json"
        }
    
    def search_by_nip(self, nip: str) -> Optional[CompanyInfo]:
        """Search by NIP"""
        nip = re.sub(r'\D', '', nip)
        
        response = self._client.get(
            f"{self.BASE_URL}/firmy",
            params={"nip": nip},
            headers=self._headers()
        )
        
        if response.status_code == 200:
            data = response.json()
            if data.get("firmy"):
                return self._parse_company(data["firmy"][0])
        
        return None
    
    def search_by_regon(self, regon: str) -> Optional[CompanyInfo]:
        """Search by REGON"""
        regon = re.sub(r'\D', '', regon)
        
        response = self._client.get(
            f"{self.BASE_URL}/firmy",
            params={"regon": regon},
            headers=self._headers()
        )
        
        if response.status_code == 200:
            data = response.json()
            if data.get("firmy"):
                return self._parse_company(data["firmy"][0])
        
        return None
    
    def search_by_name(self, name: str, limit: int = 10) -> List[CompanyInfo]:
        """Search by company name"""
        response = self._client.get(
            f"{self.BASE_URL}/firmy",
            params={"nazwa": name, "limit": limit},
            headers=self._headers()
        )
        
        if response.status_code == 200:
            data = response.json()
            return [self._parse_company(f) for f in data.get("firmy", [])]
        
        return []
    
    def _parse_company(self, data: Dict) -> CompanyInfo:
        """Parse CEIDG response"""
        adres = data.get("adresDzialalnosci", {})
        
        return CompanyInfo(
            nip=data.get("nip", ""),
            regon=data.get("regon", ""),
            name=data.get("nazwa", ""),
            address=f"{adres.get('ulica', '')} {adres.get('budynek', '')}",
            city=adres.get("miasto", ""),
            postal_code=adres.get("kodPocztowy", ""),
            voivodeship=adres.get("wojewodztwo", ""),
            pkd_main=data.get("pkdGlowny", ""),
            pkd_codes=data.get("pkd", []),
            start_date=datetime.strptime(data["dataRozpoczeciaDzialalnosci"], "%Y-%m-%d").date() 
                       if data.get("dataRozpoczeciaDzialalnosci") else None,
            status=data.get("status", ""),
            email=data.get("email"),
            phone=data.get("telefon"),
            website=data.get("www"),
            source="ceidg"
        )
    
    def close(self):
        self._client.close()


# ============================================================
# KRS API (National Court Register)
# ============================================================

class KRSClient:
    """
    KRS API Client
    
    Access to Polish National Court Register.
    For companies: sp. z o.o., S.A., etc.
    
    Documentation: https://api-krs.ms.gov.pl/
    """
    
    BASE_URL = "https://api-krs.ms.gov.pl/api/krs"
    
    def __init__(self):
        self._client = httpx.Client(timeout=30.0)
    
    def search_by_krs(self, krs_number: str) -> Optional[KRSEntry]:
        """Search by KRS number"""
        krs_number = re.sub(r'\D', '', krs_number).zfill(10)
        
        response = self._client.get(
            f"{self.BASE_URL}/OdsijchnijPodmiot/{krs_number}",
            headers={"Accept": "application/json"}
        )
        
        if response.status_code == 200:
            return self._parse_krs_entry(response.json())
        
        return None
    
    def search_by_nip(self, nip: str) -> Optional[KRSEntry]:
        """Search by NIP"""
        nip = re.sub(r'\D', '', nip)
        
        response = self._client.get(
            f"{self.BASE_URL}/OdpisAktualny/nip/{nip}",
            headers={"Accept": "application/json"}
        )
        
        if response.status_code == 200:
            return self._parse_krs_entry(response.json())
        
        return None
    
    def _parse_krs_entry(self, data: Dict) -> KRSEntry:
        """Parse KRS response"""
        dane = data.get("odpis", {}).get("dane", {})
        dzial1 = dane.get("dzial1", {})
        dzial2 = dane.get("dzial2", {})
        
        # Get representatives
        representatives = []
        for rep in dzial2.get("organUprawnionyDoReprezentowania", {}).get("sklad", []):
            representatives.append({
                "name": f"{rep.get('imiona', '')} {rep.get('nazwisko', '')}",
                "function": rep.get("funkcja", ""),
                "pesel": rep.get("pesel", "")
            })
        
        return KRSEntry(
            krs_number=dzial1.get("numerKRS", ""),
            name=dzial1.get("danePodmiotu", {}).get("nazwa", ""),
            nip=dzial1.get("danePodmiotu", {}).get("nip"),
            regon=dzial1.get("danePodmiotu", {}).get("regon"),
            legal_form=dzial1.get("danePodmiotu", {}).get("formaPrawna", ""),
            address=self._format_address(dzial1.get("siedzibaIAdres", {})),
            share_capital=Decimal(str(dzial1.get("kapital", {}).get("wysokoscKapitaluZakladowego", 0))) 
                         if dzial1.get("kapital") else None,
            court=dzial1.get("informacjeOrejestracji", {}).get("sad", ""),
            representatives=representatives
        )
    
    def _format_address(self, addr: Dict) -> str:
        """Format address from KRS data"""
        parts = [
            addr.get("ulica", ""),
            addr.get("nrDomu", ""),
            addr.get("kodPocztowy", ""),
            addr.get("miejscowosc", "")
        ]
        return " ".join(p for p in parts if p)
    
    def close(self):
        self._client.close()


# ============================================================
# VIES VAT VALIDATION (EU)
# ============================================================

class VIESClient:
    """
    VIES VAT Validation Client
    
    EU VAT number validation service.
    Documentation: https://ec.europa.eu/taxation_customs/vies/
    """
    
    WSDL_URL = "https://ec.europa.eu/taxation_customs/vies/checkVatService.wsdl"
    SERVICE_URL = "https://ec.europa.eu/taxation_customs/vies/services/checkVatService"
    
    def __init__(self):
        self._client = httpx.Client(timeout=30.0)
    
    def check_vat(self, country_code: str, vat_number: str) -> VATStatus:
        """
        Check if VAT number is valid
        
        Args:
            country_code: 2-letter country code (e.g., 'PL', 'DE')
            vat_number: VAT number without country prefix
        
        Returns:
            VATStatus with validation result
        """
        country_code = country_code.upper()
        vat_number = re.sub(r'\D', '', vat_number)
        
        envelope = f'''<?xml version="1.0" encoding="UTF-8"?>
        <soapenv:Envelope xmlns:soapenv="http://schemas.xmlsoap.org/soap/envelope/"
                          xmlns:urn="urn:ec.europa.eu:taxud:vies:services:checkVat:types">
            <soapenv:Header/>
            <soapenv:Body>
                <urn:checkVat>
                    <urn:countryCode>{country_code}</urn:countryCode>
                    <urn:vatNumber>{vat_number}</urn:vatNumber>
                </urn:checkVat>
            </soapenv:Body>
        </soapenv:Envelope>'''
        
        response = self._client.post(
            self.SERVICE_URL,
            content=envelope,
            headers={"Content-Type": "text/xml; charset=utf-8"}
        )
        
        return self._parse_response(response.text, country_code, vat_number)
    
    def _parse_response(self, xml_response: str, country_code: str, vat_number: str) -> VATStatus:
        """Parse VIES SOAP response"""
        try:
            root = ET.fromstring(xml_response)
            
            # Find response elements
            ns = {'ns': 'urn:ec.europa.eu:taxud:vies:services:checkVat:types'}
            
            valid = root.findtext('.//ns:valid', 'false', ns).lower() == 'true'
            name = root.findtext('.//ns:name', '', ns)
            address = root.findtext('.//ns:address', '', ns)
            request_id = root.findtext('.//ns:requestIdentifier', '', ns)
            
            return VATStatus(
                vat_number=f"{country_code}{vat_number}",
                country_code=country_code,
                valid=valid,
                name=name,
                address=address,
                request_date=date.today(),
                request_identifier=request_id
            )
        except Exception:
            return VATStatus(
                vat_number=f"{country_code}{vat_number}",
                country_code=country_code,
                valid=False,
                request_date=date.today()
            )
    
    def close(self):
        self._client.close()


# ============================================================
# NBP EXCHANGE RATES (National Bank of Poland)
# ============================================================

class NBPClient:
    """
    NBP (National Bank of Poland) API Client
    
    Official exchange rates for PLN.
    Documentation: https://api.nbp.pl/
    """
    
    BASE_URL = "https://api.nbp.pl/api"
    
    def __init__(self):
        self._client = httpx.Client(timeout=30.0)
    
    def get_current_rate(self, currency: str, table: str = "A") -> Optional[ExchangeRate]:
        """
        Get current exchange rate
        
        Args:
            currency: 3-letter currency code (EUR, USD, GBP, etc.)
            table: Rate table (A - average, B - average less common, C - bid/ask)
        
        Returns:
            ExchangeRate or None
        """
        response = self._client.get(
            f"{self.BASE_URL}/exchangerates/rates/{table}/{currency.upper()}/",
            headers={"Accept": "application/json"}
        )
        
        if response.status_code == 200:
            data = response.json()
            rate_data = data.get("rates", [{}])[0]
            
            return ExchangeRate(
                currency=data.get("currency", ""),
                code=data.get("code", currency.upper()),
                mid=Decimal(str(rate_data.get("mid", 0))) if "mid" in rate_data else None,
                bid=Decimal(str(rate_data.get("bid", 0))) if "bid" in rate_data else None,
                ask=Decimal(str(rate_data.get("ask", 0))) if "ask" in rate_data else None,
                effective_date=datetime.strptime(rate_data.get("effectiveDate", "2024-01-01"), "%Y-%m-%d").date(),
                table_no=rate_data.get("no", "")
            )
        
        return None
    
    def get_rate_for_date(self, currency: str, rate_date: date, table: str = "A") -> Optional[ExchangeRate]:
        """Get exchange rate for specific date"""
        response = self._client.get(
            f"{self.BASE_URL}/exchangerates/rates/{table}/{currency.upper()}/{rate_date.isoformat()}/",
            headers={"Accept": "application/json"}
        )
        
        if response.status_code == 200:
            data = response.json()
            rate_data = data.get("rates", [{}])[0]
            
            return ExchangeRate(
                currency=data.get("currency", ""),
                code=data.get("code", currency.upper()),
                mid=Decimal(str(rate_data.get("mid", 0))),
                effective_date=datetime.strptime(rate_data.get("effectiveDate", "2024-01-01"), "%Y-%m-%d").date(),
                table_no=rate_data.get("no", "")
            )
        
        return None
    
    def get_rates_range(
        self, 
        currency: str, 
        start_date: date, 
        end_date: date,
        table: str = "A"
    ) -> List[ExchangeRate]:
        """Get exchange rates for date range"""
        response = self._client.get(
            f"{self.BASE_URL}/exchangerates/rates/{table}/{currency.upper()}/{start_date.isoformat()}/{end_date.isoformat()}/",
            headers={"Accept": "application/json"}
        )
        
        rates = []
        if response.status_code == 200:
            data = response.json()
            for rate_data in data.get("rates", []):
                rates.append(ExchangeRate(
                    currency=data.get("currency", ""),
                    code=data.get("code", currency.upper()),
                    mid=Decimal(str(rate_data.get("mid", 0))),
                    effective_date=datetime.strptime(rate_data.get("effectiveDate", "2024-01-01"), "%Y-%m-%d").date(),
                    table_no=rate_data.get("no", "")
                ))
        
        return rates
    
    def get_all_rates(self, table: str = "A") -> List[ExchangeRate]:
        """Get all current exchange rates"""
        response = self._client.get(
            f"{self.BASE_URL}/exchangerates/tables/{table}/",
            headers={"Accept": "application/json"}
        )
        
        rates = []
        if response.status_code == 200:
            data = response.json()[0]
            effective_date = datetime.strptime(data.get("effectiveDate", "2024-01-01"), "%Y-%m-%d").date()
            table_no = data.get("no", "")
            
            for rate_data in data.get("rates", []):
                rates.append(ExchangeRate(
                    currency=rate_data.get("currency", ""),
                    code=rate_data.get("code", ""),
                    mid=Decimal(str(rate_data.get("mid", 0))),
                    effective_date=effective_date,
                    table_no=table_no
                ))
        
        return rates
    
    def convert_amount(
        self, 
        amount: Decimal, 
        from_currency: str, 
        to_currency: str = "PLN",
        rate_date: date = None
    ) -> Optional[Decimal]:
        """
        Convert amount between currencies
        
        Args:
            amount: Amount to convert
            from_currency: Source currency
            to_currency: Target currency (default PLN)
            rate_date: Date for rate (default: current)
        
        Returns:
            Converted amount or None
        """
        if from_currency.upper() == "PLN":
            # PLN to foreign
            rate = self.get_rate_for_date(to_currency, rate_date) if rate_date else self.get_current_rate(to_currency)
            if rate and rate.mid:
                return amount / rate.mid
        elif to_currency.upper() == "PLN":
            # Foreign to PLN
            rate = self.get_rate_for_date(from_currency, rate_date) if rate_date else self.get_current_rate(from_currency)
            if rate and rate.mid:
                return amount * rate.mid
        else:
            # Foreign to foreign via PLN
            rate_from = self.get_current_rate(from_currency)
            rate_to = self.get_current_rate(to_currency)
            if rate_from and rate_to and rate_from.mid and rate_to.mid:
                pln_amount = amount * rate_from.mid
                return pln_amount / rate_to.mid
        
        return None
    
    def close(self):
        self._client.close()


# ============================================================
# NIP VALIDATOR
# ============================================================

def validate_nip(nip: str) -> bool:
    """
    Validate Polish NIP (Tax Identification Number)
    
    NIP consists of 10 digits with checksum in last position.
    """
    nip = re.sub(r'\D', '', nip)
    
    if len(nip) != 10:
        return False
    
    weights = [6, 5, 7, 2, 3, 4, 5, 6, 7]
    checksum = sum(int(nip[i]) * weights[i] for i in range(9)) % 11
    
    return checksum == int(nip[9])


def validate_regon(regon: str) -> bool:
    """
    Validate Polish REGON (Statistical Number)
    
    REGON can be 9 or 14 digits.
    """
    regon = re.sub(r'\D', '', regon)
    
    if len(regon) == 9:
        weights = [8, 9, 2, 3, 4, 5, 6, 7]
        checksum = sum(int(regon[i]) * weights[i] for i in range(8)) % 11
        return checksum % 10 == int(regon[8])
    elif len(regon) == 14:
        weights = [2, 4, 8, 5, 0, 9, 7, 3, 6, 1, 2, 4, 8]
        checksum = sum(int(regon[i]) * weights[i] for i in range(13)) % 11
        return checksum % 10 == int(regon[13])
    
    return False


def validate_krs(krs: str) -> bool:
    """Validate KRS number (10 digits)"""
    krs = re.sub(r'\D', '', krs)
    return len(krs) == 10


# ============================================================
# EXPORTS
# ============================================================

__all__ = [
    # Models
    'CompanyInfo',
    'VATStatus',
    'ExchangeRate',
    'KRSEntry',
    
    # Clients
    'GUSRegonClient',
    'CEIDGClient',
    'KRSClient',
    'VIESClient',
    'NBPClient',
    
    # Validators
    'validate_nip',
    'validate_regon',
    'validate_krs',
]
