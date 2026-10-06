"""
Deterministic quantity rules for every item row, keyed by section code.
No AI / text interpretation needed - this is pure lookup by field name.

Rule kinds:
  ("raw", field)              -> quantity = raw input field value
  ("raw_sum", [fields])       -> quantity = sum of the given raw fields
  ("const", value)            -> quantity is always a fixed constant
  ("formula", template)       -> quantity is an Excel formula. Use these
                                  placeholders inside template, they get
                                  substituted with real cell refs:
                                    {D:<code>}  -> D-column cell of that code's row
                                    {E:<code>}  -> E-column cell (price) of that row
                                    {I:<code>}  -> I-column cell (total) of that row
                                    {L:<field>} -> raw-input cell for that field
  ("always0_visible", None)   -> quantity 0, but row must never be auto-hidden
"""

MOTOR_CODES = ['12.065.2000','12.065.2010','12.065.2020','12.065.2030','12.065.2040','12.065.2050']

RULES = {
    '60.020.0090': ("formula", "IF(SUM(" + ",".join("{D:%s}"%c for c in MOTOR_CODES) + ")>0,2,0)"),
    '09.011.9030': ("raw", "היקף כולל"),
    '11.011.9660': ("raw", "מס' חדרים"),

    '12.011.0210': ("const", 0),
    '12.011.0270': ("raw_sum", ["שטח הזזה", "שטח הזזה+קבוע"]),
    '12.012.0100': ("const", 0),
    '12.011.1001': ("formula", "{L:שטח הזזה+קבוע}*{E:12.011.0270}+{L:שטח קיפ+קבוע}*{E:12.014.0660}"),
    '12.011.9000': ("raw", 'מס\' חלונות עד 2 מ"ר'),
    '12.011.9016': ("raw", 'מס\' חלונות מעל 2 מ"ר ועד 3 מ"ר'),
    '12.011.9017': ("raw", 'מספר חלונות מעל 3 מ"ר ועד 5 מ"ר'),

    '12.014.0400': ("const", 0),   # not in use currently
    '12.014.0650': ("const", 0),   # not in use currently
    '12.014.0660': ("raw_sum", ["שטח קיפ", "שטח קיפ+קבוע"]),

    '12.016.0600': ("const", 0),
    '12.016.0610': ("const", 0),

    '12.052.0020': ("const", 0),
    '12.052.0070': ("raw", "שטח ויטרינה"),
    '12.052.0080': ("const", 0),
    '12.052.0260': ("const", 0),

    '12.053.0200': ("raw", "שטח דלת ציר"),
    '12.053.0210': ("const", 0),
    '12.053.0450': ("const", 0),

    '12.061.9000': ("formula", "SUM({D:12.052.0020}:{D:12.052.0080_range_note})"),  # replaced below explicitly

    '12.065.1613': ("raw", "שטח תריסים לחלונות"),
    '12.065.1615': ("raw", "שטח תריסים לדלתות"),
    '12.065.1710': ("raw", "שטח תריסים לחלונות (אור)"),
    '12.065.1681': ("raw", "שטח תריסים לדלתות (אור)"),

    '12.065.2000': ("raw", "כמות מנוע עד 20"),
    '12.065.2010': ("raw", "כמות מנוע 20–30"),
    '12.065.2020': ("raw", "כמות מנוע 30–50"),
    '12.065.2030': ("raw", "כמות מנוע 50–70"),
    '12.065.2040': ("raw", "כמות מנוע 70–90"),
    '12.065.2050': ("raw", "כמות מנוע 90–120+"),

    '12.065.9000': ("raw", 'מס\' יחידות תריס לפירוק עד 2 מ"ר'),
    '12.065.9020': ("raw", 'סה"כ שטח תריס לפירוק מעל 2 מ"ר'),

    '12.065.9100': ("formula", "IF(({L:שטח תריסים לחלונות}+{L:שטח תריסים לדלתות}+{L:שטח תריסים לחלונות (אור)}+{L:שטח תריסים לדלתות (אור)})=0,0,{L:רוחב 0-100})"),
    '12.065.9110': ("formula", "IF(({L:שטח תריסים לחלונות}+{L:שטח תריסים לדלתות}+{L:שטח תריסים לחלונות (אור)}+{L:שטח תריסים לדלתות (אור)})=0,0,{L:רוחב 101-150})"),
    '12.065.0001': ("formula", "IF(({L:שטח תריסים לחלונות}+{L:שטח תריסים לדלתות}+{L:שטח תריסים לחלונות (אור)}+{L:שטח תריסים לדלתות (אור)})=0,0,{L:רוחב 151-200})"),
    '12.065.0002': ("formula", "IF(({L:שטח תריסים לחלונות}+{L:שטח תריסים לדלתות}+{L:שטח תריסים לחלונות (אור)}+{L:שטח תריסים לדלתות (אור)})=0,0,{L:רוחב 201-250})"),
    '12.065.0003': ("formula", "IF(({L:שטח תריסים לחלונות}+{L:שטח תריסים לדלתות}+{L:שטח תריסים לחלונות (אור)}+{L:שטח תריסים לדלתות (אור)})=0,0,{L:רוחב 251-300})"),
    '12.065.0004': ("formula", "IF(({L:שטח תריסים לחלונות}+{L:שטח תריסים לדלתות}+{L:שטח תריסים לחלונות (אור)}+{L:שטח תריסים לדלתות (אור)})=0,0,{L:רוחב 301-350})"),
    '12.065.0005': ("formula", "IF(({L:שטח תריסים לחלונות}+{L:שטח תריסים לדלתות}+{L:שטח תריסים לחלונות (אור)}+{L:שטח תריסים לדלתות (אור)})=0,0,{L:רוחב 351-400})"),
    '12.065.0006': ("formula", "IF(({L:שטח תריסים לחלונות}+{L:שטח תריסים לדלתות}+{L:שטח תריסים לחלונות (אור)}+{L:שטח תריסים לדלתות (אור)})=0,0,{L:רוחב 401-450})"),

    '12.067.9000': ("raw", "שטח רשת כולל"),
    '12.067.0200': ("const", 0),
    '12.067.0210': ("formula", "{D:12.067.9000}"),

    '12.068.1320': ("const", 0),   # default; exception orders overridden by caller
    '12.068.1216': ("formula", "-{D:12.068.1172}-{D:12.068.1004}-{D:12.068.1006}"),
    '12.068.1006': ("formula", "-({D:12.052.0080}+{D:12.051.0460}+{D:12.051.0470})"),
    '12.068.1172': ("formula", "-({D:12.012.0100}+{D:12.012.0110}+{D:12.011.0260}+{D:12.011.0265})"),
    '12.068.1004': ("formula", "-({D:12.052.0020}+{D:12.052.0070}+{D:12.052.0260}+{D:12.053.0200}+{D:12.053.0210}+{D:12.053.0450})"),  # 12.052.0080 excluded - its own default glass is 8mm, not 6mm
    '12.068.0902': ("const", 0),
    '12.068.1002': ("const", 0),

    '15.041.1210': ("const", 0),
    '15.041.4010': ("const", 0),

    '30.050.9010': ("formula", "{D:12.065.1611}+{D:12.065.1613}+{D:12.065.1615}+{D:12.065.1700}+{D:12.065.1710}+{D:12.065.1720}+{D:12.065.1730}+{D:12.065.1661}+{D:12.065.1671}+{D:12.065.1681}"),

    '60.010.0020': ("const", 3),
    '60.010.0010': ("formula", "{D:12.065.2050}*2+{D:12.065.2000}+{D:12.065.2010}+{D:12.065.2020}+{D:12.065.2030}+{D:12.065.2040}+{L:כמות טיפול בארגז}"),

    '60.030.0605': ("formula", "IF({L:קומה 0-3}>0,IF(SUM(" + ",".join("{D:%s}"%c for c in MOTOR_CODES) + ")>=5,2,1),0)"),
    '60.030.0634': ("formula", "IF({L:קומה 4-7}>0,IF(SUM(" + ",".join("{D:%s}"%c for c in MOTOR_CODES) + ")>=5,2,1),0)"),
    '60.030.0644': ("formula", "IF({L:קומה 7 ומעלה}>0,IF(SUM(" + ",".join("{D:%s}"%c for c in MOTOR_CODES) + ")>=5,2,1),0)"),

    '85.095.0950': ("raw", 'סה"כ טקסאונד'),

    '12.99.0001': ("always0_visible", None),
    '12.99.0002': ("always0_visible", None),

    '12.093.0022': ("formula",
        "SUM({I:12.011.0210}:{I:12.011.1001},{I:12.014.0400}:{I:12.014.0660},"
        "{I:12.016.0600}:{I:12.016.0610},{I:12.052.0020}:{I:12.052.0080},"
        "{I:12.053.0200}:{I:12.053.0450},{I:12.065.1613}:{I:12.065.1681},"
        "{I:12.067.0200}:{I:12.067.0210},{I:12.99.0001}:{I:12.99.0002})/0.85/1.05"),

    '60.020.0067': ("const", 0),   # only used for special "argazei trisim" orders
}

