"""
v2 layout traced from the user's isometric campus map (1536x1024 image).
Image positions are converted to plan metres with an affine fit:
  image = O + x*A + z*B   (A: 1 m east, B: 1 m south, measured on the 400 m track)
Plan: x = east, z = south, metres. World 800 x 800 m centred on the campus.
"""
import math

A = (3.45, -0.35)
B = (-0.71, 2.30)
DET = A[0] * B[1] - B[0] * A[1]
O_IMG = (760.0, 650.0)          # image point that becomes plan (0,0) – campus centre
PX_PER_M_UP = 1.4               # how far a point 1 m above ground shifts up in the image


def img2plan(u, v, h=0.0):
    v = v + PX_PER_M_UP * h     # drop roof-level points to the ground
    du, dv = u - O_IMG[0], v - O_IMG[1]
    x = (B[1] * du - B[0] * dv) / DET
    z = (-A[1] * du + A[0] * dv) / DET
    return round(x, 1), round(z, 1)


WORLD = 800.0
HALF = WORLD / 2

# campus boundary (outer edge of perimeter road), image coords
CAMPUS_IMG = [(305, 378), (1212, 286), (1368, 596), (1062, 1022), (148, 818)]
CAMPUS = [(-192.0, -150.0), (102.0, -150.0), (180.0, 3.0), (126.0, 184.0), (-192.0, 58.0)]

# ---------------------------------------------------------------- buildings
# (u0,v0)->(u1,v1) roof ridge in image, width m, floors, floor h, wall, roof, type, th, en
_B = [
    ((588, 373), (806, 352), 12, 3, 3.5, "#eef2f2", "#3f8a5a", "gable", "อาคาร 1", "Building 1"),
    ((828, 340), (1038, 328), 12, 3, 3.5, "#eef2f2", "#3f8a5a", "gable", "อาคาร 2", "Building 2"),
    ((845, 405), (1078, 392), 12, 3, 3.5, "#eef2f2", "#3f8a5a", "gable", "อาคาร 3", "Building 3"),
    ((862, 470), (1095, 457), 12, 3, 3.5, "#eef2f2", "#3f8a5a", "gable", "อาคาร 4", "Building 4"),
    ((892, 535), (1112, 522), 12, 3, 3.5, "#eef2f2", "#3f8a5a", "gable", "อาคาร 5", "Building 5"),
    ((897, 512), (963, 518), 7, 1, 3.5, "#f3eeee", "#d6383c", "gable", "ห้องพยาบาล", "Nurse room"),
    ((1095, 338), (1200, 332), 12, 2, 3.5, "#f1f1ef", "#6b6c72", "gable", "อาคารฝึกงาน", "Workshop"),
    ((1170, 372), (1210, 505), 28, 3, 4.0, "#f6f3ee", "#e6dccf", "gable", "หอประชุม", "Auditorium"),
    ((1124, 450), (1146, 462), 8, 1, 3.2, "#f5f0f0", "#d6383c", "gable", "ร้านค้า", "Shop"),
    ((706, 415), (729, 615), 30, 1, 13.0, "#2f4f8f", "#e0423f", "barrel", "โรงยิมหลังคาโค้ง", "Dome gym"),
    ((800, 410), (833, 590), 13, 3, 3.6, "#f4f1ec", "#8a5a3c", "gable", "อาคารหลังคาน้ำตาล", "Brown-roof building"),
    ((688, 668), (826, 702), 18, 2, 3.8, "#f5f1ee", "#d93a3f", "thai", "อาคารหลังคาแดง", "Red-roof hall"),
    ((858, 652), (1003, 696), 16, 2, 3.6, "#f1f1ef", "#d8dadc", "gable", "อาคารเรียนรวม", "Classroom block"),
    ((975, 628), (1078, 586), 14, 2, 3.6, "#f1f1ef", "#c9cdd2", "gable", "อาคารวิทยาศาสตร์", "Science building"),
    ((822, 730), (930, 768), 14, 1, 4.5, "#e9e9e9", "#4a4d55", "gable", "โรงอาหาร", "Canteen"),
    ((592, 767), (745, 780), 12, 2, 3.5, "#eef2f2", "#3f9a6a", "gable", "อาคาร 6", "Building 6"),
    ((757, 787), (905, 806), 12, 2, 3.5, "#eef2f2", "#3f9a6a", "gable", "อาคาร 7", "Building 7"),
    ((1150, 690), (1295, 592), 16, 3, 3.5, "#7ea6e6", "#6f9be0", "gable", "อาคารสีฟ้า", "Blue building"),
    ((1047, 745), (1123, 712), 14, 2, 3.6, "#efe2d0", "#e0c7a8", "gable", "อาคารธุรการ", "Admin office"),
    ((1050, 850), (1165, 750), 12, 1, 4.5, "#e8f0ec", "#2fae7a", "gable", "อาคารเกษตร", "Agriculture building"),
    ((902, 935), (1030, 890), 20, 2, 3.8, "#f3f3f1", "#4b4e55", "hip", "อาคารห้องสมุด", "Library"),
    ((572, 630), (618, 632), 12, 1, 4.0, "#f2f4f4", "#e9ecee", "gable", "ห้องกรรมการสนาม", "Track office"),
    ((575, 655), (580, 700), 8, 1, 3.6, "#e8f2ec", "#2f9c5c", "gable", "ห้องเก็บอุปกรณ์กีฬา", "Sports storage"),
]


def _bld(p0, p1, w, fl, fh, wall, roof, kind, th, en):
    hroof = fl * fh + (4 if kind != "barrel" else 7)
    a = img2plan(*p0, h=hroof)
    b = img2plan(*p1, h=hroof)
    L = math.hypot(b[0] - a[0], b[1] - a[1])
    ang = math.atan2(b[1] - a[1], b[0] - a[0])
    if ang > math.pi / 2: ang -= math.pi
    if ang < -math.pi / 2: ang += math.pi
    return dict(cx=round((a[0] + b[0]) / 2, 1), cz=round((a[1] + b[1]) / 2, 1), len=round(L, 1), wid=w,
                ang=round(ang, 4), floors=fl, fh=fh, wall=wall, roof=roof, type=kind, th=th, en=en)


BUILDINGS = [_bld(*b) for b in _B]
_by = {b['en']: b for b in BUILDINGS}
for n in ('Building 1', 'Building 2', 'Building 3', 'Building 4', 'Building 5', 'Workshop', 'Nurse room'):
    _by[n]['ang'] = 0.0
_by['Nurse room'].update(cx=40.0, cz=-48.5, len=20.0)
_by['Dome gym'].update(ang=round(math.pi / 2, 4), len=72.0, cz=-50.0, cx=-21.0, wid=28)
_by['Brown-roof building'].update(ang=round(math.pi / 2, 4), len=58.0, cz=-55.0, cx=5.0)
_by['Auditorium'].update(ang=1.10, len=60.0, cx=120.0)
_by['Shop'].update(cx=128.0, cz=-12.0, ang=1.10)
# moved beside the football field (user request): between the track and the gate road
_by['Track office'].update(ang=round(math.pi / 2, 4), cx=-52.0, cz=-46.0, len=16.0, wid=8)
_by['Sports storage'].update(ang=round(math.pi / 2, 4), cx=-52.0, cz=-28.0, len=12.0, wid=7)
for n in ('Building 2', 'Building 3', 'Building 4', 'Building 5'):
    _by[n].update(cx=50.0, len=58.0)
_by['Workshop'].update(cx=100.0, len=18.0)
_by['Science building'].update(cx=86.0, cz=8.0)
_by['Library'].update(cx=100.0, cz=140.0)
_by['Admin office'].update(cx=118.0, cz=58.0)
_by['Blue building'].update(cx=143.0, cz=20.0, len=44.0)

# canopies / covered walkways: image ridge, width, height, colour
_C = [
    ((340, 430), (222, 680), 10, 7.5, "#7cc7ef"),     # west grandstand roof (light blue)
    ((192, 772), (450, 872), 8, 4.0, "#e6e8ea"),      # long south stand
    ((935, 352), (937, 392), 4, 3.2, "#3cc4b5"),      # covered walkways between green rows
    ((960, 418), (964, 458), 4, 3.2, "#3cc4b5"),
    ((976, 484), (980, 522), 4, 3.2, "#3cc4b5"),
    ((800, 608), (762, 660), 3.5, 3.5, "#d6383c"),    # red covered walkway dome -> red hall
]


def _can(p0, p1, w, h, roof):
    a, b = img2plan(*p0, h=h), img2plan(*p1, h=h)
    L = math.hypot(b[0] - a[0], b[1] - a[1])
    ang = math.atan2(b[1] - a[1], b[0] - a[0])
    return dict(cx=round((a[0] + b[0]) / 2, 1), cz=round((a[1] + b[1]) / 2, 1), len=round(L, 1), wid=w,
                ang=round(ang, 4), h=h, roof=roof)


CANOPIES = [_can(*c) for c in _C]
_rows = sorted([_by[n] for n in ('Building 2', 'Building 3', 'Building 4', 'Building 5')], key=lambda b: b['cz'])
for i, (a, b) in enumerate(zip(_rows[:-1], _rows[1:])):
    z0, z1 = a['cz'] + a['wid'] / 2, b['cz'] - b['wid'] / 2
    CANOPIES[2 + i] = dict(cx=50.0, cz=round((z0 + z1) / 2, 1), len=round(z1 - z0, 1), wid=4, ang=round(math.pi / 2, 4), h=3.2, roof="#3cc4b5")

# stadium: track centre traced at image (430, 580); long axis = plan z
_tc = img2plan(430, 580)
TRACK = dict(cx=_tc[0], cz=_tc[1], straight=84.39, r_in=36.5, lanes=6, lane_w=1.22)
_rout = TRACK['r_in'] + TRACK['lanes'] * TRACK['lane_w']

# grandstand seating = same footprint as its roof, steps rise away from the track (west)
CANOPIES[0] = dict(cx=round(TRACK['cx'] - _rout - 12, 1), cz=TRACK['cz'], len=110.0, wid=12,
                   ang=round(math.pi / 2, 4), h=7.5, roof="#7cc7ef")
GRANDSTAND = CANOPIES[0]

