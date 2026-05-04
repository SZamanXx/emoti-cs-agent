---
doc_id: KB-006
title: SOP — zgubiony Voucher / kod nie działa
category: sop
language: pl
applies_to: [voucher_redemption, gift_recipient_confusion]
---

# Zgubiony Voucher / kod nie działa — SOP

## Krok 1: identyfikacja Vouchera w CMS

Zapytaj klienta o **co najmniej dwa** z poniższych:
- adres e-mail kupującego LUB obdarowanego;
- przybliżoną datę zakupu (miesiąc + rok wystarczy);
- nazwę przeżycia (jeśli pamięta);
- kwotę zakupu;
- imię i nazwisko kupującego.

Wyszukiwanie w CMS: endpoint `GET /vouchers?email=...&purchase_month=...`.

## Krok 2: weryfikacja właściciela

Duplikat / kod wysyłamy **tylko** na e-mail zarejestrowany przy zakupie lub potwierdzony jako adres obdarowanego. **Nigdy** na świeży, nieznany adres bez weryfikacji tożsamości.

Jeśli klient nie ma dostępu do oryginalnego e-maila → eskalacja do supervisora (potencjalne nadużycie / próba przejęcia Vouchera).

## Krok 3: status w CMS

Po znalezieniu rekordu sprawdź:

| `voucher.status` | Działanie |
|---|---|
| `active` | Wyślij duplikat na zweryfikowany e-mail. |
| `redeemed` | Poinformuj klienta, że Voucher został zrealizowany dnia X. Jeśli klient twierdzi, że to nie on — eskalacja, możliwe nadużycie. |
| `expired` | Patrz `05_expired_voucher.md`. |
| `cancelled` | Pełen kontekst w CMS — najczęściej zwrot zrealizowany, do operatora. |
| `suspended` | Eskalacja do działu Partnerskiego (problem po stronie partnera). |

## Krok 4: kod nie działa po wpisaniu na stronie

Zanim wyślesz odpowiedź, weryfikuj:

1. **Format kodu** — `[A-Z]{4}-[0-9]{6}`. Spacje, małe litery, cudzysłowy → odrzucane przez form.
2. **Status** w CMS (jak wyżej).
3. **Voucher partnera B2B** — np. multivoucher, Poczta Polska, GiftKarta. Prefix kodu inny (`MUL-`, `PP-`, `GK-`). Realizacja przez stronę partnera, nie WP.
4. **Voucher korporacyjny / rebrandowany** — może mieć osobny URL realizacji (`partner.wyjatkowyprezent.pl`).

## Standardowa pierwsza odpowiedź (template)

> Pani/Panie [imię],
>
> dziękuję za kontakt. Aby pomóc Pani/Panu jak najszybciej, proszę o krótkie potwierdzenie dwóch danych:
>
> 1. Adres e-mail, na który wysłany został Voucher (lub adres osoby kupującej).
> 2. Przybliżona data zakupu (miesiąc + rok).
>
> Po weryfikacji w naszym systemie wyślę duplikat / wyjaśnię status w ciągu 1 dnia roboczego.

## Audit / log

Każde wysłanie duplikatu loguje: `audit_log(action='voucher_duplicate_sent', operator_id, ticket_id, voucher_id, recipient_email, timestamp)`.