# Optional item, only relevant for orders with a special paint tint that
# goes beyond the base "P" shade. Default 0 for every order; set an
# explicit override (e.g. '=I13/0.85/1.05') for orders where it applies.
RULES['11.011.2000'] = ("const", 0)

# Optional item, only relevant for orders that need a curved fixed top +
# curved glass (rare, custom detail). Default 0 for every order.
RULES['12.99.1'] = ("const", 0)

# Special-callout electrician crew. Default 0 for every order.
RULES['60.020.0105'] = ("const", 0)

# Special-callout flooring crew. Default 0 for every order.
RULES['60.010.0120'] = ("const", 0)
RULES['60.010.0110'] = ("const", 0)

# New 2-panel sliding door/vitrina family (2 tracks). Default 0; assigned
# via per-element size-bracket logic (see element processing notes).
RULES['12.051.0460'] = ("const", 0)
RULES['12.051.0470'] = ("const", 0)

# New 3-panel window size bracket, 5+6+6mm, 2-3 m2. Default 0; assigned via
# per-element size-bracket logic.
RULES['12.012.0110'] = ("const", 0)
RULES['12.011.0260'] = ("const", 0)
RULES['12.011.0265'] = ("const", 0)
RULES['12.011.0285'] = ("const", 0)
RULES['12.011.0275'] = ("const", 0)
RULES['12.011.0280'] = ("const", 0)  # NOTE: glass spec is 6+10+10, NOT the usual 6+10+8 target -
# if this bracket is ever used, ask whether it needs its own glass offset code before finalizing.
RULES['12.012.0120'] = ("const", 0)
RULES['12.012.0130'] = ("const", 0)
RULES['12.012.0560'] = ("const", 0)

