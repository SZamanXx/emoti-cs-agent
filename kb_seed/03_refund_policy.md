---
doc_id: KB-003
title: Polityka zwrotów i reklamacji finansowych
category: policy
language: pl
applies_to: [refund_request]
sensitivity: high
ai_draft_allowed: false
---

# Polityka zwrotów

> ⚠️ **Reguła systemowa:** AI nigdy nie generuje pełnej odpowiedzi w kategorii `refund_request`. Klasyfikator przekazuje takie zgłoszenia bezpośrednio do operatora człowieka z prefillem kontekstu z CMS. Ten dokument służy operatorowi jako referencja.

## 1. Zwrot bezwarunkowy (101 dni)

- **Warunek:** zakup nie starszy niż 101 dni, Voucher **niezrealizowany** i **nieobjęty rezerwacją**.
- Środki wracają **na konto kupującego** (nie obdarowanego).
- Czas realizacji: do 14 dni roboczych od potwierdzenia.
- Operator weryfikuje w CMS: `voucher.status` musi być `active`, `voucher.purchase_date` ≤ 101 dni.

## 2. Zwrot po 101 dniach — tryb reklamacyjny

- Wymaga **uzasadnionej podstawy prawnej**: niezgodność z umową, brak realizacji u dostawcy, błąd po stronie operatora.
- Decyzję podejmuje **dział Reklamacji**, nie CS.
- SLA: 14 dni kalendarzowych na odpowiedź pisemną.
- Operator CS przekazuje sprawę z pełnym kontekstem i kopią korespondencji.

## 3. Sytuacje, gdy zwrot jest należny po 101 dniach

| Sytuacja | Tryb |
|---|---|
| Dostawca trwale zaprzestał działalności i nie ma równoważnej oferty | zwrot pełny |
| Voucher posiadał wadę uniemożliwiającą realizację (błędny kod, brak miejsc w 100% lokalizacji) | zwrot pełny |
| Klient zgłosił reklamację jakości realizacji, uznana | zwrot częściowy lub Gift Card |
| Klient nie wykorzystał Vouchera w terminie z winy własnej | **brak podstaw do zwrotu** |

## 4. Czego operator NIE może obiecać

- Pełnego zwrotu „w drodze wyjątku" bez decyzji działu Reklamacji.
- Wypłaty środków z wygasłego Vouchera (>36 mies.).
- Zwrotu różnicy przy wymianie na tańsze przeżycie.
- Konkretnego terminu zwrotu szybszego niż SLA 14 dni.

## 5. Sygnały eskalacji do supervisora (NATYCHMIAST)

- Klient grozi UOKiK / Rzecznikiem Konsumentów / sądem.
- Kwota >2000 PLN.
- Klient zgłasza wielokrotnie tę samą sprawę (>3 ticketów w 30 dni).
- Podejrzenie nadużycia (np. wielokrotne żądania zwrotu z różnych adresów).

## 6. Standard pisemnej odpowiedzi (operator pisze ręcznie)

Każda odpowiedź na refund_request zawiera:
1. Potwierdzenie odbioru zgłoszenia + numer sprawy.
2. Identyfikację Vouchera (kod, data zakupu, status).
3. Podstawę prawną decyzji (101 dni / poza terminem / ścieżka reklamacyjna).
4. Konkretny termin następnego kroku (max 14 dni).
5. Wskazanie kanału eskalacji (`reklamacje@`).

**Bez pustych obietnic. Bez przepraszania bez kontekstu. Bez konkretnych kwot bez weryfikacji w CMS.**
