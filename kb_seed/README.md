# KB seed — Wyjątkowy Prezent CS knowledge base (demo)

Wymyślony, ale realistyczny zestaw dokumentów do testowania pipeline'u retrieval + drafter. Po wdrożeniu produkcyjnym zostaje zastąpiony rzeczywistymi materiałami od działu CS Emoti / WP.

## Zawartość

| Doc ID | Plik | Typ | Pokrywa kategorie |
|---|---|---|---|
| KB-001 | `01_regulamin_voucher.md` | policy | redemption, expired, refund |
| KB-002 | `02_faq_realizacja.md` | faq | redemption, gift_recipient |
| KB-003 | `03_refund_policy.md` | policy | refund (NO_DRAFT) |
| KB-004 | `04_supplier_dispute.md` | sop | supplier_dispute, refund |
| KB-005 | `05_expired_voucher.md` | sop | expired, refund |
| KB-006 | `06_lost_code_sop.md` | sop | redemption, gift_recipient |
| KB-007 | `07_brand_voice.md` | voice | all (cached prefix) |
| KB-008 | `08_response_templates.md` | templates | redemption, gift_recipient, expired |
| KB-009 | `09_voucher_types.md` | reference | redemption, gift_recipient |
| KB-010 | `10_cms_endpoints.md` | technical | internal |

## Źródła referencyjne (real-world grounding)

- regulamin Wyjątkowy Prezent (publiczna wersja na wyjatkowyprezent.pl/regulamin/) — ważność 36 mies., zwrot 101 dni, reklamacje 14 dni SLA, e-mail `reklamacje@`.
- FAQ realizacji rezerwacji (wyjatkowyprezent.pl/jak-dokonac-rezerwacji) — minimum 5 dni roboczych, max 28 dni przed końcem ważności, format kodu, kanały kontaktu.

## Sample data

`../sample_data/tickets.jsonl` — 15 ticketów testowych pokrywających 5 kategorii z briefa + edge cases:
- T-009: indirect prompt injection w mailu „od dostawcy".
- T-013: wrażliwa sytuacja (zmarły kupujący).
- T-014: repeat complaint (>3 zgłoszenia).
- T-015: out-of-scope (inny rynek).
- T-004: groźba UOKiK + emocjonalna treść.

## Mapowanie testów end-to-end

Każdy ticket ma pole `expected_category` i `expected_action`. Skrypt `seed_tickets.py` ładuje je do bazy, a eval harness porównuje:

- output classifier vs `expected_category`,
- decyzję routera (`draft` / `escalate` / `quarantine`) vs `expected_action`,
- accept-without-edit rate na drafterze (jeśli action == draft).

## Refresh policy

W realu te dokumenty zmieniałyby się co kwartał (regulamin), miesiąc (FAQ, templates), na bieżąco (supplier list). Re-embedding całej KB to <0.05 PLN przy `text-embedding-3-small` — nie warto cache'ować, lepiej rebuild on each upload.
