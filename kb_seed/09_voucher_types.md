---
doc_id: KB-009
title: Katalog typów Voucherów i kodów
category: reference
language: pl
applies_to: [voucher_redemption, gift_recipient_confusion]
---

# Typy Voucherów

## 1. Voucher na konkretne przeżycie

- Format kodu: `[A-Z]{4}-[0-9]{6}` (np. `WPRZ-184220`).
- Powiązany z jednym przeżyciem rekomendowanym.
- Może być wymieniony na inne przeżycie (Gift Card behavior).
- 36 miesięcy ważności.

## 2. Gift Card (kwota)

- Format kodu: `GC-[0-9]{8}`.
- Reprezentuje kwotę w PLN, do wykorzystania na dowolne przeżycie z oferty.
- Powstaje też automatycznie po wygaśnięciu okresu realizacji Vouchera kategorii 1.
- 36 miesięcy od pierwotnego zakupu.

## 3. Voucher partnera B2B

| Partner | Prefix | Realizacja | Notatka |
|---|---|---|---|
| Multivoucher | `MUL-` | Strona partnera, redirect na wybór WP | Klient widzi WP brand |
| Poczta Polska | `PP-` | Wybór z mniejszego katalogu | Specjalne SLA |
| Allegro | `ALG-` | Realizacja przez Allegro Smart | Klient częściowo z innego ekosystemu |

## 4. Voucher korporacyjny

- Format: `CORP-[A-Z]{3}-[0-9]{6}`.
- Wystawiany dla firm, customizowany branding (czasami biały label).
- Odrębny URL: `[firma].wyjatkowyprezent.pl/rezerwacje`.
- Ważność wg umowy korporacyjnej (zwykle 12-24 mies.).

## 5. Karta upominkowa drukowana w punkcie

- Format: `STORE-[0-9]{10}`.
- Aktywacja przy zakupie w punkcie stacjonarnym.
- Realizacja online lub w punkcie.

## Statusy w CMS

| Status | Znaczenie | Akcja CS |
|---|---|---|
| `active` | aktywny, do realizacji | normalna obsługa |
| `reserved` | rezerwacja w toku | oczekiwanie na potwierdzenie dostawcy |
| `redeemed` | zrealizowany | nie podlega zwrotowi |
| `expired` | wygasły (>36 mies.) | patrz `05_expired_voucher.md` |
| `cancelled` | anulowany / zwrócony | sprawa zamknięta |
| `suspended` | tymczasowo zawieszony (problem partnera) | eskalacja do Partnerskiego |
| `disputed` | otwarty spór | eskalacja do Reklamacji |

## Obsługiwane języki CMS / WP

- PL — flagowy rynek, 100% wsparcie.
- LT, LV, EE, FI — w gestii odrębnych zespołów. CS PL nie obsługuje.

CS PL nie powinien obiecywać klientom przeżyć w innych krajach, jeśli klient pisze z innego rynku — eskalacja do działu odpowiedniego kraju.
