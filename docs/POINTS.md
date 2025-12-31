# Analytica - System Punktów

## Menu

- [Dokumentacja (INDEX)](INDEX.md)
- [README](../README.md)
- [Architektura](ARCHITECTURE.md)
- [API](API.md)
- [DSL](DSL.md)
- [Moduły](MODULES.md)
- [Compliance](COMPLIANCE.md)
- [Roadmap](ROADMAP.md)
- [Views Roadmap](VIEWS_ROADMAP.md)
- [Mapa plików projektu](../PROJECT_FILES.md)

## Spis Treści

- [Przegląd](#przegląd)
- [Modele zakupu](#modele-zakupu)
- [Przelicznik punktów](#przelicznik-punktów)
- [API punktów](#api-punktów)
- [Integracja z Frontend](#integracja-z-frontend)
- [FAQ](#faq)

---

## Przegląd

System punktów to uniwersalna waluta w ekosystemie Analytica. Punkty można wykorzystać w dowolnym produkcie (PlanBudzetu, PlanInwestycji, MultiPlan, Estymacja) zarówno przez **Frontend UI** jak i **REST API**.

```
┌────────────────────────────────────────────────────────────┐
│                    SYSTEM PUNKTÓW                          │
│                                                            │
│   💳 KUP PUNKTY    →    📊 UŻYJ W DOWOLNYM PRODUKCIE      │
│                                                            │
│   Frontend UI  ────────────┐                               │
│                            ├──▶  1 punkt = 1 operacja      │
│   REST API    ─────────────┘                               │
│                                                            │
│   Ważność: 12 miesięcy od zakupu                          │
│   Rollover: TAK (w subskrypcji)                           │
└────────────────────────────────────────────────────────────┘
```

---

## Modele zakupu

### 1. 💳 Pakiet Punktów (jednorazowy)

Dla użytkowników, którzy preferują elastyczność bez zobowiązań.

| Pakiet | Cena | Cena/punkt | Oszczędność |
|--------|------|------------|-------------|
| 50 punktów | 50 zł | 1.00 zł | - |
| 100 punktów | 95 zł | 0.95 zł | 5% |
| 200 punktów | 180 zł | 0.90 zł | 10% |
| 500 punktów | 400 zł | 0.80 zł | 20% |
| 1000 punktów | 750 zł | 0.75 zł | 25% |
| 5000 punktów | 3500 zł | 0.70 zł | 30% |
| 10000 punktów | 6500 zł | 0.65 zł | 35% |

**Cechy:**
- ✅ Ważność 12 miesięcy od zakupu
- ✅ Dostęp do Frontend + API
- ✅ Faktura VAT
- ✅ Bez zobowiązań
- ❌ Brak rollover (punkty przepadają po 12 mies.)

---

### 2. 🔄 Subskrypcja (miesięczna/roczna)

Dla regularnych użytkowników z przewidywalnym zużyciem.

#### Subskrypcja Miesięczna

| Plan | Cena/mies. | Punkty/mies. | Cena/punkt |
|------|------------|--------------|------------|
| **Standard** | 199 zł | 250 pkt | 0.80 zł |

**Cechy:**
- ✅ 250 punktów miesięcznie
- ✅ **Rollover** - niewykorzystane punkty przechodzą na następny miesiąc
- ✅ DSL Pipeline Builder
- ✅ Priority support
- ✅ Anuluj w dowolnym momencie

#### Subskrypcja Roczna

| Plan | Cena/rok | Punkty/rok | Bonus | Cena/punkt |
|------|----------|------------|-------|------------|
| **Annual** | 1 990 zł | 3000 pkt | +500 pkt | 0.57 zł |

**Cechy:**
- ✅ 3500 punktów rocznie (3000 + 500 bonus)
- ✅ **43% taniej** niż miesięczna
- ✅ Wszystkie funkcje Standard
- ✅ Dedykowany opiekun
- ✅ Faktura roczna

---

### 3. 🏢 Enterprise (zapytanie ofertowe)

Dla firm wymagających dedykowanej integracji.

**Proces:**
1. Wyślij zapytanie na `enterprise@analytica.pl`
2. Spotkanie discovery (30 min)
3. Propozycja rozwiązania + wycena
4. Wdrożenie (2-8 tygodni)

**Zawiera:**
- ✅ Integracja on-premise lub private cloud
- ✅ Dedykowane API endpoints
- ✅ Custom moduły DSL
- ✅ Integracja z ERP/CRM/BI
- ✅ SLA 99.99% z gwarancją
- ✅ Dedykowany opiekun + szkolenia
- ✅ Nielimitowane punkty lub custom pricing

**Kontakt:** enterprise@analytica.pl

---

## Przelicznik punktów

### Operacje płatne (1 punkt)

| Produkt | Operacja | Koszt |
|---------|----------|-------|
| **PlanBudzetu** | Raport budżetowy (PDF/Excel/HTML) | 1 pkt |
| **PlanBudzetu** | Analiza wariancji | 1 pkt |
| **PlanInwestycji** | Analiza ROI + NPV + IRR | 1 pkt |
| **PlanInwestycji** | Scenariusz inwestycyjny | 1 pkt |
| **MultiPlan** | Scenariusz what-if | 1 pkt |
| **MultiPlan** | Rolling forecast | 1 pkt |
| **Estymacja** | Prognoza AI (do 365 dni) | 1 pkt |
| **Estymacja** | Analiza trendu | 1 pkt |

### Operacje darmowe (0 punktów)

| Operacja | Koszt |
|----------|-------|
| `data.load()` - załadowanie danych | 0 pkt |
| `data.from_input()` - dane z requestu | 0 pkt |
| `transform.*` - transformacje | 0 pkt |
| `metrics.*` - obliczenia | 0 pkt |
| `alert.threshold()` - sprawdzenie alertu | 0 pkt |
| `export.*` - eksport wyników | 0 pkt |

### Przykłady pipeline'ów

```dsl
# Koszt: 1 punkt (1x report.generate)
data.load("sales.csv")
| transform.filter(year=2024)
| metrics.sum("amount")
| report.generate(format="pdf")

# Koszt: 2 punkty (1x budget.variance + 1x report.generate)
budget.load("budget_2025")
| budget.variance()
| report.generate(format="excel")

# Koszt: 1 punkt (1x investment.analyze = ROI+NPV+IRR w jednym)
investment.analyze(
    initial_investment=100000,
    cash_flows=[30000, 40000, 50000],
    discount_rate=0.12
)

# Koszt: 0 punktów (tylko transformacje i metryki)
data.from_input()
| transform.filter(status="active")
| metrics.count()
| export.to_json()
```

---

## API punktów

### Sprawdzenie salda

```bash
GET /api/v1/auth/points
Authorization: Bearer <token>
```

**Response:**
```json
{
  "user_id": "user_123",
  "points_balance": 150,
  "plan": "subscription",
  "transactions": [
    {"id": "tx_001", "type": "purchase", "amount": 200, "timestamp": "..."},
    {"id": "tx_002", "type": "usage", "amount": -5, "timestamp": "..."}
  ]
}
```

### Zakup punktów

```bash
POST /api/v1/auth/points/purchase
Authorization: Bearer <token>
Content-Type: application/json

{
  "amount": 100,
  "payment_method": "card"
}
```

**Response:**
```json
{
  "user_id": "user_123",
  "points_balance": 250,
  "transaction_id": "tx_003",
  "amount": 100,
  "type": "purchase"
}
```

### Wykorzystanie punktów (automatyczne)

Punkty są automatycznie pobierane podczas wykonywania pipeline'ów:

```bash
POST /api/v1/pipeline/execute
Authorization: Bearer <token>
Content-Type: application/json

{
  "dsl": "budget.load('test') | budget.variance() | report.generate(format='pdf')"
}
```

**Response (sukces):**
```json
{
  "status": "success",
  "points_used": 2,
  "points_balance": 148,
  "result": { ... }
}
```

**Response (brak punktów):**
```json
{
  "status": "error",
  "error": "Insufficient points. Need 2, have 0",
  "code": "INSUFFICIENT_POINTS"
}
```

### Manualne użycie punktów

```bash
POST /api/v1/auth/points/use
Authorization: Bearer <token>
Content-Type: application/json

{
  "amount": 5
}
```

---

## Integracja z Frontend

### JavaScript SDK

```javascript
import { createClient } from '/ui/sdk/analytica.js';

const client = createClient({
  baseUrl: 'http://localhost:18000',
  token: localStorage.getItem('analytica_token')
});

// Sprawdź punkty
const points = await client.getPoints();
console.log(`Saldo: ${points.points_balance} pkt`);

// Wykonaj pipeline (automatyczne pobranie punktów)
const result = await client.run(`
  budget.load("budget_2025")
  | budget.variance()
  | report.generate(format="pdf")
`);

console.log(`Użyto: ${result.points_used} pkt`);
console.log(`Pozostało: ${result.points_balance} pkt`);
```

### Frontend UI

W Dashboard UI (`/ui/`) punkty są wyświetlane w nagłówku:

```
┌─────────────────────────────────────────────────────┐
│  Analytica Dashboard           👤 Jan K. | 💰 150 pkt │
├─────────────────────────────────────────────────────┤
│                                                      │
│  [Pipeline Builder]                                  │
│                                                      │
└─────────────────────────────────────────────────────┘
```

---

## FAQ

### Jak długo ważne są punkty?

- **Pakiet jednorazowy:** 12 miesięcy od daty zakupu
- **Subskrypcja:** Rollover - przechodzą na następny miesiąc (max 3x miesięczna pula)

### Co się stanie gdy skończą mi się punkty?

API zwróci błąd `402 Payment Required` z kodem `INSUFFICIENT_POINTS`. Frontend wyświetli modal z opcją dokupienia punktów.

### Czy mogę przenieść punkty na inne konto?

Nie, punkty są przypisane do konta i nie można ich przenosić.

### Czy dostaję punkty na start?

Tak! Nowi użytkownicy otrzymują **10 punktów GRATIS** przy rejestracji.

### Jak anulować subskrypcję?

W panelu użytkownika (`/ui/account`) lub przez email na support@analytica.pl.

### Czy ceny zawierają VAT?

Podane ceny są cenami netto. Do cen doliczany jest VAT 23%.

### Jak działa Enterprise?

1. Wyślij zapytanie na enterprise@analytica.pl
2. Odbędziemy 30-min discovery call
3. Przygotujemy propozycję z wyceną
4. Po akceptacji - wdrożenie w 2-8 tygodni

---

## Podsumowanie cennika

| Model | Cena | Punkty | Cena/pkt | Dla kogo |
|-------|------|--------|----------|----------|
| **Pakiet 50** | 50 zł | 50 | 1.00 zł | Testowanie |
| **Pakiet 200** | 180 zł | 200 | 0.90 zł | Małe projekty |
| **Pakiet 500** | 400 zł | 500 | 0.80 zł | Średnie firmy |
| **Subskrypcja mies.** | 199 zł/mies. | 250/mies. | 0.80 zł | Regularne użycie |
| **Subskrypcja roczna** | 1 990 zł/rok | 3500/rok | 0.57 zł | Firmy |
| **Enterprise** | Indywidualnie | Custom | Custom | Korporacje |

---

## Linki

- [Architektura systemu](./ARCHITECTURE.md)
- [REST API](./API.md)
- [Moduły DSL](./MODULES.md)
- [Strona główna](../README.md)

---

*Ostatnia aktualizacja: 2025-01-01*
