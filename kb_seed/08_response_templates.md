---
doc_id: KB-008
title: Szablony odpowiedzi (top 10 use-cases)
category: templates
language: pl
applies_to: [voucher_redemption, gift_recipient_confusion, expired_voucher]
note: "Templates używane bezpośrednio (bez LLM) gdy classifier confidence > 0.92 i intent dokładnie pasuje."
---

# Szablony top 10 — używane przez classifier-fast-path

## T-001 | Pytanie o ważność Vouchera

> Pani/Panie [imię],
>
> dziękuję za wiadomość. Voucher [KOD] jest ważny do **[DATA_WAZNOSCI]**, czyli **[DNI_DO_KONCA]** dni od dziś. Przypomnę, że rezerwacja musi być złożona minimum 5 dni roboczych przed datą realizacji i minimum 28 dni przed końcem ważności Vouchera.
>
> W razie pytań proszę o kontakt.

## T-002 | Jak zarezerwować

> Pani/Panie [imię],
>
> rezerwacja przebiega w trzech krokach:
>
> 1. Wejdź na: `wyjatkowyprezent.pl/rezerwacje`
> 2. Wpisz kod rezerwacji **[KOD]** i adres e-mail kontaktowy.
> 3. Wybierz lokalizację oraz dwie alternatywne daty.
>
> Dostawca potwierdzi rezerwację w ciągu maksymalnie 5 dni roboczych. W razie braku miejsc w wybranej lokalizacji można zmienić ją w panelu lub wymienić Voucher na inne przeżycie.

## T-003 | Wymiana na inne przeżycie

> Pani/Panie [imię],
>
> tak, Voucher [KOD] można w każdej chwili wymienić na inne przeżycie z aktualnej oferty:
>
> 1. `wyjatkowyprezent.pl/rezerwacje` → kod + e-mail.
> 2. Zakładka „Wymień przeżycie".
> 3. Wybór nowego przeżycia. Jeśli wybrane jest droższe — dopłata, jeśli tańsze — różnica nie podlega zwrotowi.
>
> Nowe przeżycie zachowuje datę ważności pierwotnego Vouchera ([DATA_WAZNOSCI]).

## T-004 | Brak terminów u danego dostawcy

> Pani/Panie [imię],
>
> przykro mi, że wybrana lokalizacja nie potwierdziła terminów. Proszę o jeden z trzech kroków:
>
> - Wybór innej lokalizacji w panelu rezerwacji (lista dostępna po podaniu kodu).
> - Wymiana Vouchera na inne przeżycie.
> - Odpowiedź na ten e-mail z preferowanym terminem — sprawdzę ręcznie u dostawcy.

## T-005 | Voucher otrzymany w prezencie — pierwsze kroki

> Pani/Panie [imię],
>
> super, że trafił do Pani/Pana Voucher Wyjątkowy Prezent! Trzy rzeczy do startu:
>
> 1. Na Voucherze widoczny jest **kod rezerwacji** (4 litery + 6 cyfr).
> 2. Wchodzi Pani/Pan na `wyjatkowyprezent.pl/rezerwacje`, wpisuje kod i swój e-mail.
> 3. Wybiera Pani/Pan lokalizację i dwie alternatywne daty (minimum 5 dni roboczych w przód).
>
> Voucher jest ważny przez 36 miesięcy od daty zakupu. Można też wymienić przeżycie na inne z naszej oferty.

## T-006 | Wygasły Voucher (krótka wersja)

> Pani/Panie [imię],
>
> sprawdziłam Voucher [KOD]. Niestety wygasł dnia [DATA_WYGASNIECIA] (36 miesięcy od zakupu, zgodnie z §[X] Regulaminu).
>
> Rozumiem rozczarowanie. Jeśli uważa Pani/Pan, że doszło do tego z przyczyn po naszej stronie, proszę o reklamację: `reklamacje@wyjatkowyprezent.pl` (odpowiedź do 14 dni).

## T-007 | Kod nie działa — prośba o weryfikację

> Pani/Panie [imię],
>
> aby sprawdzić Voucher, proszę o:
>
> 1. Adres e-mail przy zakupie (kupującego lub obdarowanego).
> 2. Przybliżoną datę zakupu (miesiąc + rok).
>
> Po weryfikacji wracam z odpowiedzią w ciągu 1 dnia roboczego.

## T-008 | Refund — pierwszy kontakt (operator wybiera ręcznie)

(Patrz `03_refund_policy.md` §6 — operator pisze ręcznie, ten szablon to placeholder.)

## T-009 | Spór z dostawcą — pierwsza odpowiedź

> Pani/Panie [imię],
>
> przykro mi, że doświadczenie nie spełniło oczekiwań. Aby przygotować pełne wyjaśnienie sprawy z [NAZWA_DOSTAWCY], proszę o:
>
> - krótki opis przebiegu wizyty (data, godzina, kto Panią/Pana obsługiwał);
> - załączniki: zdjęcia / korespondencja / paragony, jeśli posiada.
>
> Numer sprawy: **[TICKET_ID]**. Skontaktuję się z dostawcą w ciągu 5 dni roboczych i wrócę z propozycją rozwiązania w ciągu 14 dni.

## T-010 | Potwierdzenie zwrotu w 101 dniach

> Pani/Panie [imię],
>
> potwierdzam przyjęcie zgłoszenia zwrotu Vouchera [KOD]. Środki w wysokości **[KWOTA]** zostaną zwrócone na konto kupującego ([SPOSOB_PLATNOSCI]) w ciągu **14 dni roboczych**.
>
> Numer sprawy: [TICKET_ID]. W razie pytań proszę odpowiedzieć na ten e-mail.