# ---------------------------------------------------------------- ground areas (image polygons)
_SAND = [(562, 838), (858, 860), (822, 985), (540, 952)]
SAND = [(-40.0, 82.0), (48.0, 98.0), (48.0, 136.0), (-40.0, 104.0)]
COURT = [img2plan(*p) for p in [(982, 790), (1030, 788), (1028, 832), (978, 834)]]
DIRT_D = [img2plan(*p) for p in [(415, 412), (552, 412), (545, 450), (410, 450)]]
JUMP_PIT = [img2plan(*p) for p in [(432, 772), (482, 772), (480, 800), (428, 800)]]

# ---------------------------------------------------------------- roads (image polylines)
_R = [
    # perimeter loop just inside the boundary
    ([(330, 395), (1195, 305), (1340, 598), (1060, 1000), (170, 812), (330, 395)], 7.0),
    # road south of the dome to the classroom block
    # cross road south of row 5
    ([(880, 600), (1150, 590)], 6.0),
    # road north of the sand field
    ([(560, 815), (870, 840)], 6.0),
]
ROADS = [([img2plan(*p) for p in pts], w) for pts, w in _R[1:]]
ROADS.append(([(-42.0, -4.0), (32.0, 2.0)], 7.0))
ROADS.append(([(85.0, -144.0), (85.0, -40.0), (115.0, 5.0), (65.0, 165.0)], 8.0))


def _inset(poly, d):
    n = len(poly); out = []
    cx = sum(p[0] for p in poly) / n; cz = sum(p[1] for p in poly) / n
    for i in range(n):
        p0, p1, p2 = poly[i - 1], poly[i], poly[(i + 1) % n]
        def nrm(a, b):
            dx, dz = b[0] - a[0], b[1] - a[1]; l = math.hypot(dx, dz)
            nx, nz = -dz / l, dx / l
            mx, mz = (a[0] + b[0]) / 2, (a[1] + b[1]) / 2
            if (cx - mx) * nx + (cz - mz) * nz < 0: nx, nz = -nx, -nz
            return nx, nz
        n1, n2 = nrm(p0, p1), nrm(p1, p2)
        bx, bz = n1[0] + n2[0], n1[1] + n2[1]
        k = d / max(0.3, (bx * n1[0] + bz * n1[1]))
        out.append((round(p1[0] + bx * k, 1), round(p1[1] + bz * k, 1)))
    return out


PERIM = _inset(CAMPUS, 6.0)
ROADS.insert(0, (PERIM + [PERIM[0]], 7.0))
ROADS += [
    ([(-56.0, 106.0), (-52.0, 40.0), (-42.0, 12.0), (-42.0, -108.0)], 8.0),     # gate road
    ([(-42.0, -108.0), (16.0, -108.0)], 7.0),                    # north road
    ([(16.0, -144.0), (16.0, -20.0), (32.0, 2.0)], 7.0),         # spine
]

GATE = dict(x=-55.5, z=111.5, span=12, depth=6, h=5.5, colour="#2f6fd0")
SIGN_POS = (-34.0, 104.0)

# outside town roads (plan coords)
TOWN_ROADS = [
    ([(-400, 175), (400, 175)], 9.0),
]

# tall flagpole north of the dome (user request)
FLAGPOLE = dict(x=-24.0, z=-96.0, h=20.0)

# removed on user request (2026-11-19): waiting for a new reference image
REMOVED = {"Blue building", "Admin office", "Agriculture building", "Library", "Shop", "Canteen"}
BUILDINGS = [b for b in BUILDINGS if b["en"] not in REMOVED]
COURT = []

# ---------------------------------------------------------------- road network v2.4 (traced from the user's sketch)
# main roads: (polyline, carriageway width) -> drawn with sidewalks, kerbs, markings, lights
MAIN_ROADS = [
    ([(-55.5, 112.0), (-44.0, 40.0), (-42.0, -108.0), (16.0, -108.0)], 6.5),     # gate road + north road
    ([(16.0, -144.0), (16.0, -4.0)], 6.0),                                        # spine
    ([(16.0, -109.7), (85.0, -109.7)], 6.0),                                      # between rows 2 and 3
    ([(16.0, -79.6), (85.0, -79.6)], 6.0),                                        # between rows 3 and 4
    ([(85.0, -144.0), (85.0, -40.0), (115.0, 5.0), (62.2, 158.6)], 7.0),          # east avenue to the east gate
    ([(-44.0 + 0.0, 74.0), (83.2, 97.2)], 6.5),                                   # north of the sand field
]
SECONDARY_ROADS = [
    (PERIM + [PERIM[0]], 5.0),                                                    # service loop inside the fence
    ([(-42.0, -4.0), (109.0, -4.0)], 6.0),                                        # south of the dome
]
ROADS = SECONDARY_ROADS + MAIN_ROADS
GATES = [GATE, dict(x=62.2, z=158.6, span=12, depth=6, h=5.5, colour="#2f6fd0")]
# covered walkways that would sit on the new row roads are removed
CANOPIES = [c for c in CANOPIES if not (abs(c["cx"] - 50.0) < 1 and (abs(c["cz"] + 109.7) < 6 or abs(c["cz"] + 79.6) < 6))]

# 2026-11-19: move building 1 and 2 north, up against the service road (user arrows)
_by['Building 1'].update(cx=-19.5, cz=-134.0, len=57.0)
_by['Building 2'].update(cz=-134.0)

# 2026-11-19 (2): user's rectangles — push dome, brown building and green rows up against the roads
_by['Dome gym'].update(cx=-20.0, cz=-59.3, len=86.4, wid=28)
_by['Brown-roof building'].update(cx=4.8, cz=-59.3, len=86.4, wid=12.5)
_by['Building 3'].update(cz=-98.9)
_by['Building 4'].update(cz=-68.8)
_by['Building 5'].update(cz=-38.5)
_by['Nurse room'].update(cx=37.0, cz=-53.6)
for c in CANOPIES:
    if abs(c['cx'] - 50.0) < 1:          # covered walkway between rows 4 and 5
        z0 = _by['Building 4']['cz'] + 6; z1 = _by['Building 5']['cz'] - 6
        c.update(cz=round((z0 + z1) / 2, 1), len=round(z1 - z0, 1))
# big flagpole moves to the lawn south of building 1 (circle in the sketch)
FLAGPOLE = dict(x=-19.5, z=-120.5, h=30.0)

# 2026-11-19 (3): shorter building 2, east avenue continues north to the ring road, Buddha statue
_by['Building 2'].update(cx=43.5, len=45.0)
MAIN_ROADS[4] = ([(85.0, -164.0), (85.0, -40.0), (115.0, 5.0), (62.2, 158.6)], 7.0)
ROADS = SECONDARY_ROADS + MAIN_ROADS
GATES[0].update(out=None, rot=round(math.atan2(-11.5, 72.0), 4))
GATES[1].update(out=None, rot=round(math.atan2(-52.8, 153.6), 4))
GATES.append(dict(x=85.0, z=-150.0, span=12, depth=6, h=5.5, colour="#2f6fd0", out=(85.0, -164.0), rot=0.0))
BUDDHA = dict(x=92.5, z=-80.0, rot=round(-math.pi / 2, 4))   # faces west, towards the avenue

# ======================================================================= 2026-11-19 (4)
# multi-sport concrete court (hexagon in the sketch), buildings 6/7 squared to the road,
# school sign + waterfall at the front fence
def _unit(dx, dz):
    l = math.hypot(dx, dz); return dx / l, dz / l


def _isect(p, d, q, e):
    den = d[0] * e[1] - d[1] * e[0]
    t = ((q[0] - p[0]) * e[1] - (q[1] - p[1]) * e[0]) / den
    return (round(p[0] + d[0] * t, 1), round(p[1] + d[1] * t, 1))


_SR = MAIN_ROADS[5][0]                                   # road north of the court
COURT_ANG = math.atan2(_SR[1][1] - _SR[0][1], _SR[1][0] - _SR[0][0])
_u = (math.cos(COURT_ANG), math.sin(COURT_ANG)); _v = (-_u[1], _u[0])          # _v points south
_top_p = (_SR[0][0] + _v[0] * 6.2, _SR[0][1] + _v[1] * 6.2)
_dA = _unit(62.2 - 115.0, 158.6 - 5.0); _wA = (-_dA[1], _dA[0])
if _wA[0] > 0: _wA = (-_wA[0], -_wA[1])
_right_p = (115.0 + _wA[0] * 6.4, 5.0 + _wA[1] * 6.4)
_dS = _unit(CAMPUS[4][0] - CAMPUS[3][0], CAMPUS[4][1] - CAMPUS[3][1])        # south fence, east -> west
_inS = (-_dS[1], _dS[0])
if _inS[1] > 0: _inS = (-_inS[0], -_inS[1])                                  # inward = towards north
_bot_p = (CAMPUS[3][0] + _inS[0] * 2.5, CAMPUS[3][1] + _inS[1] * 2.5)
_dG = _unit(-44.0 - -55.5, 40.0 - 112.0); _eG = (-_dG[1], _dG[0])
if _eG[0] < 0: _eG = (-_eG[0], -_eG[1])
_left_p = (-44.0 + _eG[0] * 6.2, 40.0 + _eG[1] * 6.2)
_TL = _isect(_top_p, _u, _left_p, _dG)
_TR = _isect(_top_p, _u, _right_p, _dA)
_BR = _isect(_right_p, _dA, _bot_p, _dS)
_B = _isect(_bot_p, _dS, (-26.0, 0.0), (0.0, 1.0))
_N1 = (round(_B[0] + _inS[0] * 9.0, 1), round(_B[1] + _inS[1] * 9.0, 1))
_NL = _isect(_N1, _dS, _left_p, _dG)
COURT = [_TL, _TR, _BR, _B, _N1, _NL]
SAND = []


def _at(t, s):      # point along the court axis (t) and depth from the top edge (s)
    return (round(_TL[0] + _u[0] * t + _v[0] * s, 2), round(_TL[1] + _u[1] * t + _v[1] * s, 2))


# (kind, centre, length, width)   lengths run along the court axis
SPORT = [
    ("basketball", _at(22.0, 13.0), 28.0, 15.0),
    ("futsal", _at(62.0, 17.0), 40.0, 20.0),
    ("takraw", _at(97.0, 9.5), 13.4, 6.1),
    ("takraw", _at(97.0, 21.5), 13.4, 6.1),
]

