---
doc_id: KB-010
title: Kontrakt z CMS (mock)
category: technical
language: pl
applies_to: [internal]
note: "Demo / test mock. Realny CMS Emoti — kontrakt do uzgodnienia z Krystianem (CTO) w tygodniu 1."
---

# CMS — endpoints używane przez agenta (mock)

Wszystkie endpointy są **read-only** dla LLM. Akcje stanowiące (refund, suspend, extend) wymagają operatora + 2FA.

## GET /vouchers/{code}

Zwraca pełen rekord vouchera.

```json
{
  "code": "WPRZ-184220",
  "type": "experience_voucher",
  "status": "active",
  "purchase_date": "2024-08-12",
  "expiry_date": "2027-08-12",
  "amount_pln": 449.00,
  "experience": {
    "id": "exp-1923",
    "name": "Weekend SPA dla dwojga",
    "supplier_id": "sup-77"
  },
  "buyer_email": "anna.k@example.com",
  "recipient_email": null,
  "channel": "online_b2c"
}
```

## GET /vouchers?email={e}&purchase_month={YYYY-MM}

Wyszukiwanie po adresie e-mail i miesiącu zakupu (case zgubionego kodu).

## GET /reservations?voucher_code={code}

Lista rezerwacji powiązanych z voucherem + statusy potwierdzeń od dostawcy.

## GET /suppliers/{id}

Status dostawcy (`active` / `suspended` / `terminated`) + alternatywne lokalizacje dla danego przeżycia.

## GET /tickets/{id}/history

Historia zgłoszeń klienta — anti-abuse signal (klient z >3 ticketami w 30 dni → flag `repeat_complaint` → eskalacja).

## POST /audit_log (system → CMS)

Każda akcja agenta lub operatora trafia do audit log:

```json
{
  "ticket_id": "...",
  "voucher_code": "...",
  "action": "draft_generated|draft_accepted|draft_rejected|draft_edited|sent|escalated",
  "operator_id": "...",
  "model": "claude-sonnet-4-6",
  "prompt_version": "drafter-v3.2",
  "tokens_in": 1820,
  "tokens_out": 264,
  "cost_usd": 0.0091,
  "ts": "2026-05-04T11:23:00Z"
}
```

## Zakładane composite endpointy (do uzgodnienia)

- `GET /context/{voucher_code}` → voucher + reservations + supplier + last 5 tickets w jednym wywołaniu. Bez tego: 4 sekwencyjne calle = ~600 ms latency, niedopuszczalne. **#1 architectural risk.**
