> הערה: טבלאות הייחוס. הלוגיקה בפועל נמצאת ב-`engine/suggest.py`, `engine/rules.py` ו-`engine/order_template.py` (מקור האמת). אזכורים של bracket_assignment.py / glass_offset.py / address_rules.py מתייחסים לאפליקציית ה-Streamlit, וכאן הם ממומשים ב-suggest.py.

# RULEBOOK.md — reference data for nta-billing

Companion to SKILL.md. This is the data; SKILL.md is the process. Prices and
descriptions here reflect `order_template.py` as of the last update — if
they ever disagree, the `.py` files are the source of truth (this file may
lag a live fix by one turn; always re-check the actual code for a number
that matters).

## Chapters (must-have prefix list)

`01, 05, 09, 11, 12, 15, 22, 30, 60, 85` — every section code's prefix must
be one of these. A code with an unlisted prefix silently drops out of every
summary with no error. When a new chapter appears (this happened once with
"22"), add it here **and** to `CHAPTERS` in `generate.py` before anything
else.

## Bracket families (per-element, via bracket_assignment.py)

All families use the fallback rule: area ≤ lowest bracket's own max → lowest
bracket, real area. Area > highest bracket's max → highest bracket, real
area. Never invent a code for a real gap — ask and get the actual price.

### חלון הזזה, 2 מסלולים — 12.011