# buildings 6 and 7: identical 50 x 12 m, parallel to the road, just north of its sidewalk
for _n, _t in (("Building 6", 34.0), ("Building 7", 92.0)):
    _c = (_SR[0][0] + _u[0] * _t - _v[0] * 11.15, _SR[0][1] + _u[1] * _t - _v[1] * 11.15)
    _by[_n].update(cx=round(_c[0], 1), cz=round(_c[1], 1), len=50.0, wid=12, ang=round(COURT_ANG, 4),
                   floors=2, roof="#3f9a6a")

# school sign on the fence line, waterfall pond in front of it (outside the fence)
_sx = -37.5
_sz = CAMPUS[4][1] + (CAMPUS[3][1] - CAMPUS[4][1]) * (_sx - CAMPUS[4][0]) / (CAMPUS[3][0] - CAMPUS[4][0])
SIGN_ANG = math.atan2(-_dS[1], -_dS[0])                 # along the fence (west -> east)
_out = (-_inS[0], -_inS[1])
SIGN = dict(x=_sx, z=round(_sz, 1), w=18.0, h=4.0, ang=round(SIGN_ANG, 4))
WATERFALL = dict(x=round(_sx + _out[0] * 3.6, 1), z=round(_sz + _out[1] * 3.6, 1), ang=round(SIGN_ANG, 4))
SIGN_POS = (SIGN["x"], SIGN["z"])

# the service road no longer runs along the front fence between the two gates
_P = PERIM
_pe = _isect(_P[3], _unit(_P[4][0] - _P[3][0], _P[4][1] - _P[3][1]), (115.0, 5.0), _dA)
_pg = _isect(_P[3], _unit(_P[4][0] - _P[3][0], _P[4][1] - _P[3][1]), (-44.0, 40.0), _dG)
SECONDARY_ROADS[0] = ([_pe, _P[3], _P[2], _P[1], _P[0], _P[4], _pg], 5.0)
ROADS = SECONDARY_ROADS + MAIN_ROADS
SPORT = [
    ("basketball", _at(22.0, 13.5), 28.0, 15.0),
    ("futsal", _at(63.0, 24.0), 40.0, 20.0),
    ("takraw", _at(100.0, 15.0), 13.4, 6.1),
    ("takraw", _at(100.0, 29.0), 13.4, 6.1),
]
# 2026-11-19 (5): courts re-arranged per the user's rectangles (right -> left):
# futsal, basketball, sepak takraw (all turned 90°, long side across the slab), skateboard park
SPORT = [
    ("futsal", _at(101.0, 25.6), 40.0, 20.0, math.pi / 2),
    ("basketball", _at(72.7, 21.8), 28.0, 15.0, math.pi / 2),
    ("takraw", _at(49.6, 13.5), 13.4, 6.1, math.pi / 2),
    ("skate", _at(19.5, 11.8), 34.0, 18.0, 0.0),
]
# 2026-11-19 (6): remove auditorium + crossed buildings, new middle road gate-road -> east avenue
REMOVED |= {"Auditorium", "Red-roof hall", "Classroom block", "Science building"}
BUILDINGS = [b for b in BUILDINGS if b["en"] not in REMOVED]
CANOPIES = [c for c in CANOPIES if c["roof"] != "#d6383c"]          # red walkway to the removed hall
MAIN_ROADS[1] = ([(16.0, -144.0), (16.0, 4.8)], 6.0)                  # spine now meets the middle road
MAIN_ROADS.append(([(-42.0, -4.0), (110.1, 19.2)], 6.5))              # middle road
SECONDARY_ROADS = [SECONDARY_ROADS[0]]                                # old road south of the dome replaced
ROADS = SECONDARY_ROADS + MAIN_ROADS
# 2026-11-19 (7): two identical 2-storey auditoriums, swimming pool, large library (frame = middle road)
_MR0 = (-42.0, -4.0); _MA = math.atan2(23.2, 152.1)
_mu = (math.cos(_MA), math.sin(_MA)); _mv = (-_mu[1], _mu[0])


def _mid(t, s):
    return (round(_MR0[0] + _mu[0] * t + _mv[0] * s, 1), round(_MR0[1] + _mu[1] * t + _mv[1] * s, 1))


def _new(name_th, name_en, t, s, L_, W_, floors, fh, wall, roof, kind, portico):
    c = _mid(t, s)
    return dict(cx=c[0], cz=c[1], len=L_, wid=W_, ang=round(_MA, 4), floors=floors, fh=fh, wall=wall, roof=roof,
                type=kind, th=name_th, en=name_en, portico=portico)


BUILDINGS += [
    _new("หอประชุม 1", "Auditorium 1", 99.3, -24.0, 58.0, 24.0, 2, 5.5, "#f3ecdf", "#9c2f2f", "hip", 1),
    _new("หอประชุม 2", "Auditorium 2", 44.6, 24.0, 58.0, 24.0, 2, 5.5, "#f3ecdf", "#9c2f2f", "hip", -1),
    _new("ห้องสมุด", "Library", 108.0, 32.7, 58.0, 44.0, 3, 4.2, "#f4f3ef", "#e9e7e2", "flat", -1),
]
_pc = _mid(46.4, 48.0)
POOL = dict(cx=_pc[0], cz=_pc[1], len=54.0, wid=18.0, ang=round(_MA, 4), wlen=50.0, wwid=12.5)
# 2026-11-19 (8): student motorcycle sheds + guard booth by the main gate (frame = front fence at the gate)
_fe = (math.cos(0.3774), math.sin(0.3774)); _fn = (_fe[1], -_fe[0])          # along fence (east), inward (north)


def _fence(a, d):
    return (round(GATE["x"] + _fe[0] * a + _fn[0] * d, 1), round(GATE["z"] + _fe[1] * a + _fn[1] * d, 1))


_FA = round(math.atan2(_fe[1], _fe[0]), 4)
SHEDS = []
for _a0, _a1, _d0, _d1 in ((-115.0, -48.0, 11.5, 16.5), (-115.0, -24.0, 3.5, 9.0)):
    _c = _fence((_a0 + _a1) / 2, (_d0 + _d1) / 2)
    SHEDS.append(dict(cx=_c[0], cz=_c[1], len=_a1 - _a0, wid=_d1 - _d0, ang=_FA, h=3.0))
_g = _fence(-12.0, 7.0)
GUARD = dict(cx=_g[0], cz=_g[1], len=4.5, wid=3.5, ang=_FA, barrier=_fence(-5.5, 9.0))
# the service road no longer runs along the fence west of the gate (the sheds use that strip)
SECONDARY_ROADS[0] = (SECONDARY_ROADS[0][0][:-1], SECONDARY_ROADS[0][1])
ROADS = SECONDARY_ROADS + MAIN_ROADS
# 2026-11-19 (9): old long white stand removed; inner motorcycle shed now full length like the outer one
CANOPIES = [c for c in CANOPIES if c["roof"] != "#e6e8ea"]
_c = _fence((-115.0 + -24.0) / 2, (11.5 + 16.5) / 2)
SHEDS[0].update(cx=_c[0], cz=_c[1], len=91.0)
# 2026-11-19 (10): east strip — canteen (2 floors), two classroom blocks, auditorium 3, student shop
_A0 = (115.0, 5.0); _dA2 = _unit(62.2 - 115.0, 158.6 - 5.0); _nE = (-_dA2[1], _dA2[0])
if _nE[0] < 0: _nE = (-_nE[0], -_nE[1])
_AANG = round(math.atan2(_dA2[1], _dA2[0]), 4)


def _av(t, s):
    return (round(_A0[0] + _dA2[0] * t + _nE[0] * s, 1), round(_A0[1] + _dA2[1] * t + _nE[1] * s, 1))


def _bx(th, en, c, L_, W_, ang, floors, fh, wall, roof, kind, **kw):
    return dict(cx=c[0], cz=c[1], len=L_, wid=W_, ang=round(ang, 4), floors=floors, fh=fh, wall=wall, roof=roof,
                type=kind, th=th, en=en, **kw)


