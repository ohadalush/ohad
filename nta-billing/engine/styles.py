import pickle, copy, os

_here = os.path.dirname(os.path.abspath(__file__))
with open(os.path.join(_here, "style_data.pkl"), "rb") as f:
    _data = pickle.load(f)

STYLES = _data["styles"]
COL_WIDTHS = _data["col_widths"]      # for columns A-M, matches the order-sheet template
ROW_HEIGHTS = _data["row_heights"]    # row# -> height, matches the order-sheet template (rows 1-104)

YELLOW = "FFFFFF00"


def apply_cell_style(cell, style_key, col):
    """Apply a saved style (minus any yellow fill) to a cell."""
    st = STYLES[style_key].get(col)
    if not st:
        return
    cell.font = copy.copy(st["font"])
    cell.border = copy.copy(st["border"])
    cell.alignment = copy.copy(st["alignment"])
    cell.number_format = st["number_format"]
    fill = st["fill"]
    fg = fill.fgColor.rgb if fill and fill.fgColor else None
    if fg == YELLOW:
        return  # skip yellow highlight per user's request - leave default (no fill)
    cell.fill = copy.copy(fill)


def set_column_widths(ws, cols="ABCDEFGHI"):
    for col in cols:
        if col in COL_WIDTHS:
            ws.column_dimensions[col].width = COL_WIDTHS[col]


def set_row_height(ws, row):
    if row in ROW_HEIGHTS:
        ws.row_dimensions[row].height = ROW_HEIGHTS[row]
