#!/usr/bin/env python3
"""Parametric model of the "S" bunk bed with drawer stairs.

One panel list -> every output:
  out/cutlist.csv     cut list grouped by identical parts (Excel-friendly UTF-8)
  out/hardware.csv    hardware and accessories (estimate)
  out/dxf/<id>.dxf    one CNC file per part, true arcs (bulge), mm
  out/all_panels.dxf  all parts laid out on one sheet
  out/viewer.html     3D viewer (three.js) with explode and part info
Run: python3 build.py   (prints a short check summary only)

Axes (mm): x = width left->right (stairs on the right), y = depth front(0)->back,
z = height. All parts are flat boards; outline is in the part's own (u, v) plane.
"""
import csv, json, math, os, sys
from collections import OrderedDict

# ---------------------------------------------------------------- parameters
P = dict(
    T=18,            # carcass board
    TF=25,           # fascia "S" board (room for the LED groove)
    grooveW=12, grooveD=10, grooveE=22,   # LED groove width, depth, centre distance from edge
    TB=9,            # back panel
    TD=15,           # drawer box board
    TH=6,            # drawer bottom (HDF)
    matL=1900, matW=900, matH=150,  # mattress (Israeli standard)
    clr=20,          # mattress clearance each side
    H=1950,          # overall height
    zLow=200,        # top of lower deck
    zUp=1050,        # top of upper deck
    topBand=180,     # fascia roof band height
    guard=160,       # rail height above upper mattress (EN 747: >=160)
    bbH=80,          # bottom band lip above lower deck
    colL=340,        # fascia left column (upper level)
    a2=390,          # wood filler width left of lower opening
    rightCol=320,    # fascia right column (lower level)
    R=90,            # fascia corner radius
    nSteps=4, run=240, Ds=450,      # stairs: steps, tread run, stair width
    shelfUpZ=600, shelfUpD=200,     # upper shelf height above deck, depth
    shelfLoZ=520, shelfLoD=150,     # lower shelf
    drawerDepth=350, slide=13,      # drawer box depth, slide gap per side
    sheetL=2440, sheetW=1220,       # stock sheet
)

MATERIALS = {
    'white':  ('MDF/סנדוויץ׳ לבן 18', '#eceef2'),
    'oak':    ('מלמין אלון 18', '#c9a073'),
    'back':   ('HDF/מלמין אלון 9', '#b88d62'),
    'drawer': ('מלמין לבן 15', '#f4f4f4'),
    'hdf':    ('HDF 6', '#a58a6b'),
    'white25': ('MDF 25 לבן (חזית S)', '#eceef2'),
    'steel':  ('נירוסטה מוברשת 3', '#b9bec4'),
    'knob':   ('ידית כפתור מתכת', '#8e9399'),
}

# ---------------------------------------------------------------- geometry helpers
def fillet(pts):
    """pts: [(x, y, r)] CCW polygon -> [(x, y, bulge)] with arcs of radius r at corners."""
    n, out = len(pts), []
    for i, (x, y, r) in enumerate(pts):
        if not r:
            out.append((x, y, 0.0)); continue
        px, py, _ = pts[i - 1]; nx, ny, _ = pts[(i + 1) % n]
        d1 = (x - px, y - py); l1 = math.hypot(*d1); d1 = (d1[0] / l1, d1[1] / l1)
        d2 = (nx - x, ny - y); l2 = math.hypot(*d2); d2 = (d2[0] / l2, d2[1] / l2)
        turn = math.atan2(d1[0] * d2[1] - d1[1] * d2[0], d1[0] * d2[0] + d1[1] * d2[1])
        t = r * math.tan(abs(turn) / 2)
        out.append((x - d1[0] * t, y - d1[1] * t, math.tan(turn / 4)))
        out.append((x + d2[0] * t, y + d2[1] * t, 0.0))
    return out

def rect(w, h):
    return [(0, 0, 0.0), (w, 0, 0.0), (w, h, 0.0), (0, h, 0.0)]

def tessellate(outline, seg=10):
    pts = []
    for i, (x, y, b) in enumerate(outline):
        pts.append((x, y))
        if b:
            qx, qy, _ = outline[(i + 1) % len(outline)]
            cx, cy = (qx - x), (qy - y)
            k = (1 - b * b) / (4 * b)
            ox, oy = (x + qx) / 2 - cy * k, (y + qy) / 2 + cx * k
            a0, sweep = math.atan2(y - oy, x - ox), 4 * math.atan(b)
            rr = math.hypot(x - ox, y - oy)
            for s in range(1, seg):
                a = a0 + sweep * s / seg
                pts.append((ox + rr * math.cos(a), oy + rr * math.sin(a)))
    return pts