_NEd = _unit(CAMPUS[2][0] - CAMPUS[1][0], CAMPUS[2][1] - CAMPUS[1][1]); _NEn = (_NEd[1], -_NEd[0])     # outward
_cant = (PERIM[1][0] + _NEd[0] * 78.0 - _NEn[0] * 17.0, PERIM[1][1] + _NEd[1] * 78.0 - _NEn[1] * 17.0)
_shop = (98.0 + 0.368 * 10.0, 172.9 - 0.930 * 10.0)
BUILDINGS += [
    _bx("โรงอาหาร", "Canteen", (round(_cant[0], 1), round(_cant[1], 1)), 55.0, 26.0, math.atan2(_NEd[1], _NEd[0]),
        2, 4.5, "#f6efe2", "#c8692f", "gable", portico=None, open_ground=True),
    _bx("อาคารเรียน 8", "Building 8", (142.0, -3.0), 52.0, 22.0, 1.62, 4, 3.5, "#eef2f2", "#3f8a5a", "gable"),
    _bx("อาคารเรียน 9", "Building 9", _av(39.0, 30.0), 55.0, 28.0, _AANG, 4, 3.5, "#eef2f2", "#3f8a5a", "gable"),
    _bx("หอประชุม 3", "Auditorium 3", _av(106.0, 29.0), 70.0, 34.0, _AANG, 2, 5.5, "#f3ecdf", "#9c2f2f", "hip", portico=1),
    _bx("ร้านค้าฝึกประสบการณ์", "Student shop", (round(_shop[0], 1), round(_shop[1], 1)), 26.0, 14.0, 0.3774,
        1, 4.0, "#fff6e6", "#2f6fd0", "gable", shopfront=-1),
]
SECONDARY_ROADS[0] = (SECONDARY_ROADS[0][0][1:], SECONDARY_ROADS[0][1])        # drop the leg along the south fence
ROADS = SECONDARY_ROADS + MAIN_ROADS
# 2026-11-19 (11): east strip redo per the user's rectangles — smaller auditorium 3, two slimmer classroom blocks
BUILDINGS = [b for b in BUILDINGS if b["en"] not in ("Building 8", "Building 9", "Auditorium 3")]
BUILDINGS += [
    _bx("อาคารเรียน 8", "Building 8", _av(-13.5, 26.6), 40.0, 12.5, _AANG, 4, 3.5, "#eef2f2", "#3f8a5a", "gable"),
    _bx("อาคารเรียน 9", "Building 9", _av(37.5, 27.0), 40.0, 14.0, _AANG, 4, 3.5, "#eef2f2", "#3f8a5a", "gable"),
    _bx("หอประชุม 3", "Auditorium 3", _av(111.5, 30.5), 49.0, 27.0, _AANG, 2, 5.5, "#f3ecdf", "#9c2f2f", "hip", portico=1),
]
# 2026-11-19 (12): first-aid room between the brown building and the middle road
BUILDINGS.append(_bx("ห้องปฐมพยาบาล", "First-aid room", (5.0, -8.8), 11.0, 8.5, 0.0, 1, 3.6, "#fbfbf8", "#d6383c", "gable", clinic=1))
# 2026-11-20: bigger guard booth (old one replaced), blue drop-off canopy over the gate road, Thai sala (grey-red)
_gd = _fence(-13.5, 5.5)
GUARD = dict(cx=_gd[0], cz=_gd[1], len=9.0, wid=7.0, ang=_FA, barrier=_fence(-5.5, 9.0))
_dGu = _unit(-44.0 - -55.5, 40.0 - 112.0)
_dc = (GATE["x"] + _dGu[0] * 15.0, GATE["z"] + _dGu[1] * 15.0)
DROPOFF = dict(cx=round(_dc[0], 1), cz=round(_dc[1], 1), len=15.0, wid=11.0, ang=round(math.atan2(_dGu[1], _dGu[0]), 4), h=5.2)
_sl = _fence(13.0, 7.5)
SALA = dict(cx=_sl[0], cz=_sl[1], len=11.0, wid=8.0, ang=_FA, name="ศาลารวมใจศิษย์เทา-แดง")
# 2026-11-20 (2): LED screen at the front fence beside the main gate (faces the ring road)
_ld = _fence(-11.0, 1.2)
LED = dict(cx=_ld[0], cz=_ld[1], len=7.0, wid=1.2, ang=_FA, text="Welcome to Phibunmangsahan School", clock="07:30 น.")
# 2026-11-20 (3): the real "ศาลารวมใจ 55 ปี เทาแดง 2561" beside the football field replaces the track office
_by['Track office'].update(type="sala55", th="ศาลารวมใจ 55 ปี เทาแดง 2561", en="Sala 55th anniversary", len=16.0, wid=8.5,
                           floors=2, fh=3.4, wall="#efe6cf", roof="#3f6b4e")
# 2026-11-20 (4): หอประชุมศรีวนาลัย (real photos) — gable end faces the road; auditorium 1 shares the design
_by2 = {b['en']: b for b in BUILDINGS}
_by2['Auditorium 2'].update(type="sriwanalai", th="หอประชุมศรีวนาลัย", en="SRIWANALAI HALL", len=34.0, wid=24.0, floors=3, fh=4.3,
                            wall="#e8414a", roof="#e23b45")
_by2['Auditorium 1'].update(type="sriwanalai", en="AUDITORIUM 1", len=34.0, wid=24.0, floors=3, fh=4.3, wall="#e8414a", roof="#e23b45")
_c1 = _mid(99.3, -25.6); _c2 = _mid(44.6, 25.6)
_by2['Auditorium 1'].update(cx=_c1[0], cz=_c1[1]); _by2['Auditorium 2'].update(cx=_c2[0], cz=_c2[1])
# 2026-11-20 (5): Sriwanalai Hall turned to face west (towards the gate road) with a wide asphalt plaza in front
_c2 = _mid(43.4, 21.2)
_by2['Auditorium 2'].update(cx=_c2[0], cz=_c2[1], len=30.0, wid=24.0, ang=round(_MA + math.pi / 2, 4), portico=1)
PLAZAS = [[_mid(4.0, 4.7), _mid(22.5, 4.7), _mid(22.5, 37.5), _mid(9.5, 37.5)]]
# 2026-11-20 (6): หอประชุมราษฎร์รังสรรค์ (auditorium 1) faces east towards the avenue, concrete plaza in front
_by2['Auditorium 1'].update(th="หอประชุมราษฎร์รังสรรค์", en="", cx=40.0, cz=-13.6, len=30.0, wid=24.0, ang=round(-math.pi / 2, 4), portico=1)
PLAZAS = [dict(pts=PLAZAS[0], kind="asphalt"),
          dict(pts=[(57.0, -28.5), (86.0, -28.5), (108.0, 5.5), (102.0, 12.6), (57.0, 5.8)], kind="concrete")]
# 2026-11-20 (7): both halls made longer (40 m deep) per the user's boxes
_c2 = _mid(51.4, 21.2)
_by2['Auditorium 2'].update(cx=_c2[0], cz=_c2[1], wid=40.0)
_by2['Auditorium 1'].update(cx=48.0, wid=40.0)
PLAZAS[1]['pts'] = [(76.5, -28.5), (86.0, -28.5), (108.0, 5.5), (102.0, 12.6), (76.5, 8.8)]
# 2026-11-20 (8): Ratrangsan hall turned parallel to the middle road, slimmer (24 m) so it clears the green rows
_cR = _mid(85.0, -18.2)
_by2['Auditorium 1'].update(cx=_cR[0], cz=_cR[1], len=24.0, wid=40.0, ang=round(_MA - math.pi / 2, 4), portico=1)
PLAZAS[1]['pts'] = [_mid(113.0, -30.2), _mid(128.0, -30.2), (108.0, 5.5), (102.0, 12.6), _mid(113.0, -5.2)]
# 2026-11-20 (9): Ratrangsan Hall is single-storey — its own design (type hall1f)
_by2['Auditorium 1'].update(type="hall1f", floors=1, fh=7.5, wall="#f4eee2", roof="#c62f37")
_cR = _mid(85.0, -21.6)
_by2['Auditorium 1'].update(cx=_cR[0], cz=_cR[1])
# 2026-11-20 (10): ตึก IEP Programme (real photos) — building 6 becomes the pink 4-storey IEP block,
# 10 m deep, pulled 1.5 m back from the court road to leave a hedge strip with the WELCOME letters
_by2['Building 6'].update(type="iep", th="ตึก IEP Programme", en="IEP Programme", floors=4, fh=3.6, wid=10.0,
                          wall="#f2a7b5", roof="#cf5f63",
                          cx=round(_SR[0][0] + _u[0] * 34 - _v[0] * 12.65, 2), cz=round(_SR[0][1] + _u[1] * 34 - _v[1] * 12.65, 2))
# 2026-11-20 (11): ตึก ICT Department (real photos) — building 7 becomes the twin of the IEP block, mirrored
# (stair tower with "ICT DEPARTMENT" at the east end), stone relief wall + blue sign + frangipani in front
_by2['Building 7'].update(type="ict", sign="ICT", mirror=1, th="ตึก ICT Department", en="ICT Department", floors=4, fh=3.6, wid=10.0,
                          wall="#f2a7b5", roof="#cf5f63",
                          cx=round(_SR[0][0] + _u[0] * 92 - _v[0] * 12.65, 2), cz=round(_SR[0][1] + _u[1] * 92 - _v[1] * 12.65, 2))
# 2026-11-20 (12): ศูนย์ฝึกทักษะอาชีพ (real photos) — red shop with glass front opening onto the street at the front
# fence (fence gap), side terrace, green curved motorcycle canopy, white boundary wall
_n_f = (-math.sin(0.3774), math.cos(0.3774))
_by2['Student shop'].update(type="vshop", th="ศูนย์ฝึกทักษะอาชีพโรงเรียนพิบูลมังสาหาร", en="Career Skills Centre", len=26.0, wid=14.0,
                            cx=round(98.0 - _n_f[0] * 7.2, 2), cz=round(172.9 - _n_f[1] * 7.2, 2), fenceGap=1,
                            floors=1, fh=4.2, wall="#d81e25", roof="#c41a20", shopfront=None)
# 2026-11-20 (13): โดมระหว่างอาคารเรียน (real photos) — the red barrel-roof dome between classroom blocks 4 and 5,
# replaces the old small red-roof room; tiled steps up from the west road, open underneath (walkable)
_by2['Nurse room'].update(type="arcdome", th="โดมระหว่างอาคารเรียน", en="Courtyard dome", cx=36.0, cz=-53.65, len=27.0, wid=13.0,
                          ang=0.0, floors=1, fh=7.0, wall="#9aa0a4", roof="#d8332b", open_ground=True)
# 2026-11-20 (14): โรงอาหารครบรอบ 60 ปี (real photos) — white 2-storey open canteen, red low gable roof with
# white soffit, open balconies with salmon railings, sign block + exterior stair at the west end, white tiled
# plaza; the Buddha shrine moves along the front so it stands to the right of the stair as in the photo
_by2['Canteen'].update(type="canteen60", th="โรงอาหารครบรอบ 60 ปี", en="60th Anniversary Canteen", fh=4.3, roof="#c8574a", wall="#f2f2ee")
_cb = _by2['Canteen']; _ca, _sa = math.cos(_cb['ang']), math.sin(_cb['ang'])
BUDDHA.update(x=round(_cb['cx'] + _ca * -11.0 - _sa * 18.0, 2), z=round(_cb['cz'] + _sa * -11.0 + _ca * 18.0, 2))
BUDDHA.update(rot=round(-_cb['ang'], 4))
# 2026-11-20 (15): covered walkways (curved metal roofs) linking classroom blocks across the roads, per the user's
# red lines: block 2 ↔ 3, block 3 ↔ 4, block 1 ↔ brown-roof building
def _walk(x, z0, z1, w=3.4):
    return dict(cx=x, cz=round((z0 + z1) / 2, 2), len=round(abs(z1 - z0), 2), wid=w, ang=round(math.pi / 2, 4))
WALKWAYS = [_walk(44.0, -128.0, -104.9), _walk(44.0, -92.9, -74.8), _walk(1.5, -128.0, -102.5)]
# 2026-11-20 (16): no posts on the roads — each walkway gets an explicit post list (local metres along it) that
# skips the carriageway + sidewalks; the block-1 ↔ brown-roof link becomes a 2nd-floor sky bridge over the road
def _seg_d(p, a, b):
    dx, dz = b[0] - a[0], b[1] - a[1]; t = max(0.0, min(1.0, ((p[0] - a[0]) * dx + (p[1] - a[1]) * dz) / (dx * dx + dz * dz)))
    return math.hypot(p[0] - a[0] - t * dx, p[1] - a[1] - t * dz)