# Shutter brackets assigned via per-element bracket assignment only -
# these were added to CANONICAL_ROWS but the RULES entries were missed,
# which left their D-column truly blank (not even 0) in the order sheet -
# causing #VALUE! errors when a combined ריכוז tried to sum across orders.
RULES['12.065.1611'] = ("const", 0)
RULES['12.065.1700'] = ("const", 0)
RULES['12.065.1720'] = ("const", 0)
RULES['12.065.1730'] = ("const", 0)
RULES['12.065.1661'] = ("const", 0)
RULES['12.065.1671'] = ("const", 0)

# fix 12.061.9000: sum of the 6 door/vitrina codes explicitly
RULES['12.061.9000'] = ("formula",
    "{D:12.052.0020}+{D:12.052.0070}+{D:12.052.0080}+{D:12.052.0260}+{D:12.053.0200}+{D:12.053.0210}+{D:12.053.0450}")

# All raw field names the schema knows about (used to build the input block
# with every known field, even if a given order's file doesn't include it -
# missing ones default to 0).
ALL_RAW_FIELDS = [
    "מס' חדרים", "היקף כולל", "שטח ויטרינה", "שטח קיפ+קבוע", "שטח רשת כולל",
    'מס\' חלונות עד 2 מ"ר', 'מס\' חלונות מעל 2 מ"ר ועד 3 מ"ר', 'מספר חלונות מעל 3 מ"ר ועד 5 מ"ר',
    "רוחב 0-100", "רוחב 101-150", "רוחב 151-200", "רוחב 201-250",
    "רוחב 251-300", "רוחב 301-350", "רוחב 351-400", "רוחב 401-450",
    "קומה 0-3", "קומה 4-7", "קומה 7 ומעלה",
    'שטח תריסים לחלונות (אור)', 'שטח תריסים לדלתות (אור)',
    "כמות מנוע עד 20", "כמות מנוע 20–30", "כמות מנוע 30–50",
    "כמות מנוע 50–70", "כמות מנוע 70–90", "כמות מנוע 90–120+",
    "כמות טיפול בארגז", 'סה"כ טקסאונד',
    "שטח הזזה", "שטח הזזה+קבוע", "שטח קיפ", "שטח חלון ציר",
    "שטח תריסים לחלונות", "שטח תריסים לדלתות", "שטח דלת ציר",
    'מס\' יחידות תריס לפירוק עד 2 מ"ר', 'סה"כ שטח תריס לפירוק מעל 2 מ"ר',
    'קיזוז זכוכית לארגז תריס',
]