| קוד | זיגוג | טווח (מ"ר) | מחיר |
|---|---|---|---:|
| 12.011.0260 | 5+6+6 | 0.6–1.0 | 2,440 |
| 12.011.0265 | 5+6+6 | 1.0–2.0 | 2,120 |
| 12.011.0270 | 6+10+8 | 2.0–3.0 | 1,980 |
| 12.011.0275 | 6+10+8 | 3.0–4.0 | 1,760 |
| 12.011.0280 | **6+10+10** (no glass bucket yet — ask before using) | 4.0–5.0 | 1,630 |
| 12.011.0285 | 6+10+8 | 5.0–6.0 | 1,490 |

`12.011.0210` (5+6+6, 1.0–2.0, ₪1,760, קליל 7000) exists separately and is
**not** part of the 9000-line bracket ladder above — only use it if the
order specifies the 7000 profile explicitly.

### חלון הזזה, 3 מסלולים — 12.012

| קוד | זיגוג | טווח (מ"ר) | מחיר |
|---|---|---|---:|
| 12.012.0100 | 5+6+6 | 1.0–2.0 | 2,210 |
| 12.012.0110 | 5+6+6 | 2.0–3.0 | 2,110 |
| 12.012.0120 | 6+10+8 | 3.0–5.0 | 2,060 |
| 12.012.0130 | 6+10+8 | 5.0–7.0 | 1,970 |

### תוספת 15% לחלק "קבוע" — 12.011.1001 (₪ per m², price=0.15)

Only for **הזזה+קבוע** (not קיפ+קבוע/דרייקיפ+קבוע — those use 12.016.06xx
instead, see below). Quantity = weighted sum, `Σ(area × bracket_price)`
over every הזזה+קבוע element, using whichever bracket each element's area
landed in.

### דלת/ויטרינה הזזה, 2 מסלולים — 12.051

| קוד | זיגוג | טווח (מ"ר) | מחיר |
|---|---|---|---:|
| 12.051.0460 | 8mm | 4.0–6.0 | 1,630 |
| 12.051.0470 | 8mm | 6.0–8.0 | 1,580 |

### דלת/ויטרינה הזזה, 3 מסלולים — 12.052

| קוד | פרופיל | זיגוג | טווח (מ"ר) | מחיר |
|---|---|---|---|---:|
| 12.052.0020 | קליל 7000 | 6mm | 6.0–8.0 | 1,760 |
| 12.052.0070 | קליל 9000 | 6mm | 6.0–8.0 | 1,850 |
| 12.052.0260 | קליל בלגי 7300 | 6mm | 6.0–8.0 | 2,101 |
| 12.052.0080 | קליל 9000 | **8mm** | 8.0–10.0 | 1,680 |

0020 vs 0070 vs 0260 all cover the **same** 6.0–8.0 bracket and differ only
by product line — area alone can't choose between them. Default to 0070
(9000 line) unless the order specifies a different profile (0260's exact
profile, "קליל בלגי 7300", was given explicitly in one real order — ask
when unsure, don't assume).

### קיפ / דרייקיפ — 12.014.0660 (single code, both names map here)

Minimum **0.6 m² per unit**, applied before summing:
`Σ(count × max(0.6, unit_area))`.

### קיפ+קבוע / דרייקיפ+קבוע — always ask, never automatic

Get the split (same width, height splits into two parts). קיפ part →
12.014.0660 as above. קבוע part → counted in **units**, bracket:

| קוד | טווח (מ"ר, שטח יחידה) |
|---|---|
| 12.016.0600 | 0.6–1.0 |
| 12.016.0610 | 1.0–2.0 |

No 15% addition for this קבוע part.

### תריס רגיל (no window/vitrina split) — 12.065.16xx

| קוד | טווח (מ"ר) | מחיר |
|---|---|---:|
| 12.065.1611 | 0.6–1.0 | 910 |
| 12.065.1613 | 1.0–3.0 | 717 |
| 12.065.1615 | 3.0–6.0 (and above) | 582 |

### תריס אור — לחלונות (הזזה/הזזה+קבוע/קיפ/קיפ+קבוע)

| קוד | טווח (מ"ר) | מחיר |
|---|---|---:|
| 12.065.1700 | 0.6–1.0 | 1,120 |
| 12.065.1710 | 1.0–3.0 | 800 |
| 12.065.1720 | 3.0–6.0 | 880 |
| 12.065.1730 | 6.0–8.5 (and above) | 840 |

### תריס אור — לויטרינה/דלת ציר

| קוד | טווח (מ"ר) | מחיר |
|---|---|---:|
| 12.065.1661 | 0.6–1.0 | 1,840 |
| 12.065.1671 | 1.0–3.0 | 1,730 |
| 12.065.1681 | 3.0–6.0 (and above) | 1,440 |

**Price rule for all shutter families above:** the catalog shows two
tiers ("עד 20/25/30" vs "מעל 20/25/30") — **always use "מעל"**, regardless
of actual quantity. Confirmed explicitly, no exception known.

### מנוע חשמלי לתריס — 12.065.2000–2050

Six weight brackets, driven directly by six raw fields (כמות מנוע עד
20/20–30/30–50/50–70/70–90/90–120+). No bracket-assignment logic needed —
these are literal 1:1 field mappings.

### פירוק תריסים — 12.065.9000 (units) / 12.065.9020 (area)

Driven by two raw fields: `מס' יחידות תריס לפירוק עד 2 מ"ר` (units) and
`סה"כ שטח תריס לפירוק מעל 2 מ"ר` (area). **Both must be 0 if the order has
no shutter area at all**, regardless of what the ARGZ width fields say —
see below.

### פירוק ארגז תריס — 12.065.9100 / 9110 / 0001–0006 (8 width brackets)

Conditioned on total shutter area (regular + light, windows + doors) being
nonzero. If it's 0, all 8 codes are 0 even if the width fields themselves
have values.

## Glass offset buckets (glass_offset.py)

Default target: `6+10+8` (code `12.068.1216`).

| Bucket | Offset code | Members |
|---|---|---|
| 5+6+6 | 12.068.1172 | 12.012.0100, 12.012.0110, 12.011.0260, 12.011.0265 |
| 6mm | 12.068.1004 | 12.052.0020, 12.052.0070, 12.052.0260, 12.053.0200, 12.053.0210, 12.053.0450 |
| 8mm | 12.068.1006 | 12.052.0080 |
| 6+10+8 (target) | 12.068.1216 | 12.011.0270, 12.011.0275, 12.011.0285, 12.012.0120, 12.012.0130, 12.051.0460, 12.051.0470, 12.014.0660 |
| 5+0.76+5 (an exception target, not a default bucket) | 12.068.1320 | — |
| 6+10+10 | **no bucket yet** | 12.011.0280 — ask before using |

Rule: every bucket except the order's actual target gets offset (negated);
the sum of all offsets becomes the positive value in the target code. For a
normal order that's just "everything except 6+10+8 gets offset, 6+10+8
collects the total." For an exception order (say, target = 5+0.76+5),
**every** bucket including 6+10+8 itself gets offset, and 12.068.1320
collects the whole total. Always run `verify_balance()`.

`12.052.0080` (8mm) was once wrongly bucketed with the 6mm group — a real,
fixed bug. `12.052.0260` (also 6mm, added later) was correctly added to the
6mm bucket from the start.

## Address rules (address_rules.py)

| Address | Shutter type | Rotating handles |
|---|---|---|
| שולמית אלוני 15 | light (אור) | no |
| משה רינת 4 | light | no |
| משה רינת 10 | light | no |
| מנחם בגין 40 | light | no |
| מנחם בגין 50 | light | no |
| מנחם בגין 52 | light | no |
| משה רינת 2 | regular | **yes** |
| מנחם בגין 48 | regular | **yes** |

Unrecognized address → stop and ask, don't guess. When handles apply:
12.99.0002 = total window-type element count, 12.99.0001 = vitrina count
(both always displayed even at 0, never hidden).

## Other section rules worth remembering

- **09.011.9030** (טיח) — direct from raw field `היקף כולל`.
- **11.011.9660** (צבע לחדר) — direct from raw field `מס' חדרים`.
- **11.011.2000** (תוספת P) — override only, formula `=I<row of
  11.011.9660>/0.85/1.05` — **look up the row fresh in the just-built file**,
  never reuse a row number from memory.
- **12.093.0022** (6% Fine Iron) — sums a specific closed list of I-values,
  divided by 0.85/1.05. Excludes demolition codes, glass codes, and **motor**
  codes (12.065.2000–2050) — including motors here once overcharged an order
  by ~₪460.
- **60.020.0090** (חשמלאי מוסמך) — auto: 2 if any motor field >0, else 0.
- **60.010.0020** (פועל בנין פשוט) — always 3, **except** special orders
  (ארגזי תריס בלבד / "השלמות") — ask, then override to 0 if not relevant.
- **60.010.0010** (פועל בנין מקצועי) — `(מנוע 90–120+ ×2) + Σ(other 5 motor
  fields) + כמות טיפול בארגז`. "טיפול בארגז לויטרינה = ×2" is a **per-order
  override only**, never a global rule change.
- **60.030.0605/0634/0644** (מנוף by floor) — `IF(floor flag, IF(SUM(6 motor
  fields) >= 5, 2, 1), 0)`. Threshold is `>=5`, confirmed, not `>5`.
- **60.020.0067 / 60.020.0105 / 60.010.0120** — special-callout crews
  (aluminum ₪3,400 / electricians ₪3,500 / flooring ₪3,650), all default 0,
  override-only.
- **85.095.0950** (טקסאונד) — direct from raw field `סה"כ טקסאונד`.

## Special order types

- **ארגזי תריס בלבד** — only 60.020.0067 (+ טקסאונד if relevant). Ask about
  and likely zero 60.010.0020.
- **"השלמות"** — separate order, number `0000`, no raw data, no address,
  overrides only (team cancellations etc).
- **Glass exception (e.g. 5+0.76+5)** — must be stated explicitly per order;
  see glass_offset.py section above.

## Real bugs already found and fixed (don't reintroduce)

1. **Missing chapter prefix ("22")** silently dropped ~₪12,000 from a real
   account. Always keep `CHAPTERS` current when a new prefix appears.
2. **Crane threshold** was `>5`, corrected to `>=5`.
3. **Global rule change instead of per-order override** — "טיפול בארגז ×2
   for vitrina" was mistakenly written into the global rule once, silently
   changing 6 orders. Always scope a one-off correction as an override.
4. **Verbatim descriptions reverted to shortened versions** — happened
   twice, both times after an environment reset restored a stale backup.
   Always diff descriptions against the true source price-list file if
   there's any doubt, and re-save the backup after fixing.
5. **Locked-order data loss** — a "regenerate all orders" loop once
   overwrote a hand-edited, locked order because the loop didn't check
   `order.get("locked")`. Always check.
6. **Hardcoded row numbers in override formulas** (`=-D69-D70` style) broke
   silently once the template grew and row numbers shifted. Always look up
   the current row from the file you just built.
7. **12.052.0080 wrongly bucketed as 6mm glass** instead of its own 8mm —
   fixed by adding a dedicated `12.068.1006` bucket.
8. **Six shutter section codes added to `order_template.py` without a
   matching `RULES` entry** (12.065.1611/1700/1720/1730/1661/1671) — left
   their D-column truly blank (not 0) in single-order files, which looked
   fine until a combined multi-order ריכוז's cross-order "+"-chain summary
   formulas hit the blank cell and threw `#VALUE!`. Fixed by adding
   `("const", 0)` for all six. **Lesson: every code added to
   CANONICAL_ROWS needs a RULES entry the same turn, even if it's only ever
   set via override** — a missing rule is invisible in a single order and
   only surfaces once orders are combined.
9. **`read_raw.py` field-matching only tried `שטח `/`מס' `/`מספר `
   prefixes, never `כמות `** — a column named exactly `טיפול בארגז` (no
   prefix) or `מנוע 20–30` would silently show as unmatched even though
   `כמות טיפול בארגז` / `כמות מנוע 20–30` are canonical fields. Found while
   building the separate local-app version; the same fix applies here if
   ever hit.
10. **`שטח יחידה` ≠ `רוחב × גובה`** for shutter-bearing elements — QuantCalc
    subtracts 30cm from the height for the window-price calc only, not for
    the shutter's own area. Never recompute area from width/height; always
    use the given unit-area column.