def _on_road(x, z, margin=1.9):
    return any(_seg_d((x, z), a, b) < rw / 2 + margin for pts, rw in ROADS for a, b in zip(pts, pts[1:]))


def _posts(w, step=3.2):
    ca, sa = math.cos(w['ang']), math.sin(w['ang'])
    n = max(2, round(w['len'] / step)); out = []
    for i in range(n + 1):
        t = -w['len'] / 2 + i * w['len'] / n
        if not _on_road(w['cx'] + ca * t, w['cz'] + sa * t): out.append(round(t, 2))
    return out


WALKWAYS[2].update(kind="bridge", level=3.6, wid=3.2)
for _w in WALKWAYS: _w['posts'] = _posts(_w, 5.0 if _w.get('kind') == 'bridge' else 3.2)
# 2026-11-20 (17): courtyard dome shortened to the user's box (x 22.5–39.8), old teal canopy removed, and a covered
# walkway crosses between blocks 4 and 5 just north of it
_by2['Nurse room'].update(cx=31.15, len=17.3)
CANOPIES = [c for c in CANOPIES if c['roof'] != '#3cc4b5']
WALKWAYS.append(_walk(44.8, -62.8, -44.5, 3.5))
WALKWAYS[-1]['posts'] = _posts(WALKWAYS[-1])

# 2026-11-21: the gate-side sala is ศาลาแห่งความฮักแพง พี่มีให้น้อง (real photos)
SALA.update(name='ศาลาแห่งความฮักแพง พี่มีให้น้อง')

# ======================================================================================================
# 2026-11-21 (roads): new internal road network traced from the teacher's red lines on the satellite image
# (mapped via a 5-corner homography), and every interior building moved with a thin-plate warp anchored on
# the old→new road junctions, then pushed clear of the carriageways.
import numpy as _np
_OLD_ROADS = ROADS
MAIN_ROADS = [
    ([(46.0, -164.0), (46.0, -150.0), (64.0, -106.6), (85.0, -75.4), (118.0, -22.8), (119.7, -11.6), (107.0, 50.1), (97.0, 111.8), (80.0, 165.8)], 7.0),
    ([(61.0, -107.0), (8.5, -100.8), (-40.7, -93.7), (-41.8, -70.9), (-24.6, -39.8), (-19.6, -15.7), (-36.2, 49.5), (-55.5, 112.0)], 6.5),
    ([(85.0, -75.4), (24.0, -70.5)], 6.0),
    ([(8.5, -100.8), (39.1, -40.8), (53.4, -18.7), (54.0, 8.8)], 6.0),
    ([(-19.6, -15.7), (14.2, -9.8), (56.8, 10.6), (107.0, 50.1)], 6.5),
    ([(-36.2, 49.5), (97.0, 111.8)], 6.5),
]
SECONDARY_ROADS = []
ROADS = SECONDARY_ROADS + MAIN_ROADS
GATES[1].update(x=80.0, z=165.8)
GATES[2].update(x=46.0, z=-150.0, out=(46.0, -164.0))

# ---- buildings re-placed block by block from the rectified satellite image (plan metres)
_OLD_WALK = [dict(w) for w in WALKWAYS]
_PLACE = {   # index: (cx, cz, ang, len, wid)  — None keeps the current value
    0: (-30.2, -122.1, -0.157, 49.5, 11.1),     # 2026-11-22: redrawn by the teacher, parallel to the road          # north row, flagpole in front
    1: (18.7, -129.8, -0.157, 34.0, 11.1),
    6: (92.0, -122.0, 0.0, None, None),
    2: (45.0, -88.5, -0.10, 36.0, None),          # between the north road and road N3
    3: (61.0, -60.0, -0.08, 42.0, None),          # south of N3
    5: (55.0, -47.5, -0.08, None, None),          # courtyard dome between 3 and 4
    4: (76.0, -35.0, -0.08, 42.0, None),
    13: (85.0, -8.0, -1.42, None, None),          # hall, light roof on the satellite
    21: (38.0, -20.0, 1.0, None, None),
    7: (-8.0, -56.0, 1.12, 66.0, None),          # red-roof dome gym along the diagonal
    8: (14.64, -60.29, 1.12, 62.0, None),
    16: (116.0, -62.0, 1.01, None, None),         # canteen, east of road E
    18: (148.0, 5.0, 1.9, None, None),
    19: (132.0, 49.0, 1.9, None, None),
    20: (121.5, 121.0, 1.9, None, 24.0),
    9: (-1.0, 46.6, 0.437, 44.0, None),            # IEP / ICT: the two white roofs along road C
    10: (51.5, 71.1, 0.437, 44.0, None),
    14: (18.0, 20.0, 2.007, None, None),
    15: (64.0, 51.0, 0.437, 46.0, 32.0),
    11: (-52.0, -46.0, 1.5708, None, None),
    12: (-52.0, -28.0, 1.5708, None, None),
}
for _i, (_x, _z, _a, _l, _w) in _PLACE.items():
    _b = BUILDINGS[_i]; _b.update(cx=_x, cz=_z, ang=_a)
    if _l: _b['len'] = _l
    if _w: _b['wid'] = _w
POOL.update(cx=-46.0, cz=22.0, ang=1.82)
PLAZAS = [dict(pts=[(-58.0, -18.0), (-32.0, -18.0), (-32.0, -7.0), (-58.0, -7.0)], kind='asphalt')]
COURT = [(-30.0, 60.0), (88.0, 116.0), (75.0, 158.0), (-26.0, 121.1), (-22.7, 112.7), (-42.0, 96.0)]
COURT_ANG = round(math.atan2(56.0, 118.0), 4)
SPORT = [('futsal', (46.0, 124.0), 40.0, 20.0, math.pi / 2), ('basketball', (22.0, 106.0), 28.0, 15.0, math.pi / 2),
         ('takraw', (2.0, 95.0), 13.4, 6.1, math.pi / 2), ('skate', (-18.0, 82.0), 34.0, 18.0, 0.0)]
FLAGPOLE.update(x=-28.9, z=-109.4)
PARKING = [(-54.0 + i * 4.6, -12.5) for i in range(5)]

# ---- push buildings clear of the roads (carriageway + sidewalk + 1 m)
def _rect(b, pad=0.0):
    c, s = math.cos(b['ang']), math.sin(b['ang']); hl, hw = b['len'] / 2 + pad, b['wid'] / 2 + pad
    return [(b['cx'] + c * u - s * v, b['cz'] + s * u + c * v) for u, v in ((-hl, -hw), (hl, -hw), (hl, hw), (-hl, hw))]
def _in_rect(p, b, pad=0.0):
    dx, dz = p[0] - b['cx'], p[1] - b['cz']; c, s = math.cos(b['ang']), math.sin(b['ang'])
    return abs(dx * c + dz * s) <= b['len'] / 2 + pad and abs(-dx * s + dz * c) <= b['wid'] / 2 + pad
def _road_push(b, clear):
    """smallest push vector that gets the rectangle `clear` m away from every road centreline segment"""
    best = None
    for pts, rw in ROADS:
        need = rw / 2 + clear
        for a, e in zip(pts, pts[1:]):
            dx, dz = e[0] - a[0], e[1] - a[1]; Lg = math.hypot(dx, dz); ux, uz = dx / Lg, dz / Lg; nx, nz = -uz, ux
            corners = _rect(b)
            ts = [((q[0] - a[0]) * ux + (q[1] - a[1]) * uz) for q in corners]
            if max(ts) < 0 or min(ts) > Lg: continue
            ds = [((q[0] - a[0]) * nx + (q[1] - a[1]) * nz) for q in corners]
            lo, hi = min(ds), max(ds)
            if hi < -need or lo > need: continue
            push = (need - lo) if abs(need - lo) < abs(-need - hi) else (-need - hi)
            if best is None or abs(push) > abs(best[0]): best = (push, nx, nz)
    return best
# ---- walkways: keep each link's direction, re-snap both ends onto the faces of the blocks it joins
_WPAIRS = [(1, 2), (2, 3), (0, 8), (3, 4)]
WALKWAYS = []
for _w, (_i, _j) in zip(_OLD_WALK, _WPAIRS):
    _bi, _bj = BUILDINGS[_i], BUILDINGS[_j]
    _m = ((_bi['cx'] + _bj['cx']) / 2, (_bi['cz'] + _bj['cz']) / 2)
    _d = (_bj['cx'] - _bi['cx'], _bj['cz'] - _bi['cz'])
    # run perpendicular to the first block's long axis, towards the second block
    _nx, _nz = -math.sin(_bi['ang']), math.cos(_bi['ang'])
    if _nx * _d[0] + _nz * _d[1] < 0: _nx, _nz = -_nx, -_nz
    # start on the first block's face, at the point of its axis nearest the second block's centre
    _ca, _sa = math.cos(_bi['ang']), math.sin(_bi['ang'])
    _t = max(-_bi['len'] / 2 + 3, min(_bi['len'] / 2 - 3, (_bj['cx'] - _bi['cx']) * _ca + (_bj['cz'] - _bi['cz']) * _sa))
    _s0 = (_bi['cx'] + _ca * _t + _nx * _bi['wid'] / 2, _bi['cz'] + _sa * _t + _nz * _bi['wid'] / 2)
    _k = 0.0
    while _k < 80 and not _in_rect((_s0[0] + _nx * _k, _s0[1] + _nz * _k), _bj): _k += 0.1
    if _k >= 80: continue
    _e = (_s0[0] + _nx * _k, _s0[1] + _nz * _k)
    _nw = dict(_w, cx=round((_s0[0] + _e[0]) / 2, 2), cz=round((_s0[1] + _e[1]) / 2, 2), len=round(_k, 2), ang=round(math.atan2(_nz, _nx), 4))
    _nw['posts'] = _posts(_nw, 5.0 if _nw.get('kind') == 'bridge' else 3.2)
    WALKWAYS.append(_nw)