def bbox2(outline):
    p = tessellate(outline)
    xs, ys = [a for a, _ in p], [b for _, b in p]
    return min(xs), min(ys), max(xs), max(ys)

def perimeter(outline):
    p = tessellate(outline, 16)
    return sum(math.dist(p[i], p[(i + 1) % len(p)]) for i in range(len(p)))

def area(outline):
    p = tessellate(outline, 16)
    return abs(sum(p[i][0] * p[(i + 1) % len(p)][1] - p[(i + 1) % len(p)][0] * p[i][1]
                   for i in range(len(p)))) / 2

BASIS = {'XZ': ((1, 0, 0), (0, 0, 1), (0, 1, 0)),
         'YZ': ((0, 1, 0), (0, 0, 1), (1, 0, 0)),
         'XY': ((1, 0, 0), (0, 1, 0), (0, 0, 1))}

def to_model(plane, origin, u, v, w):
    eu, ev, ew = BASIS[plane]
    return tuple(origin[i] + eu[i] * u + ev[i] * v + ew[i] * w for i in range(3))

# ---------------------------------------------------------------- model
PANELS, LED, DIMS = [], [], []

HW = {'steel', 'knob'}      # bought / engraved parts: not in the cut list or sheet count

def add(pid, name, group, mat, plane, origin, outline, t=None, band='front', explode=(0, 0, 0),
        text=None):
    t = t if t is not None else {'back': P['TB'], 'drawer': P['TD'], 'hdf': P['TH'],
                                 'white25': P['TF'], 'steel': 3, 'knob': 25}.get(mat, P['T'])
    PANELS.append(dict(id=pid, name=name, group=group, mat=mat, plane=plane, origin=origin,
                       outline=outline, t=t, band=band, explode=explode, text=text, grooves=[]))

def fillet_open(pts):
    """Open polyline [(x, y, r)] -> [(x, y, bulge)]; end points are not rounded."""
    out = [(pts[0][0], pts[0][1], 0.0)]
    for i in range(1, len(pts) - 1):
        if pts[i][2]:
            out += fillet([pts[i - 1][:2] + (0,), pts[i], pts[i + 1][:2] + (0,)])[1:3]
        else:
            out.append((pts[i][0], pts[i][1], 0.0))
    return out + [(pts[-1][0], pts[-1][1], 0.0)]

def groove(pid, path):
    """LED groove along an open centre-line path (panel u,v coords) on the panel front face."""
    p = next(q for q in PANELS if q['id'] == pid)
    c = tessellate(fillet_open(path), 10)
    hw, nrm = P['grooveW'] / 2, []
    for i in range(len(c)):
        a, b = c[max(i - 1, 0)], c[min(i + 1, len(c) - 1)]
        d = math.hypot(b[0] - a[0], b[1] - a[1])
        nrm.append((-(b[1] - a[1]) / d, (b[0] - a[0]) / d))
    band = [(x + n[0] * hw, y + n[1] * hw) for (x, y), n in zip(c, nrm)] + \
           [(x - n[0] * hw, y - n[1] * hw) for (x, y), n in reversed(list(zip(c, nrm)))]
    p['grooves'].append(dict(center=c, band=band))
    LED.append([to_model('XZ', p['origin'], x, z, -1) for x, z in c])

