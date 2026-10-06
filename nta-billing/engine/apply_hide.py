import openpyxl
from order_template import CANONICAL_ROWS

ALWAYS_SHOW_CODES = {'12.99.0001', '12.99.0002'}

def build_row_layout():
    """Re-derive code->row and header->children_codes from CANONICAL_ROWS,
    the same way generate.py laid rows out (row 7 = first item, blank code = spacer)."""
    # 30.050.9010 (curtains chapter) has no dedicated header row of its own in
    # this BOQ - it just happens to sit right after the "15 - מיזוג אוויר"
    # block. It must NOT be treated as a child of that unrelated chapter.
    STANDALONE_CODES = {"30.050.9010"}

    code_to_row = {}
    r = 7
    header_children = {}
    stack = []  # list of (depth, code)
    for code, desc, unit, price in CANONICAL_ROWS:
        if code is None:
            r += 1
            continue
        code_to_row[code] = r
        is_header = (price == "")
        depth = len(code.split("."))
        if code in STANDALONE_CODES:
            stack = []  # not a child of any currently-open header
            r += 1
            continue
        if is_header:
            while stack and stack[-1][0] >= depth:
                stack.pop()
            header_children[code] = []
            stack.append((depth, code))
        else:
            for _, h in stack:
                header_children[h].append(code)
        r += 1
    return code_to_row, header_children

def hide_zero_rows(ws, code_to_row, header_children, d_values):
    for code, row in code_to_row.items():
        if code in header_children:
            continue  # headers handled separately below
        if code in ALWAYS_SHOW_CODES:
            continue
        if d_values.get(code, 0) == 0:
            ws.row_dimensions[row].hidden = True
    for header_code, children in header_children.items():
        any_visible = any(
            (d_values.get(c, 0) != 0) or (c in ALWAYS_SHOW_CODES)
            for c in children
        )
        if not any_visible:
            ws.row_dimensions[code_to_row[header_code]].hidden = True

if __name__ == "__main__":
    code_to_row, header_children = build_row_layout()
    import json
    print(json.dumps(header_children, ensure_ascii=False, indent=1))