_cb = _by2['Canteen']; _ca, _sa = math.cos(_cb['ang']), math.sin(_cb['ang'])
# road E now runs close in front of the canteen, so the shrine stands just past its west (stair) end
BUDDHA.update(x=round(_cb['cx'] + _ca * -33.0 - _sa * 8.0, 2), z=round(_cb['cz'] + _sa * -33.0 + _ca * 8.0, 2), rot=round(-_cb['ang'], 4))

# 2026-11-21 (roads 2): canteen pushed back from road E to the teacher's red box (9.3 m towards its west end,
# 7 m back towards the fence); the Buddha shrine moves to the open forecourt in front of it
_cb = _by2['Canteen']; _ca, _sa = math.cos(_cb['ang']), math.sin(_cb['ang'])
def _cl(u, v): return (round(_cb['cx'] + _ca * u - _sa * v, 2), round(_cb['cz'] + _sa * u + _ca * v, 2))
_cb['cx'], _cb['cz'] = _cl(-9.3, -7.0)
_ca, _sa = math.cos(_cb['ang']), math.sin(_cb['ang'])
BUDDHA.update(zip(('x', 'z'), _cl(-15.0, 18.5)), rot=round(-_cb['ang'], 4))

# 2026-11-22: หอประชุมพิบูลประชาสรรค์ (building 20) shortened to the teacher's red box and slid towards the
# vocational-training centre: 49 m -> 36 m long, 26 m wide, centre 22.7 m along its axis + 2.7 m east
_h = BUILDINGS[20]; _hc, _hs = math.cos(_h['ang']), math.sin(_h['ang'])
_h.update(cx=round(_h['cx'] + _hc * 22.7 + _hs * 2.7, 2), cz=round(_h['cz'] + _hs * 22.7 - _hc * 2.7, 2), len=36.0, wid=26.0)
_h.update(th='หอประชุมพิบูลประชาสรรค์', en='Phibun Prachasan Auditorium')
_h.update(cx=round(_h['cx'] - _hc * 0.8, 2), cz=round(_h['cz'] - _hs * 0.8, 2))   # keep ~2.4 m from the training centre

# 2026-11-27: grey-roofed block next to หอประชุมราษฎร์รังสรรค์ seen on the satellite (with a small annex on its
# west face). Kept small so อาคาร 5 stays (teacher's choice); the hall slides 5 m south to make room.
BUILDINGS[13]['cz'] = -3.0
BUILDINGS.append(dict(BUILDINGS[4], cx=98.0, cz=-21.5, len=13.0, wid=12.0, ang=-1.42, floors=2, fh=3.5,
                      wall='#eef0ee', roof='#b8bcbf', th='อาคารหลังคาเทา', en='Grey-roof block'))
BUILDINGS.append(dict(BUILDINGS[4], cx=90.39, cz=-24.68, len=7.0, wid=4.0, ang=-1.42, floors=1, fh=3.2,
                      wall='#eef0ee', roof='#a9adb0', th='ห้องข้างอาคารหลังคาเทา', en='Annex'))

# 2026-11-27: swimming pool removed; trees cleared where the teacher crossed them out (around the old pool,
# between the car park and the gym, and west of หอประชุมราษฎร์รังสรรค์)
POOL = None
NO_TREES = [[(-73.4, 63.1), (-64.4, -15.2), (-4.5, -6.2), (-13.5, 72.0)], [(-54.3, -22.4), (-51.3, -49.0), (-17.9, -44.0), (-20.9, -17.4)], [(82.1, 34.4), (85.2, 7.8), (117.2, 12.6), (114.1, 39.1)]]

# 2026-11-27: the bent road past หอประชุมศรีวนาลัย becomes one straight road from the junction by the gym to road E;
# the car park beside the football field is removed; a wide asphalt forecourt in front of หอประชุมศรีวนาลัย
MAIN_ROADS[4] = ([(-19.6, -15.7), (110.5, 33.0)], 6.5)
MAIN_ROADS[3] = (MAIN_ROADS[3][0][:-1] + [(54.0, 11.8)], MAIN_ROADS[3][1])
ROADS = SECONDARY_ROADS + MAIN_ROADS
PARKING = []
_d = (-0.2467, 0.9691); _n = (0.9691, 0.2467)
def _fp(t, o): return (round(-19.6 + _d[0] * t + _n[0] * o, 2), round(-15.7 + _d[1] * t + _n[1] * o, 2))
PLAZAS = [dict(pts=[_fp(4, 5.5), _fp(4, 23.5), _fp(42, 23.5), _fp(42, 5.5)], kind='asphalt')]
_sw = _by2['Assembly hall 2'] if 'Assembly hall 2' in _by2 else [b for b in BUILDINGS if b.get('type') == 'sriwanalai'][0]
_sw.update(cx=round(_sw['cx'] - 0.350 * 3.6, 2), cz=round(_sw['cz'] + 0.937 * 3.6, 2))   # keep the straight road clear
PLAZAS = [dict(pts=[_fp(4, 5.5), _fp(4, 22.0), _fp(42, 22.0), _fp(42, 5.5)], kind='asphalt')]

# 2026-11-27: three halls trimmed/moved to the teacher's red boxes
for _th, _v in {'หอประชุมราษฎร์รังสรรค์': dict(cx=74.4, cz=3.67, len=14.6, wid=30.0),
                'ห้องสมุด': dict(cx=68.76, cz=43.84, len=39.1, wid=25.0, th='โรงฝึกงานหลังคาสีขาว', en='White-roof workshop'),
                'หอประชุมศรีวนาลัย': dict(cx=16.92, cz=19.23, len=25.5, wid=35.6)}.items():
    [b for b in BUILDINGS if b.get('th') == _th][0].update(_v)
[b for b in BUILDINGS if b.get('th') == 'หอประชุมราษฎร์รังสรรค์'][0].update(cz=1.8)   # keep the pavement clear
[b for b in BUILDINGS if b.get('th') == 'หอประชุมราษฎร์รังสรรค์'][0].update(cx=75.9)

# 2026-11-27: the grey block is the school library — rebuilt as a two-storey library to the teacher's box, entrance
# facing road E (local +z = east); its small annex is merged in
BUILDINGS = [b for b in BUILDINGS if b.get('th') != 'ห้องข้างอาคารหลังคาเทา']
[b for b in BUILDINGS if b.get('th') == 'อาคารหลังคาเทา'][0].update(type='library', th='ห้องสมุด', en='Library', cx=101.0, cz=-18.0, len=17.0, wid=16.0, ang=-1.42)
[b for b in BUILDINGS if b.get('th') == 'ห้องสมุด'][0].update(cx=99.5, cz=-16.0, len=16.0)

# 2026-11-27: more trees cleared around หอประชุมราษฎร์รังสรรค์ (teacher's crosses)
NO_TREES = NO_TREES + [[(49.3, 12.1), (53.8, 14.8), (55.1, 19.9), (52.4, 24.4), (47.3, 25.7), (42.8, 23.1), (41.5, 18.0), (44.2, 13.4)], [(63.2, 16.0), (66.3, 17.9), (67.2, 21.4), (65.3, 24.5), (61.8, 25.4), (58.7, 23.6), (57.8, 20.0), (59.6, 16.9)], [(74.4, 19.5), (77.9, 21.6), (78.9, 25.5), (76.8, 29.0), (72.9, 30.0), (69.4, 27.9), (68.4, 24.0), (70.5, 20.5)], [(84.0, 23.3), (87.9, 25.6), (89.0, 29.9), (86.7, 33.7), (82.4, 34.8), (78.5, 32.5), (77.4, 28.2), (79.7, 24.4)], [(86.1, 8.6), (90.0, 10.9), (91.1, 15.2), (88.8, 19.0), (84.5, 20.1), (80.7, 17.9), (79.6, 13.6), (81.8, 9.7)], [(65.0, -15.0), (68.8, -12.7), (69.9, -8.4), (67.6, -4.6), (63.3, -3.5), (59.5, -5.8), (58.4, -10.1), (60.6, -13.9)], [(73.9, -13.7), (77.3, -11.7), (78.3, -7.7), (76.3, -4.3), (72.4, -3.3), (68.9, -5.3), (67.9, -9.2), (69.9, -12.7)], [(81.8, -13.1), (85.3, -11.1), (86.3, -7.1), (84.2, -3.6), (80.3, -2.6), (76.8, -4.7), (75.8, -8.6), (77.9, -12.1)], [(89.5, -14.7), (92.3, -13.0), (93.1, -9.9), (91.4, -7.1), (88.3, -6.3), (85.5, -8.0), (84.7, -11.1), (86.4, -13.9)], [(103.3, -3.1), (107.2, -0.8), (108.3, 3.5), (106.0, 7.4), (101.7, 8.5), (97.8, 6.2), (96.7, 1.9), (99.0, -2.0)], [(110.8, -13.8), (115.6, -10.9), (117.0, -5.4), (114.1, -0.5), (108.6, 0.9), (103.8, -2.0), (102.4, -7.5), (105.3, -12.4)], [(122.7, 18.4), (127.9, 21.5), (129.4, 27.4), (126.3, 32.6), (120.4, 34.1), (115.2, 31.0), (113.7, 25.2), (116.8, 19.9)], [(125.3, 0.1), (130.5, 3.2), (132.0, 9.1), (128.9, 14.3), (123.1, 15.8), (117.8, 12.7), (116.3, 6.8), (119.4, 1.6)], [(127.5, -18.8), (132.7, -15.7), (134.2, -9.8), (131.1, -4.6), (125.3, -3.1), (120.0, -6.2), (118.5, -12.1), (121.6, -17.3)], [(129.0, -28.8), (132.8, -26.5), (133.9, -22.2), (131.6, -18.4), (127.3, -17.3), (123.5, -19.5), (122.4, -23.8), (124.6, -27.7)]]