def build():
    T, TB, R = P['T'], P['TB'], P['R']
    W = P['matL'] + 2 * T + 2 * P['clr']
    D = P['matW'] + 2 * P['clr'] + P['TF'] + TB
    H, zLow, zUp = P['H'], P['zLow'], P['zUp']
    Ls = D - TB - P['TF']                # side panel depth (behind fascia, before back)
    midBot = zUp - T - 60
    midTop = zUp + P['matH'] + P['guard']
    zTb, zBb = H - P['topBand'], zLow + P['bbH']
    colL, a2, rc = P['colL'], P['a2'], P['rightCol']
    P.update(W=W, D=D)

    # --- fascia "S" (front plane y=0..TF), LED grooves on its front face
    h1, TF, e = H - midBot, P['TF'], P['grooveE']
    mt, tb = midTop - midBot, zTb - midBot
    add('F1', 'חזית S עליונה (גג+עמוד שמאל+מעקה)', 'fascia', 'white25', 'XZ', (0, 0, midBot),
        fillet([(0, 0, 0), (W, 0, 0), (W, mt, R), (colL, mt, R), (colL, tb, R), (W, tb, R),
                (W, h1, 0), (0, h1, 0)]), band='all', explode=(0, -400, 0))
    add('F2', 'חזית S תחתונה (סף+עמוד ימין)', 'fascia', 'white25', 'XZ', (0, 0, 0),
        fillet([(0, 0, 0), (W, 0, 0), (W, midBot, 0), (W - rc, midBot, 0),
                (W - rc, zBb, R), (0, zBb, 0)]), band='all', explode=(0, -400, 0))
    add('F3', 'מילוי חזית שמאלי (עץ)', 'fascia', 'oak', 'XZ', (0, 0, zBb),
        rect(a2, midBot - zBb), t=TF, band='all', explode=(0, -400, 0))
    groove('F1', [(W - R - 10, mt - e, 0), (colL - e, mt - e, R + e), (colL - e, tb + e, R + e),
                  (W - R - 10, tb + e, 0)])                       # around the upper opening
    groove('F1', [(a2 + 15, e, 0), (W - rc - 15, e, 0)])          # top of the lower opening
    groove('F2', [(W - rc + e, midBot - 15, 0), (W - rc + e, zBb - e, R + e),
                  (a2 + 15, zBb - e, 0)])                         # right side and sill
    plate = fillet([(0, 0, 12), (240, 0, 12), (240, 110, 12), (0, 110, 12)])
    add('N1', 'לוחית פלדה MAOR', 'fascia', 'steel', 'XZ', (W - 300, -3, midBot + 130), plate,
        band='none', explode=(0, -550, 0), text='MAOR')
    add('N2', 'לוחית פלדה TAHEL', 'fascia', 'steel', 'XZ', (W - 280, -3, zBb + 300), plate,
        band='none', explode=(0, -550, 0), text='TAHEL')

    # --- carcass
    add('S1', 'דופן שמאל', 'carcass', 'oak', 'YZ', (0, TF, 0), rect(Ls, H), explode=(-300, 0, 0))
    add('S2', 'דופן ימין (פתח כניסה)', 'carcass', 'oak', 'YZ', (W - T, TF, 0), fillet(
        [(0, 0, 0), (Ls, 0, 0), (Ls, zUp, 0), (Ls - 2 * P['run'] - 40, zUp, R),
         (Ls - 2 * P['run'] - 40, H, R), (0, H, 0)]), band='all', explode=(300, 0, 0))
    add('RF', 'גג', 'carcass', 'white', 'XY', (T, TF, H - T), rect(W - 2 * T, Ls), explode=(0, 0, 400))
    add('UD', 'רצפת מיטה עליונה', 'upper', 'oak', 'XY', (T, TF, zUp - T), rect(W - 2 * T, Ls),
        explode=(0, 0, 150))
    add('LD', 'רצפת מיטה תחתונה', 'lower', 'oak', 'XY', (T, TF, zLow - T), rect(W - 2 * T, Ls),
        explode=(0, 0, -100))
    for i, y in enumerate((TF, TF + Ls / 2 - T / 2, TF + Ls - T)):
        add(f'B{i+1}', 'קורת בסיס', 'lower', 'oak', 'XZ', (T, y, 0),
            rect(W - 2 * T, zLow - T), band='none', explode=(0, 0, -250))
    for i, f in enumerate((1 / 3, 2 / 3)):
        add(f'K{i+1}', 'צלע חיזוק מתחת לרצפה עליונה', 'upper', 'oak', 'XZ',
            (T, TF + Ls * f - T / 2, zUp - T - 100), rect(W - 2 * T, 100), band='none',
            explode=(0, 0, 50))
    split = zUp - T
    add('BK1', 'גב תחתון', 'back', 'back', 'XZ', (0, D - TB, 0), rect(W, split), band='none',
        explode=(0, 400, 0))
    add('BK2', 'גב עליון', 'back', 'back', 'XZ', (0, D - TB, split), rect(W, H - split),
        band='none', explode=(0, 400, 0))

    # --- shelves (back wall) upper and lower
    def shelf(tag, grp, zbase, zs, depth, divH, ex):
        y0 = D - TB - depth
        add(f'{tag}S', f'מדף אחורי {grp}', grp, 'oak', 'XY', (T, y0, zbase + zs),
            rect(W - 2 * T, depth), explode=(0, ex, 0))
        for i, f in enumerate((0.25, 0.5, 0.75)):
            add(f'{tag}D{i+1}', f'מחיצת מדף {grp}', grp, 'oak', 'YZ', (W * f - T / 2, y0, zbase + zs + T),
                rect(depth, divH), explode=(0, ex, 0))
        add(f'{tag}P', f'תומך מדף {grp}', grp, 'oak', 'YZ', (W * 0.72 - T / 2, y0, zbase),
            rect(depth, zs), explode=(0, ex, 0))
    shelf('U', 'upper', zUp, P['shelfUpZ'], P['shelfUpD'], H - T - (zUp + P['shelfUpZ'] + T), 250)
    shelf('L', 'lower', zLow, P['shelfLoZ'], P['shelfLoD'], 180, 250)

    # --- stairs with drawers beside the right side (x = W..W+Ds), climbing front -> back.
    # Each level panel is the tread of step k and the floor of the drawer above it.
    n, Ds, rise = P['nSteps'], P['Ds'], zUp / (P['nSteps'] + 1)
    run = min(P['run'], (D - 5) // n)
    h = [(k + 1) * rise for k in range(n)]          # tread top of step k (k=0 at the front)
    Lr, ex, dex = n * run, (450, 0, 0), (450, -350, 0)
    prof = [(0, 0, 0), (Lr, 0, 0)]
    for k in range(n - 1, -1, -1):
        prof += [((k + 1) * run, h[k] - T, 0), (k * run, h[k] - T, 0)]
    add('SWI', 'דופן מדרגות פנימית (מדורגת)', 'stairs', 'oak', 'YZ', (W, 0, 0), prof, explode=ex)
    g = P['guard'] - 10
    add('SWO', 'דופן מדרגות חיצונית לבנה + מעקה', 'stairs', 'white', 'YZ', (W + Ds - T, 0, 0), fillet(
        [(0, 0, 0), (Lr, 0, 0), (Lr, zUp + 300, 60), ((n - 1) * run, h[-1] + g, 0),
         (0, h[0] + g, 60)]), band='all', explode=(650, 0, 0))
    add('SBS', 'בסיס מדרגות', 'stairs', 'oak', 'XY', (W + T, 0, 0), rect(Ds - 2 * T, Lr - T),
        band='front', explode=ex)
    add('SBK', 'גב מדרגות', 'stairs', 'oak', 'XZ', (W + T, Lr - T, T), rect(Ds - 2 * T, h[-1] - 2 * T),
        band='none', explode=ex)
    for k in range(n):
        y1 = Lr if k == n - 1 else Lr - T
        add(f'ST{k}', f'שלב מדרגה {k+1}', 'stairs', 'oak', 'XY', (W + T, k * run, h[k] - T),
            rect(Ds - 2 * T, y1 - k * run), band='front', explode=ex)
    a, b, s, td = W + T, W + Ds - T, P['slide'], P['TD']
    slides = []
    for k in range(n):
        zb = h[k - 1] if k else T
        add(f'DF{k}', f'חזית מגירה {k+1}', 'drawers', 'oak', 'XZ', (a + 2, k * run, zb + 2),
            rect(b - a - 4, h[k] - T - zb - 4), band='all', explode=dex)
        add(f'KN{k}', f'ידית מגירה {k+1}', 'drawers', 'knob', 'XZ',
            ((a + b) / 2, k * run - 25, (zb + h[k] - T) / 2), [(-15, 0, 1.0), (15, 0, 1.0)],
            band='none', explode=dex)
        bd = min(P['drawerDepth'], int((Lr - T - k * run - T - 10) // 50 * 50))
        bh, z0, y0 = min(h[k] - T - zb - 40, 250), zb + 12 + P['TH'], k * run + T
        slides.append(bd)
        for side, x in (('L', a + s), ('R', b - s - td)):
            add(f'DS{k}{side}', 'דופן מגירה', 'drawers', 'drawer', 'YZ', (x, y0, z0), rect(bd, bh),
                band='front', explode=dex)
        for tag, y in (('I', y0), ('K', y0 + bd - td)):
            add(f'D{tag}{k}', 'חזית/גב פנימי מגירה', 'drawers', 'drawer', 'XZ', (a + s + td, y, z0),
                rect(b - a - 2 * s - 2 * td, bh), band='front', explode=dex)
        add(f'DB{k}', 'תחתית מגירה', 'drawers', 'hdf', 'XY', (a + s, y0, z0 - P['TH']),
            rect(b - a - 2 * s, bd), band='none', explode=dex)
    P.update(slides=slides, run_eff=run)

    # main dimensions for the viewer: (from, to, offset, label in cm)
    cm = lambda mm: f'{mm / 10:.1f}'.rstrip('0').rstrip('.')
    WS = W + Ds
    for a, b, off in (
            ((0, 0, 0), (0, 0, H), (-250, 0, 0)),                      # total height
            ((0, D, 0), (0, D, zUp), (-250, 0, 0)),                    # upper deck height
            ((0, D, 0), (0, D, zLow), (-500, 0, 0)),                   # lower deck height
            ((0, 0, H), (W, 0, H), (0, 0, 220)),                       # body width
            ((0, 0, 0), (WS, 0, 0), (0, -350, 0)),                     # width incl. stairs
            ((W, 0, H), (W, D, H), (0, 0, 220)),                       # depth
            ((WS, 0, 0), (WS, Lr, 0), (250, 0, 0)),                    # stairs length
            ((WS, Lr, 0), (WS, Lr, h[-1]), (250, 0, 0)),               # top step height
            ((W, 0, 0), (WS, 0, 0), (0, -170, 0)),                     # stairs width
            ((colL + 250, 0, midTop), (colL + 250, 0, zTb), (0, -1, 0)),   # upper opening height
            ((colL, 0, midTop + 120), (W, 0, midTop + 120), (0, -1, 0)),   # upper opening width
            ((a2 + 250, 0, zBb), (a2 + 250, 0, midBot), (0, -1, 0)),       # lower opening height
            ((a2, 0, zBb + 120), (W - rc, 0, zBb + 120), (0, -1, 0))):     # lower opening width
        L = math.dist(a, b) if a[2] == b[2] or a[0] != b[0] or a[1] != b[1] else abs(b[2] - a[2])
        DIMS.append(dict(a=a, b=b, off=off, label=cm(L)))
    P.update(midBot=midBot, midTop=midTop, zTb=zTb, zBb=zBb, rise=rise, h=h)

# ---------------------------------------------------------------- checks
def model_bbox(p):
    x0, y0, x1, y1 = bbox2(p['outline'])
    c = [to_model(p['plane'], p['origin'], u, v, w)
         for u in (x0, x1) for v in (y0, y1) for w in (0, p['t'])]
    return [min(q[i] for q in c) for i in range(3)], [max(q[i] for q in c) for i in range(3)]

def inside(p, pt):
    eu, ev, ew = BASIS[p['plane']]
    d = [pt[i] - p['origin'][i] for i in range(3)]
    u, v, w = (sum(d[i] * e[i] for i in range(3)) for e in (eu, ev, ew))
    if not (0 < w < p['t']):
        return False
    poly, c = p['_poly'], False
    for i in range(len(poly)):
        (x1, y1), (x2, y2) = poly[i - 1], poly[i]
        if (y1 > v) != (y2 > v) and u < x1 + (v - y1) * (x2 - x1) / (y2 - y1):
            c = not c
    return c

def collisions():
    for p in PANELS:
        p['_poly'], p['_bb'] = tessellate(p['outline']), model_bbox(p)
    hits = []
    for i, a in enumerate(PANELS):
        for b in PANELS[i + 1:]:
            lo = [max(a['_bb'][0][k], b['_bb'][0][k]) for k in range(3)]
            hi = [min(a['_bb'][1][k], b['_bb'][1][k]) for k in range(3)]
            if any(hi[k] - lo[k] < 0.5 for k in range(3)):
                continue
            N = 6
            for ix in range(N):
                pt = None
                for iy in range(N):
                    for iz in range(N):
                        q = [lo[k] + (hi[k] - lo[k]) * (s + 0.5) / N
                             for k, s in zip(range(3), (ix, iy, iz))]
                        if inside(a, q) and inside(b, q):
                            pt = q; break
                    if pt: break
                if pt:
                    hits.append((a['id'], b['id'])); break
    return hits

# ---------------------------------------------------------------- outputs
def part_dims(p):
    x0, y0, x1, y1 = bbox2(p['outline'])
    return round(x1 - x0), round(y1 - y0)

def is_rect(p):
    return len(p['outline']) == 4 and not any(b for *_, b in p['outline'])

def pack(mat, kerf=5):
    """Shelf (strip) packing, first-fit decreasing: realistic sheet count per material."""
    SL, SW = P['sheetL'], P['sheetW']
    parts = sorted((sorted(part_dims(p), reverse=True) for p in PANELS if p['mat'] == mat),
                   key=lambda d: (-d[1], -d[0]))
    sheets = []                      # each: [free_height, [strip: [height, free_length]]]
    for L, Wd in parts:
        if L > SL or Wd > SW:
            raise SystemExit(f'part {L}x{Wd} ({mat}) larger than sheet')
        done = False
        for sh in sheets:
            for st in sh[1]:
                if Wd <= st[0] and L + kerf <= st[1]:
                    st[1] -= L + kerf; done = True; break
            if not done and Wd + kerf <= sh[0]:
                sh[0] -= Wd + kerf; sh[1].append([Wd, SL - L - kerf]); done = True
            if done: break
        if not done:
            sheets.append([SW - Wd - kerf, [[Wd, SL - L - kerf]]])
    return len(sheets)

def write_outputs(out):
    import ezdxf
    os.makedirs(f'{out}/dxf', exist_ok=True)
    for f in os.listdir(f'{out}/dxf'):
        os.remove(f'{out}/dxf/{f}')
    groups = OrderedDict()
    for p in (q for q in PANELS if q['mat'] not in HW):
        a, b = part_dims(p)
        key = (p['name'], max(a, b), min(a, b), p['t'], p['mat'], is_rect(p))
        groups.setdefault(key, []).append(p['id'])
    band_len = 0.0
    with open(f'{out}/cutlist.csv', 'w', newline='', encoding='utf-8-sig') as f:
        w = csv.writer(f)
        w.writerow(['מזהים', 'שם החלק', 'חומר', 'עובי', 'אורך', 'רוחב', 'כמות', 'קנט',
                    'חיתוך', 'שטח מ"ר (סה"כ)'])
        for (name, L, Wd, t, mat, rectangular), ids in groups.items():
            p = next(q for q in PANELS if q['id'] == ids[0])
            band = {'all': 'מסביב', 'front': 'צד ארוך אחד', 'none': '-'}[p['band']]
            band_len += len(ids) * {'all': perimeter(p['outline']), 'front': L, 'none': 0}[p['band']]
            w.writerow([' '.join(ids), name, MATERIALS[mat][0], t, L, Wd, len(ids), band,
                        ('מסור' if rectangular else 'CNC (קובץ DXF)') +
                        (' + חריץ LED' if p['grooves'] else ''),
                        round(len(ids) * area(p['outline']) / 1e6, 3)])
    # DXF per part + combined layout
    allDoc = ezdxf.new('R2010', units=4); allMsp = allDoc.modelspace()
    allDoc.layers.add('CUT', color=1); allDoc.layers.add('TEXT', color=7)
    ox = oy = rowH = 0
    gl = f"LED_GROOVE_{P['grooveW']}x{P['grooveD']}"
    allDoc.layers.add(gl, color=3); allDoc.layers.add('LED_CENTER', color=2)
    for p in (q for q in PANELS if q['mat'] not in HW):
        a, b = part_dims(p)
        doc = ezdxf.new('R2010', units=4); msp = doc.modelspace()
        doc.layers.add('CUT', color=1); doc.layers.add('TEXT', color=7)
        doc.layers.add(gl, color=3); doc.layers.add('LED_CENTER', color=2)
        for m, dx, dy in ((msp, 0, 0), (allMsp, ox, oy)):
            for g in p['grooves']:     # pocket on the FRONT face, depth grooveD
                m.add_lwpolyline([(x + dx, y + dy) for x, y in g['band']], close=True,
                                 dxfattribs={'layer': gl})
                m.add_lwpolyline([(x + dx, y + dy) for x, y in g['center']], dxfattribs={'layer': 'LED_CENTER'})
            m.add_lwpolyline([(x + dx, y + dy, 0, 0, bl) for x, y, bl in p['outline']],
                             format='xyseb', close=True, dxfattribs={'layer': 'CUT'})
            m.add_text(f"{p['id']}  {a}x{b}x{p['t']}  {p['mat']}", height=25,
                       dxfattribs={'layer': 'TEXT'}).set_placement((dx + 20, dy + 20))
        doc.saveas(f"{out}/dxf/{p['id']}.dxf")
        ox += a + 60; rowH = max(rowH, b)
        if ox > 6000:
            ox, oy, rowH = 0, oy + rowH + 80, 0
    allDoc.saveas(f'{out}/all_panels.dxf')
    # hardware (estimate)
    W, D, Ds = P['W'], P['D'], P['Ds']
    n = P['nSteps']
    led_len = sum(sum(math.dist(s[i], s[i + 1]) for i in range(len(s) - 1)) for s in LED) / 1000
    carcass_joints = sum(1 for p in PANELS if p['group'] in ('carcass', 'upper', 'lower', 'stairs')
                         and p['mat'] != 'back')
    hw = [
        ('ברגי קונפירמט 7x50', carcass_joints * 4, 'הערכה: 4 לכל חלק גוף'),
        ('ברגי סיני 4x30 לחיבור החזית מאחור', math.ceil(2 * W / 250) * 2, 'כל 25 ס"מ'),
        ('ברגי גב 3.5x16 / סיכות', math.ceil(2 * (W + P['H']) / 150) * 2, 'כל 15 ס"מ'),
        ('מסילות טלסקופיות טריקה שקטה (זוג)', n, 'אורכים: ' + ', '.join(map(str, P['slides'])) + ' מ"מ'),
        ('ידיות כפתור מתכת Ø30', n, 'במרכז כל חזית מגירה'),
        ('לוחיות נירוסטה 240x110x3 עם חריטה', 2, 'MAOR (למעלה), TAHEL (למטה), פינות R12'),
        ('פס LED 12V צהוב/חם + פרופיל אלומיניום שקוע + מפזר (מטר)', round(led_len + 0.5, 1),
         f"בחריץ {P['grooveW']}x{P['grooveD']} מ\"מ בחזית ה-S"),
        ('ספק 12V 36W + מתג/שלט', 1, ''),
        ('מוט וילון עליון (מ"מ)', round(W - P['colL'] - P['T']), ''),
        ('מוט וילון תחתון (מ"מ)', round(W - P['rightCol'] - P['a2']), ''),
        ('תושבת עיגון לקיר נגד התהפכות', 2, 'חובה'),
        ('רגליות פילוס', 6, ''),
        ('קנט PVC לבן/אלון 1 מ"מ (מטר)', round(band_len / 1000 * 1.1, 1), 'כולל 10% פחת'),
    ]
    with open(f'{out}/hardware.csv', 'w', newline='', encoding='utf-8-sig') as f:
        w = csv.writer(f); w.writerow(['פריט', 'כמות', 'הערה']); w.writerows(hw)
    # sheet estimate per material
    sheet = P['sheetL'] * P['sheetW'] / 1e6
    mats = OrderedDict()
    for p in (q for q in PANELS if q['mat'] not in HW):
        mats[p['mat']] = mats.get(p['mat'], 0) + area(p['outline']) / 1e6
    sheets = {m: dict(name=MATERIALS[m][0], m2=round(a, 2), sheets=pack(m)) for m, a in mats.items()}
    # viewer data
    data = dict(params={k: P[k] for k in ('W', 'D', 'H', 'zLow', 'zUp', 'matL', 'matW', 'T')},
                materials={k: dict(name=v[0], color=v[1]) for k, v in MATERIALS.items()},
                panels=[dict(id=p['id'], name=p['name'], group=p['group'], mat=p['mat'], t=p['t'],
                             plane=p['plane'], origin=p['origin'], explode=p['explode'],
                             dims=part_dims(p), cnc=not is_rect(p), hw=p['mat'] in HW,
                             text=p['text'], gd=P['grooveD'],
                             grooves=[[(round(x, 1), round(y, 1)) for x, y in g['band']]
                                      for g in p['grooves']],
                             pts=[(round(x, 1), round(y, 1)) for x, y in tessellate(p['outline'], 8)])
                        for p in PANELS],
                led=[[tuple(round(c, 1) for c in q) for q in s] for s in LED], dims=DIMS,
                cutlist=[dict(ids=ids, name=k[0], L=k[1], W=k[2], t=k[3], mat=k[4], qty=len(ids),
                              cnc=not k[5]) for k, ids in groups.items()],
                hardware=[dict(item=a, qty=b, note=c) for a, b, c in hw],
                sheets=sheets)
    tpl = open(os.path.join(os.path.dirname(__file__), 'viewer_template.html'), encoding='utf-8').read()
    with open(f'{out}/viewer.html', 'w', encoding='utf-8') as f:
        f.write(tpl.replace('/*DATA*/null', json.dumps(data, ensure_ascii=False, separators=(',', ':'))))
    write_sketchup(f'{out}/bunkbed_sketchup.rb')
    return groups, sheets, led_len

def write_sketchup(path):
    """Ruby script that builds the model natively in SketchUp: assembled + fully exploded."""
    gd, parts = P['grooveD'], []
    for p in PANELS:
        ew = BASIS[p['plane']][2]
        loop = lambda pts, w: [[round(c, 2) for c in to_model(p['plane'], p['origin'], u, v, w)]
                               for u, v in pts]
        outer, sol = tessellate(p['outline'], 8), []
        if p['grooves']:
            bands = [g['band'] for g in p['grooves']]
            sol.append(dict(outer=loop(outer, gd), holes=[], dir=ew, depth=p['t'] - gd, mat=p['mat']))
            sol.append(dict(outer=loop(outer, 0), holes=[loop(b, 0) for b in bands], dir=ew,
                            depth=gd, mat=p['mat']))
            sol += [dict(outer=loop(b, 1), holes=[], dir=ew, depth=gd - 1, mat='led') for b in bands]
        else:
            sol.append(dict(outer=loop(outer, 0), holes=[], dir=ew, depth=p['t'], mat=p['mat']))
        x0, y0, x1, y1 = bbox2(p['outline'])
        parts.append(dict(id=p['id'], name=p['name'], group=p['group'], explode=p['explode'],
                          solids=sol, text=p['text'],
                          tc=to_model(p['plane'], p['origin'], (x0 + x1) / 2, (y0 + y1) / 2, -0.4)))
    mats = {k: [v[0], v[1]] for k, v in MATERIALS.items()}
    mats.update(led=['LED צהוב', '#ffd21f'], ink=['חריטה', '#2b2f33'])
    data = json.dumps(dict(parts=parts, mats=mats, groups=GROUP_NAMES, shift=P['W'] + P['Ds'] + 1800),
                      ensure_ascii=False)
    with open(path, 'w', encoding='utf-8') as f:
        f.write(RUBY.replace('__DATA__', data))

GROUP_NAMES = {'fascia': 'חזית S', 'carcass': 'גוף וגג', 'upper': 'מיטה עליונה',
               'lower': 'מיטה תחתונה', 'back': 'גב', 'stairs': 'מדרגות', 'drawers': 'מגירות'}

RUBY = r'''# encoding: UTF-8
# S bunk bed - generated by bunkbed/build.py. Builds two models in the open SketchUp file:
#   "מודל מורכב" (assembled, every part its own named group) and
#   "מודל מפורק" (fully exploded, same as the viewer slider at maximum).
# SketchUp: Extensions > Developer > Ruby Console, then:  load '/full/path/bunkbed_sketchup.rb'
# then File > Save As... bunkbed.skp
require 'json'

module BunkBedS
  D = JSON.parse(<<~'JSONDATA')
    __DATA__
  JSONDATA

  def self.pt(a) Geom::Point3d.new(a[0].mm, a[1].mm, a[2].mm) end

  def self.solid(ents, s, mats)
    g = ents.add_group
    e = g.entities
    e.add_face(s['outer'].map { |a| pt(a) })
    s['holes'].each { |h| hf = e.add_face(h.map { |a| pt(a) }); hf.erase! if hf && hf.valid? }
    f = e.grep(Sketchup::Face).max_by(&:area)
    f.reverse! if f.normal.dot(Geom::Vector3d.new(*s['dir'])) < 0
    f.pushpull(s['depth'].mm)
    g.material = mats[s['mat']]
    g
  end

  def self.text(ents, str, center, mat)
    g = ents.add_group
    g.entities.add_3d_text(str, TextAlignCenter, 'Arial', true, false, 46.mm, 0.0, 0.0, true, 0.8.mm)
    g.transform!(Geom::Transformation.translation(ORIGIN - g.bounds.center))
    g.transform!(Geom::Transformation.rotation(ORIGIN, X_AXIS, 90.degrees))
    g.transform!(Geom::Transformation.translation(pt(center) - ORIGIN))
    g.material = mat
    g.name = str
  end

  def self.model(name, shift, k, mats, tags)
    top = Sketchup.active_model.active_entities.add_group
    top.name = name
    cats = {}
    D['parts'].each do |p|
      cat = cats[p['group']] ||= begin
        c = top.entities.add_group
        c.name = D['groups'][p['group']]
        c.layer = tags[p['group']]
        c
      end
      g = cat.entities.add_group
      g.name = "#{p['id']} #{p['name']}"
      p['solids'].each { |s| solid(g.entities, s, mats) }
      text(g.entities, p['text'], p['tc'], mats['ink']) if p['text']
      if k > 0
        v = Geom::Vector3d.new(*p['explode'].map { |x| (x * k).mm })
        g.transform!(Geom::Transformation.translation(v))
      end
    end
    top.transform!(Geom::Transformation.translation(Geom::Vector3d.new(shift.mm, 0, 0)))
  end

  def self.run
    m = Sketchup.active_model
    m.start_operation('מיטת קומותיים S', true)
    mats = {}
    D['mats'].each do |key, (label, hex)|
      mat = m.materials[label] || m.materials.add(label)
      mat.color = Sketchup::Color.new(hex)
      mats[key] = mat
    end
    tags = {}
    D['groups'].each { |key, label| tags[key] = m.layers[label] || m.layers.add(label) }
    model('מודל מורכב', 0, 0, mats, tags)
    model('מודל מפורק', D['shift'], 1, mats, tags)
    m.commit_operation
    m.active_view.zoom_extents
  end
end

BunkBedS.run
'''

if __name__ == '__main__':
    here = os.path.dirname(os.path.abspath(__file__))
    build()
    hits = collisions()
    groups, sheets, led_len = write_outputs(os.path.join(here, 'out'))
    print(f"overall W x D x H = {P['W']} x {P['D']} x {P['H']} mm; with stairs W = "
          f"{P['W'] + P['Ds']} mm")
    print(f"panels {len(PANELS)}, cut-list lines {len(groups)}, LED {led_len:.1f} m, "
          f"step rise {P['rise']:.0f} mm")
    print('sheets:', ', '.join(f"{v['name']}: {v['m2']} m2 -> {v['sheets']}" for v in sheets.values()))
    print('collisions:', hits or 'none')
    sys.exit(1 if hits else 0)
