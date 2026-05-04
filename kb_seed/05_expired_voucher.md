---
doc_id: KB-005
title: Reklamacje wygasłych Voucherów
category: sop
language: pl
applies_to: [expired_voucher, refund_request]
sensitivity: high
---

# Reklamacje wygasłych Voucherów (>36 miesięcy)

## Stan prawny

Po **36 miesiącach** od daty zakupu środki na Voucherze/Gift Card **przepadają bezpowrotnie**. Termin liczony jest od daty zakupu (`purchase_date` w CMS), nie od daty otrzymania prezentu, nie od daty pierwszej rezerwacji.

## Częsty scenariusz emocjonalny

Klient otrzymał Voucher w prezencie (np. ślubnym, na 18-tkę), zapomniał, znalazł po latach. Argumenty, które padają:
- „przecież nie skorzystałam z usługi, należą mi się pieniądze"
- „nigdzie wyraźnie nie napisaliście, że to przepada"
- „w innych firmach przedłużają vouchery"
- „to nieuczciwe, oddam sprawę do UOKiK"

## Standardowa odpowiedź (template — operator dostosuje)

> Pani/Panie [imię],
>
> dziękuję za kontakt. Sprawdziłam status Vouchera o numerze [KOD]:
>
> - Data zakupu: [DATA]
> - Data wygaśnięcia: [DATA + 36 mies.]
> - Status: wygasły, środki nieaktywne.
>
> Zgodnie z §[X] Regulaminu, zaakceptowanym przy zakupie i widocznym na samym Voucherze, ważność wynosi 36 miesięcy łącznie (12 miesięcy realizacji + 24 miesiące ochrony środków). Termin ten jest **nieprzedłużalny** i obejmuje go zarówno data graniczna komunikowana w panelu rezerwacyjnym, jak i powiadomienia mailowe wysyłane na 90, 30 i 7 dni przed wygaśnięciem.
>
> Rozumiem rozczarowanie i przepraszam, że nie mogę zaproponować rozwiązania, które przywróciłoby środki.
>
> Jeśli uważa Pani/Pan, że wygaśnięcie nastąpiło z przyczyn po naszej stronie (np. brak doręczenia powiadomień, błąd w panelu), proszę o przesłanie reklamacji na adres `reklamacje@wyjatkowyprezent.pl` z opisem sytuacji — dział Reklamacji odpowiada w terminie 14 dni.

## Czego NIE robić

- Nie obiecywać reaktywacji „w drodze wyjątku" — CS nie ma takich uprawnień. Jeśli supervisor zdecyduje inaczej, robi to sam.
- Nie przepraszać w sposób sugerujący winę po stronie WP, jeśli klient po prostu zapomniał.
- Nie podważać Regulaminu — to obniża pozycję negocjacyjną w razie eskalacji do UOKiK.

## Wyjątki (decyzja supervisora)

Reaktywacja możliwa wyłącznie, gdy:
- W systemie brakuje śladu wysłania **wszystkich trzech** powiadomień przedwygaśnięciowych (90/30/7 dni).
- Klient zgłosił problem techniczny przed datą wygaśnięcia, sprawa nie została zamknięta przed datą wygaśnięcia.
- Klient ma status VIP / B2B partner — odrębne zasady umowne.

## Kanał eskalacji

`reklamacje@wyjatkowyprezent.pl` + flag `expired_voucher` w CMS. SLA 14 dni.