# 2026-11-27: concrete apron around the front and south side of หอประชุมราษฎร์รังสรรค์ (teacher's outline)
PLAZAS = PLAZAS + [dict(pts=[(69.0, 12.9), (79.4, 20.0), (91.0, 24.5), (108.2, 30.0), (111.5, 15.2), (117.5, -11.3), (115.7, -12.0), (111.1, -8.3), (109.3, -3.0), (104.4, -3.8), (99.9, 14.5), (92.9, 13.2), (88.9, 17.1), (82.8, 16.3), (71.4, 13.1)], kind='concrete')]
NO_TREES = NO_TREES + [[(69.0, 12.9), (79.4, 20.0), (91.0, 24.5), (108.2, 30.0), (111.5, 15.2), (117.5, -11.3), (115.7, -12.0), (111.1, -8.3), (109.3, -3.0), (104.4, -3.8), (99.9, 14.5), (92.9, 13.2), (88.9, 17.1), (82.8, 16.3), (71.4, 13.1)]]
def _push_off_roads(P, extra=2.6):
    """move polygon vertices so each sits at least kerb+pavement away from every road centreline"""
    def segd(p, a, b):
        dx, dz = b[0] - a[0], b[1] - a[1]; t = max(0, min(1, ((p[0] - a[0]) * dx + (p[1] - a[1]) * dz) / (dx * dx + dz * dz)))
        return math.hypot(p[0] - a[0] - t * dx, p[1] - a[1] - t * dz), (a[0] + t * dx, a[1] + t * dz)
    out = []
    for p in P:
        p = list(p)
        for _ in range(6):
            worst = None
            for pts, w in ROADS:
                for a, b in zip(pts, pts[1:]):
                    d, q = segd(p, a, b); need = w / 2 + extra
                    if d < need and (worst is None or need - d > worst[0]): worst = (need - d, q, d)
            if not worst: break
            gap, q, d = worst
            if d < 1e-6: break
            p[0] += (p[0] - q[0]) / d * (gap + 0.05); p[1] += (p[1] - q[1]) / d * (gap + 0.05)
        out.append((round(p[0], 2), round(p[1], 2)))
    return out
PLAZAS[-1]['pts'] = _push_off_roads(PLAZAS[-1]['pts'], extra=0.4)   # concrete right up to the kerb (teacher)

# no trees on the hall plinth, portico or front steps
NO_TREES = NO_TREES + [[(57.25, 11.41), (60.94, -12.91), (103.45, -6.45), (99.76, 17.87)]]

# 2026-11-27: teacher's numbering of the classroom blocks
_ren = {'อาคาร 2': 'อาคาร 1', 'อาคาร 3': 'อาคาร 2', 'อาคาร 4': 'อาคาร 3', 'อาคาร 1': 'อาคาร 4'}
for _b in [b for b in BUILDINGS if b.get('th') in _ren]: _b['th'] = '\x00' + _ren[_b['th']]
for _b in BUILDINGS:
    if _b.get('th', '').startswith('\x00'): _b['th'] = _b['th'][1:]
for _b in BUILDINGS:
    if _b.get('th') == 'อาคารหลังคาน้ำตาล': _b['th'] = 'อาคาร 6'
    elif _b.get('th') == 'โรงยิมหลังคาโค้ง': _b['th'] = 'โดมอเนกประสงค์'
for _b in BUILDINGS:
    if _b.get('th') == 'อาคารเรียน 8': _b.update(th='อาคารเรียน 10 ห้องเรียนพิเศษ AP Program', en='Building 10 - AP Program')
for _b in BUILDINGS:
    if _b.get('type') == 'iep': _b['th'] = 'ห้องเรียนพิเศษ IEP Programme'
    elif _b.get('type') == 'ict': _b['th'] = 'ห้องเรียนพิเศษ MIT ICT Department'
for _b in BUILDINGS:
    if _b.get('type') == 'canteen60': _b['th'] = 'โรงอาหาร 2 ชั้น'
# concrete also on the strip between the hall's back end and road N4 (teacher's outline)
_strip = _push_off_roads([(56.0, -13.0), (62.6, -11.8), (59.3, 10.4), (69.0, 12.9), (64.0, 17.0), (56.0, 16.0)], extra=0.4)
PLAZAS = PLAZAS + [dict(pts=_strip, kind='concrete')]
NO_TREES = NO_TREES + [_strip]

# 2026-11-27: trees cleared at the teacher's crosses (whole-campus screenshot)
NO_TREES = NO_TREES + [[(133.6, -14.0), (127.1, -17.0), (124.7, -23.8), (127.7, -30.3), (134.5, -32.8), (141.0, -29.7), (143.4, -22.9), (140.3, -16.4)], [(130.2, 8.3), (123.7, 5.2), (121.2, -1.6), (124.3, -8.1), (131.1, -10.5), (137.6, -7.5), (140.0, -0.7), (136.9, 5.8)], [(127.0, 24.6), (120.5, 21.5), (118.1, 14.7), (121.2, 8.2), (127.9, 5.8), (134.4, 8.9), (136.8, 15.7), (133.8, 22.2)], [(116.0, 58.2), (109.5, 55.1), (107.1, 48.3), (110.2, 41.8), (116.9, 39.4), (123.4, 42.5), (125.8, 49.3), (122.8, 55.8)], [(114.5, 88.7), (108.0, 85.7), (105.6, 78.9), (108.7, 72.4), (115.4, 69.9), (121.9, 73.0), (124.4, 79.8), (121.3, 86.3)], [(111.2, 108.6), (104.7, 105.5), (102.3, 98.7), (105.4, 92.2), (112.1, 89.8), (118.6, 92.9), (121.0, 99.7), (118.0, 106.2)], [(104.3, 130.6), (97.8, 127.6), (95.4, 120.8), (98.4, 114.3), (105.2, 111.8), (111.7, 114.9), (114.1, 121.7), (111.0, 128.2)], [(95.0, 152.6), (88.5, 149.5), (86.1, 142.7), (89.2, 136.2), (95.9, 133.8), (102.4, 136.8), (104.8, 143.6), (101.8, 150.1)], [(111.3, -38.6), (104.8, -41.7), (102.4, -48.5), (105.4, -55.0), (112.2, -57.4), (118.7, -54.3), (121.1, -47.6), (118.0, -41.0)], [(100.5, -58.0), (94.0, -61.1), (91.6, -67.9), (94.6, -74.4), (101.4, -76.8), (107.9, -73.7), (110.3, -66.9), (107.2, -60.4)], [(94.8, -63.0), (88.4, -66.1), (85.9, -72.9), (89.0, -79.4), (95.8, -81.8), (102.2, -78.7), (104.7, -71.9), (101.6, -65.4)], [(85.6, -41.1), (79.1, -44.2), (76.7, -51.0), (79.7, -57.5), (86.5, -59.9), (93.0, -56.8), (95.4, -50.0), (92.3, -43.5)], [(83.0, -84.8), (76.5, -87.9), (74.1, -94.7), (77.1, -101.2), (83.9, -103.6), (90.4, -100.5), (92.8, -93.7), (89.7, -87.2)], [(70.9, -101.9), (64.4, -105.0), (62.0, -111.8), (65.0, -118.3), (71.8, -120.7), (78.3, -117.6), (80.7, -110.8), (77.7, -104.3)], [(64.7, -118.7), (58.2, -121.8), (55.7, -128.6), (58.8, -135.1), (65.6, -137.5), (72.1, -134.4), (74.5, -127.6), (71.4, -121.1)], [(67.1, -72.6), (60.6, -75.7), (58.2, -82.5), (61.3, -89.0), (68.0, -91.4), (74.5, -88.4), (77.0, -81.6), (73.9, -75.1)], [(67.9, -39.6), (61.4, -42.7), (59.0, -49.5), (62.0, -56.0), (68.8, -58.4), (75.3, -55.3), (77.7, -48.5), (74.6, -42.0)], [(43.0, -108.0), (36.5, -111.1), (34.1, -117.9), (37.2, -124.4), (43.9, -126.8), (50.4, -123.7), (52.8, -116.9), (49.8, -110.4)], [(44.7, 2.8), (38.2, -0.3), (35.8, -7.1), (38.9, -13.6), (45.6, -16.0), (52.1, -12.9), (54.5, -6.1), (51.5, 0.4)], [(45.5, 35.8), (39.0, 32.7), (36.5, 26.0), (39.6, 19.5), (46.4, 17.0), (52.9, 20.1), (55.3, 26.9), (52.2, 33.4)], [(40.3, 46.2), (33.8, 43.1), (31.3, 36.3), (34.4, 29.8), (41.2, 27.4), (47.7, 30.5), (50.1, 37.2), (47.0, 43.8)], [(18.2, -6.8), (11.7, -9.8), (9.2, -16.6), (12.3, -23.1), (19.1, -25.6), (25.6, -22.5), (28.0, -15.7), (24.9, -9.2)], [(5.3, -8.6), (-1.2, -11.7), (-3.6, -18.4), (-0.5, -25.0), (6.2, -27.4), (12.7, -24.3), (15.2, -17.5), (12.1, -11.0)], [(14.3, 48.4), (7.8, 45.3), (5.4, 38.5), (8.5, 32.0), (15.2, 29.6), (21.7, 32.7), (24.2, 39.5), (21.1, 46.0)], [(0.4, 44.2), (-6.1, 41.1), (-8.5, 34.3), (-5.4, 27.8), (1.3, 25.4), (7.8, 28.5), (10.3, 35.3), (7.2, 41.8)], [(2.9, -104.1), (-3.6, -107.2), (-6.0, -114.0), (-2.9, -120.5), (3.8, -122.9), (10.3, -119.8), (12.7, -113.0), (9.7, -106.5)], [(-48.0, -94.9), (-54.5, -98.0), (-56.9, -104.7), (-53.9, -111.2), (-47.1, -113.7), (-40.6, -110.6), (-38.2, -103.8), (-41.3, -97.3)], [(-42.3, -43.9), (-48.8, -47.0), (-51.2, -53.8), (-48.1, -60.3), (-41.4, -62.7), (-34.9, -59.6), (-32.4, -52.9), (-35.5, -46.4)], [(-37.1, -6.0), (-43.5, -9.1), (-46.0, -15.8), (-42.9, -22.4), (-36.1, -24.8), (-29.7, -21.7), (-27.2, -14.9), (-30.3, -8.4)], [(-48.8, -5.4), (-55.3, -8.5), (-57.7, -15.3), (-54.7, -21.8), (-47.9, -24.2), (-41.4, -21.1), (-39.0, -14.3), (-42.1, -7.8)], [(-29.1, 121.6), (-35.6, 118.6), (-38.0, 111.8), (-35.0, 105.3), (-28.2, 102.8), (-21.7, 105.9), (-19.3, 112.7), (-22.4, 119.2)], [(-39.1, 109.4), (-45.6, 106.3), (-48.0, 99.5), (-45.0, 93.0), (-38.2, 90.6), (-31.7, 93.6), (-29.3, 100.4), (-32.3, 106.9)], [(-57.9, 84.9), (-64.4, 81.8), (-66.8, 75.0), (-63.7, 68.5), (-57.0, 66.1), (-50.5, 69.1), (-48.1, 75.9), (-51.1, 82.4)], [(-65.7, 101.0), (-72.2, 97.9), (-74.6, 91.1), (-71.6, 84.6), (-64.8, 82.2), (-58.3, 85.2), (-55.9, 92.0), (-58.9, 98.5)], [(-81.0, 76.6), (-87.5, 73.6), (-89.9, 66.8), (-86.8, 60.3), (-80.1, 57.8), (-73.6, 60.9), (-71.1, 67.7), (-74.2, 74.2)], [(-101.7, 68.5), (-108.2, 65.5), (-110.6, 58.7), (-107.6, 52.2), (-100.8, 49.7), (-94.3, 52.8), (-91.9, 59.6), (-94.9, 66.1)], [(-129.6, 62.4), (-136.1, 59.4), (-138.5, 52.6), (-135.4, 46.1), (-128.7, 43.6), (-122.2, 46.7), (-119.8, 53.5), (-122.8, 60.0)], [(-147.8, 50.9), (-154.3, 47.8), (-156.7, 41.1), (-153.7, 34.6), (-146.9, 32.1), (-140.4, 35.2), (-138.0, 42.0), (-141.1, 48.5)], [(-158.7, 33.9), (-165.2, 30.8), (-167.7, 24.0), (-164.6, 17.5), (-157.8, 15.1), (-151.3, 18.2), (-148.9, 25.0), (-152.0, 31.5)]]

# 2026-11-27: public toilets between หอประชุมศรีวนาลัย and the white-roof workshop (teacher's red box), doors to the road
BUILDINGS.append(dict(type='toilet', th='ห้องน้ำ', en='Toilets', cx=45.6, cz=25.8, len=9.5, wid=13.0, ang=0.437, floors=1, fh=3.4))

# 2026-11-27: covered walkway (rain/sun shelter) along the track side of road W, from the bend by the
# multipurpose dome down past Sriwanalai and the IEP building to the drop-off canopy (teacher's red line)
def _side_path(pts, off):
    out = []
    for i, p in enumerate(pts):
        ds = []
        for a, b in ((pts[i - 1], p) if i > 0 else (p, pts[1]), (p, pts[i + 1]) if i < len(pts) - 1 else (pts[-2], p)):
            l = math.hypot(b[0] - a[0], b[1] - a[1]); ds.append(((b[0] - a[0]) / l, (b[1] - a[1]) / l))
        nx = sum(-d[1] for d in ds) / 2; nz = sum(d[0] for d in ds) / 2; nl = math.hypot(nx, nz)
        cosh = max(0.5, (ds[0][0] * ds[1][0] + ds[0][1] * ds[1][1] + 1) / 2) ** 0.5
        out.append((p[0] + nx / nl * off / cosh, p[1] + nz / nl * off / cosh))
    return out
_wc = [(-41.8, -70.9), (-24.6, -39.8), (-19.6, -15.7), (-36.2, 49.5), (-47.8, 87.0)]
_cand = [_side_path(_wc, 7.0), _side_path(_wc, -7.0)]
_wp = min(_cand, key=lambda P: sum(x for x, z in P))          # the track (west) side
for _a, _b in zip(_wp, _wp[1:]):
    _l = math.hypot(_b[0] - _a[0], _b[1] - _a[1])
    _w = dict(cx=round((_a[0] + _b[0]) / 2, 2), cz=round((_a[1] + _b[1]) / 2, 2), len=round(_l + 1.2, 2), wid=3.2,
              ang=round(math.atan2(_b[1] - _a[1], _b[0] - _a[0]), 4), kind='roadside')
    _w['posts'] = _posts(_w, 4.0)
    WALKWAYS.append(_w)

# 2026-11-27 (2): second roadside covered walkway, east side of road E, from the bend by the library down past
# the AP / classroom buildings to หอประชุมพิบูลประชาสรรค์ and the vocational centre (teacher's red line)
_wc2 = [(118.0, -22.8), (119.7, -11.6), (107.0, 50.1), (97.0, 111.8), (86.6, 142.0)]
_wp2 = max([_side_path(_wc2, 7.0), _side_path(_wc2, -7.0)], key=lambda P: sum(x for x, z in P))   # east side
for _a, _b in zip(_wp2, _wp2[1:]):
    _l = math.hypot(_b[0] - _a[0], _b[1] - _a[1])
    _w = dict(cx=round((_a[0] + _b[0]) / 2, 2), cz=round((_a[1] + _b[1]) / 2, 2), len=round(_l + 1.2, 2), wid=3.2,
              ang=round(math.atan2(_b[1] - _a[1], _b[0] - _a[0]), 4), kind='roadside')
    _w['posts'] = _posts(_w, 4.0)
    WALKWAYS.append(_w)

# 2026-11-27 (3): road-E shelters continue north: east side from the road-W junction past the canteen to the
# library bend (joins the earlier one), and west side from the junction up towards the north gate
_wc3 = [(68.0, -100.6), (85.0, -75.4), (118.0, -22.8)]
_wc4 = [(57.6, -121.5), (47.5, -146.0)]
_new = [max([_side_path(_wc3, 7.0), _side_path(_wc3, -7.0)], key=lambda P: sum(x for x, z in P)),
        min([_side_path(_wc4, 7.0), _side_path(_wc4, -7.0)], key=lambda P: sum(x for x, z in P))]
for _wp3 in _new:
    for _a, _b in zip(_wp3, _wp3[1:]):
        _l = math.hypot(_b[0] - _a[0], _b[1] - _a[1])
        _w = dict(cx=round((_a[0] + _b[0]) / 2, 2), cz=round((_a[1] + _b[1]) / 2, 2), len=round(_l + 1.2, 2), wid=3.2,
                  ang=round(math.atan2(_b[1] - _a[1], _b[0] - _a[0]), 4), kind='roadside')
        _w['posts'] = _posts(_w, 4.0)
        WALKWAYS.append(_w)

_cb = [b for b in BUILDINGS if b.get('type') == 'canteen60'][0]; _ca, _sa = math.cos(_cb['ang']), math.sin(_cb['ang'])
BUDDHA.update(x=round(_cb['cx'] + _ca * -15.0 - _sa * 15.2, 2), z=round(_cb['cz'] + _sa * -15.0 + _ca * 15.2, 2))   # step back from the new shelter

# 2026-11-27 (4): roadside shelters pulled in to the kerb (teacher) and a gap left in front of the Buddha shrine
WALKWAYS = [w for w in WALKWAYS if w.get('kind') != 'roadside']
def _shelter(cl, side, rw):
    off = rw / 2 + 0.35 + 1.6                                     # kerb + half the shelter width
    P = [_side_path(cl, off), _side_path(cl, -off)]
    return (min if side == 'W' else max)(P, key=lambda Q: sum(x for x, z in Q))
_runs = [(_wc, 'W', 6.5), (_wc2, 'E', 7.0), (_wc3, 'E', 7.0), (_wc4, 'W', 7.0)]
_bx, _bz = BUDDHA['x'], BUDDHA['z']
for _cl, _sd, _rw in _runs:
    _wp = _shelter(_cl, _sd, _rw)
    for _a, _b in zip(_wp, _wp[1:]):
        _l = math.hypot(_b[0] - _a[0], _b[1] - _a[1]); _ux, _uz = (_b[0] - _a[0]) / _l, (_b[1] - _a[1]) / _l
        _parts = [(0.0, _l)]
        _t = (_bx - _a[0]) * _ux + (_bz - _a[1]) * _uz; _d = abs(-(_bx - _a[0]) * _uz + (_bz - _a[1]) * _ux)
        if 0 < _t < _l and _d < 12: _parts = [(0.0, _t - 4.5), (_t + 4.5, _l)]      # open in front of the shrine
        for _t0, _t1 in _parts:
            if _t1 - _t0 < 2: continue
            _e0 = _t0 - (0.6 if _t0 == 0 else 0); _e1 = _t1 + (0.6 if _t1 == _l else 0)
            _m = (_e0 + _e1) / 2
            _w = dict(cx=round(_a[0] + _ux * _m, 2), cz=round(_a[1] + _uz * _m, 2), len=round(_e1 - _e0, 2), wid=3.2,
                      ang=round(math.atan2(_uz, _ux), 4), kind='roadside')
            _w['posts'] = _posts(_w, 4.0)
            WALKWAYS.append(_w)
# nudge any shelter whose edge still touches the carriageway back to the kerb line
def _roadclear(w):
    c, s = math.cos(w['ang']), math.sin(w['ang']); best = 9e9
    for i in range(21):
        for v in (-w['wid'] / 2, w['wid'] / 2):
            u = -w['len'] / 2 + w['len'] * i / 20; p = (w['cx'] + c * u - s * v, w['cz'] + s * u + c * v)
            for pts, rw in ROADS:
                for a, b in zip(pts, pts[1:]):
                    dx, dz = b[0] - a[0], b[1] - a[1]; t = max(0, min(1, ((p[0] - a[0]) * dx + (p[1] - a[1]) * dz) / (dx * dx + dz * dz)))
                    best = min(best, math.hypot(p[0] - a[0] - t * dx, p[1] - a[1] - t * dz) - rw / 2)
    return best
for _w in [w for w in WALKWAYS if w.get('kind') == 'roadside']:
    for _ in range(12):
        if _roadclear(_w) >= 0.2: break
        _nx, _nz = -math.sin(_w['ang']), math.cos(_w['ang'])
        _side = 1 if _roadclear(dict(_w, cx=_w['cx'] + _nx * 0.3, cz=_w['cz'] + _nz * 0.3)) > _roadclear(dict(_w, cx=_w['cx'] - _nx * 0.3, cz=_w['cz'] - _nz * 0.3)) else -1
        _w['cx'] = round(_w['cx'] + _side * _nx * 0.15, 2); _w['cz'] = round(_w['cz'] + _side * _nz * 0.15, 2)
    _w['posts'] = _posts(_w, 4.0)
