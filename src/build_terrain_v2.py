import json, math, os, sys
import numpy as np
from PIL import Image, ImageDraw
from scipy import ndimage
from matplotlib.path import Path

sys.path.insert(0, os.path.dirname(__file__))
import layout_v2 as L

OUT = sys.argv[1] if len(sys.argv) > 1 else "out_v2"
os.makedirs(OUT, exist_ok=True)
rng = np.random.default_rng(11)

N = 1025
HALF = L.HALF
px = L.WORLD / (N - 1)
coords = np.linspace(-HALF, HALF, N)
X, Z = np.meshgrid(coords, coords)
PTS = np.stack([X.ravel(), Z.ravel()], 1)


# ------------------------------------------------------------ helpers
def seg_dist(ax, az, bx, bz):
    dx, dz = bx - ax, bz - az
    t = np.clip(((X - ax) * dx + (Z - az) * dz) / (dx * dx + dz * dz), 0, 1)
    return np.hypot(X - (ax + t * dx), Z - (az + t * dz))


def poly_dist(pts):
    d = np.full(X.shape, 1e9)
    for a, b in zip(pts[:-1], pts[1:]):
        d = np.minimum(d, seg_dist(*a, *b))
    return d


def poly_mask(poly):
    return Path(poly).contains_points(PTS).reshape(N, N)


def obox_local(c):
    ca, sa = math.cos(c["ang"]), math.sin(c["ang"])
    u = (X - c["cx"]) * ca + (Z - c["cz"]) * sa
    v = -(X - c["cx"]) * sa + (Z - c["cz"]) * ca
    return u, v


def obox_mask(c, pad=0.0):
    u, v = obox_local(c)
    return (np.abs(u) <= c["len"] / 2 + pad) & (np.abs(v) <= c["wid"] / 2 + pad)


def fbm(octaves, base_cells, seed):
    r = np.random.default_rng(seed)
    out = np.zeros((N, N)); amp = 1.0; total = 0.0; cells = base_cells
    for _ in range(octaves):
        g = r.standard_normal((cells + 1, cells + 1))
        out += amp * ndimage.zoom(g, N / (cells + 1), order=3)[:N, :N]
        total += amp; amp *= 0.5; cells *= 2
    return out / total


def rc(x, z):
    return int(round((z + HALF) / px)), int(round((x + HALF) / px))


# ------------------------------------------------------------ material map
GRASS, FOREST, TURF, SAND, TRACK, ASPHALT, CONCRETE, WATER, DIRT = range(9)
mat = np.full((N, N), GRASS, np.uint8)

inside = poly_mask(L.CAMPUS)
d_campus = ndimage.distance_transform_edt(~inside) * px          # metres outside the fence
forest_noise = fbm(4, 6, 1)
mat[(~inside) & (forest_noise > -0.1)] = FOREST
mat[inside & (fbm(4, 12, 2) > 0.6)] = DIRT

# town roads outside the campus: an outer ring + radial streets
# ---- ring road hugging the school fence (user request): 2 lanes + sidewalks + verges
RING_OFF, RING_HALF, WALK = 14.0, 5.0, 2.5          # centre offset, half carriageway, sidewalk width
RING = L._inset(L.CAMPUS, -RING_OFF)
RING_C = RING + [RING[0]]
ring_d = poly_dist(RING_C)


def on_ring_edge(i, t):
    a, b = RING[i], RING[(i + 1) % len(RING)]
    return (a[0] + (b[0] - a[0]) * t, a[1] + (b[1] - a[1]) * t)


def ring_point_at_x(i, x):           # point on ring edge i with the given x
    a, b = RING[i], RING[(i + 1) % len(RING)]
    t = (x - a[0]) / (b[0] - a[0])
    return on_ring_edge(i, t)


# the gate leads straight out to the ring road
_gs = L.CAMPUS[3], L.CAMPUS[4]
_ux, _uz = _gs[1][0] - _gs[0][0], _gs[1][1] - _gs[0][1]; _ul = math.hypot(_ux, _uz); _ux, _uz = _ux / _ul, _uz / _ul
_nx, _nz = -_uz, _ux                       # outward normal of the south edge
if _nz < 0: _nx, _nz = -_nx, -_nz
GATE_OUTS = [tuple(g["out"]) if g.get("out") else (g["x"] + _nx * RING_OFF, g["z"] + _nz * RING_OFF) for g in L.GATES]
GATE_OUT = GATE_OUTS[0]

town_roads = [([(g["x"], g["z"]), go], 7.0) for g, go in zip(L.GATES, GATE_OUTS)]
# 2026-11-19: everything outside the ring road is removed (map ends at the outer sidewalk)
BOUND = L._inset(L.CAMPUS, -(RING_OFF + RING_HALF + WALK + 0.5))
bound_mask = poly_mask(BOUND)

# sidewalks first, carriageway on top
mat[(ring_d > RING_HALF) & (ring_d <= RING_HALF + WALK)] = CONCRETE
IWALK = 1.4
main_walk = np.zeros(X.shape, bool)
for pts, w in L.MAIN_ROADS:
    d = poly_dist(pts)
    main_walk |= (d > w / 2) & (d <= w / 2 + IWALK)
main_walk &= inside
mat[main_walk] = CONCRETE
road_d = np.full(X.shape, 1e9)
for pts, w in [(RING_C, RING_HALF * 2)] + town_roads + L.ROADS:
    d = poly_dist(pts)
    mat[d <= w / 2] = ASPHALT
    road_d = np.minimum(road_d, d - w / 2)
# kerbside concrete on the campus perimeter road
perim_d = poly_dist(L.PERIM + [L.PERIM[0]])

court_mask = poly_mask(L.COURT)
for _pl in L.PLAZAS:
    mat[poly_mask(_pl['pts']) & (road_d > 0)] = ASPHALT if _pl['kind'] == 'asphalt' else CONCRETE   # never paint over a road
for poly, m in ((L.SAND, SAND), (L.COURT, CONCRETE)):
    if not poly: continue
    mat[poly_mask(poly)] = m

T = L.TRACK
dz = np.abs(Z - T["cz"]) - T["straight"] / 2
dx = X - T["cx"]
stad_r = np.where(dz > 0, np.hypot(dx, dz), np.abs(dx))
r_out = T["r_in"] + T["lanes"] * T["lane_w"]
mat[stad_r <= r_out + 3.0] = CONCRETE
mat[(stad_r <= r_out) & (stad_r >= T["r_in"])] = TRACK
mat[stad_r < T["r_in"]] = TURF
# brown dirt D-areas at both ends of the pitch (as in the drawing) + long-jump pit
dmask = (stad_r < T["r_in"] - 1) & (np.abs(Z - T["cz"]) > 53)
mat[dmask & (Z < T["cz"])] = DIRT
mat[poly_mask(L.JUMP_PIT)] = SAND

for b in L.BUILDINGS:
    mat[obox_mask(b, pad=1.5)] = CONCRETE
FP = L.FLAGPOLE
mat[np.hypot(X - FP["x"], Z - FP["z"]) < 4.0] = CONCRETE
BU = L.BUDDHA
WF = L.WATERFALL
_ca, _sa = math.cos(WF["ang"]), math.sin(WF["ang"])
_wu = (X - WF["x"]) * _ca + (Z - WF["z"]) * _sa; _wv = -(X - WF["x"]) * _sa + (Z - WF["z"]) * _ca
pond = (_wu / 6.5) ** 2 + (_wv / 2.2) ** 2 < 1
mat[pond] = WATER
HAS_POOL = getattr(L, "POOL", None) is not None
PO = L.POOL if HAS_POOL else dict(cx=-9999.0, cz=-9999.0, len=1.0, wid=1.0, ang=0.0, wlen=0.5, wwid=0.5)   # pool removed -> off-map stub
pool_deck = obox_mask(PO)
pool_water = obox_mask(dict(PO, len=PO["wlen"], wid=PO["wwid"]))
mat[pool_deck] = CONCRETE
for _sh in L.SHEDS + [L.GUARD, L.SALA]:
    mat[obox_mask(_sh, pad=0.8)] = CONCRETE
mat[pool_water] = WATER
mat[(np.abs(X - BU["x"]) < 2.6) & (np.abs(Z - BU["z"]) < 3.4)] = CONCRETE
for c in L.CANOPIES:
    mat[obox_mask(c, pad=0.5)] = CONCRETE

# ------------------------------------------------------------ heightmap (metres)
H = np.full((N, N), 1.0)
fade = np.clip((d_campus - 34) / 70.0, 0, 1); fade = fade * fade * (3 - 2 * fade)
H += fade * (2.4 * fbm(5, 4, 11) + 0.7)
H += 0.08 * fbm(5, 24, 12)
H += np.where(road_d <= 0, -0.15, 0)
# raised kerbed sidewalks along the ring road
H += np.where((ring_d > RING_HALF) & (ring_d <= RING_HALF + WALK), 0.17, 0)
H += np.where(main_walk & (road_d > 0), 0.15, 0)

H = np.where(mat == SAND, 0.95, H)
H = np.where(court_mask, 1.05, H)
H = np.where(pond, 0.55, H)
H = np.where(pool_deck, 1.1, H)
H = np.where(pool_water, -0.6, H)
in_stad = stad_r <= r_out + 3.0
crown = np.clip(1 - (stad_r / T["r_in"]) ** 2, 0, 1)
H = np.where(in_stad, 1.05 + 0.25 * crown * (stad_r < T["r_in"]), H)

G = L.GRANDSTAND
gu, gv = obox_local(G)
gmask = obox_mask(G)
gx0, gx1 = G["cx"] - G["wid"] / 2, G["cx"] + G["wid"] / 2
steps = np.floor(np.clip((gx1 - X) / (gx1 - gx0), 0, 1) * 10) / 10
H = np.where(gmask, 1.05 + 5.5 * steps, H)

for b in L.BUILDINGS:
    H = np.where(obox_mask(b, pad=1.0), np.maximum(H, 1.35), H)

H = ndimage.gaussian_filter(H, 0.9)
H = np.where(gmask, 1.05 + 5.5 * steps, H)

H = np.where(bound_mask, H, 1.0)
HMIN, HMAX = -2.0, 8.0
h16 = np.clip((H - HMIN) / (HMAX - HMIN), 0, 1)
Image.fromarray((h16 * 65535).astype(np.uint16)).save(f"{OUT}/heightmap_1025_16bit.png")
(h16 * 65535).astype("<u2").tofile(f"{OUT}/heightmap_1025_16bit.r16")
print("height range m:", H.min().round(2), H.max().round(2))

gy, gx = np.gradient(H * 6, px)
shade = np.clip(0.6 + 0.4 * (-gx * 0.6 - gy * 0.6 + 1) / np.sqrt(gx ** 2 + gy ** 2 + 1), 0, 1.15)
t = (H - H.min()) / (H.max() - H.min())
stops = np.array([[30, 60, 140], [40, 120, 90], [120, 170, 80], [220, 200, 120], [200, 120, 70], [250, 250, 250]]) / 255
pos = np.linspace(0, 1, len(stops))
rgb = np.stack([np.interp(t, pos, stops[:, i]) for i in range(3)], -1) * shade[..., None]
Image.fromarray((np.clip(rgb, 0, 1) * 255).astype(np.uint8)).save(f"{OUT}/heightmap_preview.png")

mat[~bound_mask] = GRASS
Image.fromarray((bound_mask * 255).astype(np.uint8)).save(f"{OUT}/boundary_mask_1025.png")
# ------------------------------------------------------------ splat maps
layers = [GRASS, TURF, SAND, TRACK, ASPHALT, CONCRETE, WATER, FOREST]
w = np.zeros((8, N, N), np.float32)
for i, m in enumerate(layers):
    w[i] = (mat == m)
w[0] += (mat == DIRT) * 0.35
w[2] += (mat == DIRT) * 0.65
w = ndimage.gaussian_filter(w, (0, 1.0, 1.0))
w /= np.maximum(w.sum(0, keepdims=True), 1e-6)
Image.fromarray((np.moveaxis(w[:4], 0, -1) * 255).astype(np.uint8), "RGBA").save(f"{OUT}/splatmap0_grass_turf_sand_track.png")
Image.fromarray((np.moveaxis(w[4:], 0, -1) * 255).astype(np.uint8), "RGBA").save(f"{OUT}/splatmap1_asphalt_concrete_water_forest.png")

# ------------------------------------------------------------ albedo
NA = 2048
palette = {GRASS: (108, 158, 66), FOREST: (62, 100, 46), TURF: (86, 170, 62), SAND: (218, 204, 172),
           TRACK: (196, 74, 62), ASPHALT: (74, 76, 80), CONCRETE: (180, 176, 168), WATER: (60, 92, 70), DIRT: (160, 98, 62)}
cols = np.zeros((NA, NA, 3), np.float32); wsum = np.zeros((NA, NA), np.float32)
for i in range(8):
    wi = np.clip(ndimage.zoom(w[i], NA / N, order=1)[:NA, :NA], 0, 1)
    c = palette[layers[i]]
    cols += wi[..., None] * np.array(c, np.float32); wsum += wi
# dirt red-brown tint where DIRT
dd = np.clip(ndimage.zoom(ndimage.gaussian_filter((dmask & (Z < T['cz'])).astype(np.float32), 1), NA / N, order=1)[:NA, :NA], 0, 1)
cols /= np.maximum(wsum, 1e-6)[..., None]
cols = cols * (1 - dd[..., None]) + dd[..., None] * np.array(palette[DIRT], np.float32)
nz = ndimage.gaussian_filter(np.random.default_rng(3).standard_normal((NA, NA)).astype(np.float32), 1.2) * 16
nz += ndimage.zoom(fbm(4, 16, 5), NA / N, order=1)[:NA, :NA] * 12
cols += nz[..., None]
img = Image.fromarray(np.clip(cols, 0, 255).astype(np.uint8))
dr = ImageDraw.Draw(img)
s = NA / L.WORLD
P = lambda x, z: ((x + HALF) * s, (z + HALF) * s)
for k in range(T["lanes"] + 1):
    r = T["r_in"] + k * T["lane_w"]
    a, b = T["cz"] - T["straight"] / 2, T["cz"] + T["straight"] / 2
    for xx in (T["cx"] - r, T["cx"] + r):
        dr.line([P(xx, a), P(xx, b)], fill=(240, 228, 218), width=1)
    for zc, a0 in ((a, 180), (b, 0)):
        dr.arc([P(T["cx"] - r, zc - r), P(T["cx"] + r, zc + r)], a0, a0 + 180, fill=(240, 228, 218), width=1)
fx0, fx1, fz0, fz1 = T["cx"] - 32, T["cx"] + 32, T["cz"] - 50, T["cz"] + 50
lc = (242, 246, 236)
for i in range(10):
    if i % 2 == 0:
        ov = Image.new("RGBA", img.size, (0, 0, 0, 0))
        ImageDraw.Draw(ov).rectangle([P(fx0 + 1, fz0 + i * 10), P(fx1 - 1, fz0 + i * 10 + 10)], fill=(255, 255, 255, 16))
        img.paste(ov, (0, 0), ov)
dr.rectangle([P(fx0, fz0), P(fx1, fz1)], outline=lc, width=2)
dr.line([P(fx0, T["cz"]), P(fx1, T["cz"])], fill=lc, width=2)
dr.ellipse([P(T["cx"] - 9.15, T["cz"] - 9.15), P(T["cx"] + 9.15, T["cz"] + 9.15)], outline=lc, width=2)
for zz, sg in ((fz0, 1), (fz1, -1)):
    dr.rectangle([P(T["cx"] - 20, min(zz, zz + sg * 16.5)), P(T["cx"] + 20, max(zz, zz + sg * 16.5))], outline=lc, width=2)
    dr.rectangle([P(T["cx"] - 9, min(zz, zz + sg * 5.5)), P(T["cx"] + 9, max(zz, zz + sg * 5.5))], outline=lc, width=2)
# ---- multi-sport concrete court: coloured playing areas + line markings for each sport
HOOPS, FGOALS, NETS = [], [], []
dr.polygon([P(*c) for c in L.COURT], fill=(196, 194, 188))
WL = (248, 248, 244)


def L2W(c, ang, lx, lz):
    ca, sa = math.cos(ang), math.sin(ang)
    return (c[0] + ca * lx - sa * lz, c[1] + sa * lx + ca * lz)


def rect(c, ang, x0, z0, x1, z1, fill=None, outline=WL):
    pts = [P(*L2W(c, ang, x, z)) for x, z in ((x0, z0), (x1, z0), (x1, z1), (x0, z1))]
    dr.polygon(pts, fill=fill, outline=outline)


def arc(c, ang, cx, cz, r, a0, a1, n=24):
    pts = [P(*L2W(c, ang, cx + r * math.cos(a0 + (a1 - a0) * i / n), cz + r * math.sin(a0 + (a1 - a0) * i / n))) for i in range(n + 1)]
    dr.line(pts, fill=WL, width=1)


SKATES = []
for kind, c, ln, wd, rot in L.SPORT:
    A = L.COURT_ANG + rot
    hl, hw = ln / 2, wd / 2
    fill = {"basketball": (178, 98, 64), "futsal": (52, 112, 170), "takraw": (60, 142, 98), "skate": (150, 148, 146)}[kind]
    if kind == "skate":
        rect(c, A, -hl - 1.0, -hw - 1.0, hl + 1.0, hw + 1.0, fill=(120, 118, 116), outline=None)
        rect(c, A, -hl, -hw, hl, hw, fill=fill, outline=(235, 200, 60))
        for k in range(-3, 4):          # smooth-concrete pour joints
            dr.line([P(*L2W(c, A, k * hl / 4, -hw)), P(*L2W(c, A, k * hl / 4, hw))], fill=(132, 130, 128), width=1)
        SKATES.append((round(c[0], 2), round(c[1], 2), round(A, 4), ln, wd))
        continue
    rect(c, A, -hl - 1.5, -hw - 1.5, hl + 1.5, hw + 1.5, fill=tuple(int(v * 0.82) for v in fill), outline=None)   # run-off
    rect(c, A, -hl, -hw, hl, hw, fill=fill)
    dr.line([P(*L2W(c, A, 0, -hw)), P(*L2W(c, A, 0, hw))], fill=WL, width=1)
    if kind == "basketball":
        arc(c, A, 0, 0, 1.8, 0, 2 * math.pi, 32)
        for sg in (-1, 1):
            bx = sg * (hl - 1.575)
            rect(c, A, sg * hl, -2.45, sg * (hl - 5.8), 2.45, fill=tuple(int(v * 0.88) for v in fill))
            arc(c, A, sg * (hl - 5.8), 0, 1.8, 0, 2 * math.pi, 28)
            a0, a1 = (math.pi / 2 + 0.21, 3 * math.pi / 2 - 0.21) if sg > 0 else (-math.pi / 2 + 0.21, math.pi / 2 - 0.21)
            arc(c, A, bx, 0, 6.75, a0, a1, 40)
            for zz in (-6.6, 6.6):     # straight parts of the 3-point line
                dr.line([P(*L2W(c, A, sg * hl, zz)), P(*L2W(c, A, sg * (hl - 2.99), zz))], fill=WL, width=1)
            HOOPS.append((*[round(v, 2) for v in L2W(c, A, sg * (hl - 1.2), 0)], sg, round(A, 4)))
    elif kind == "futsal":
        arc(c, A, 0, 0, 3.0, 0, 2 * math.pi, 36)
        for sg in (-1, 1):
            a0, a1 = (math.pi / 2, 3 * math.pi / 2) if sg > 0 else (-math.pi / 2, math.pi / 2)
            # penalty area: two quarter arcs joined by a short line (FIFA futsal)
            arc(c, A, sg * hl, -1.58, 6.0, (math.pi if sg > 0 else -math.pi / 2), (3 * math.pi / 2 if sg > 0 else 0), 16)
            arc(c, A, sg * hl, 1.58, 6.0, (math.pi / 2 if sg > 0 else 0), (math.pi if sg > 0 else math.pi / 2), 16)
            dr.line([P(*L2W(c, A, sg * (hl - 6), -1.58)), P(*L2W(c, A, sg * (hl - 6), 1.58))], fill=WL, width=1)
            pm = L2W(c, A, sg * (hl - 6), 0); dr.ellipse([P(pm[0] - .2, pm[1] - .2), P(pm[0] + .2, pm[1] + .2)], fill=WL)
            FGOALS.append((*[round(v, 2) for v in L2W(c, A, sg * hl, 0)], sg, round(A, 4)))
    else:   # sepak takraw
        for sg in (-1, 1):
            arc(c, A, 0, sg * hw, 0.9, (math.pi if sg > 0 else 0), (2 * math.pi if sg > 0 else math.pi), 12)
            arc(c, A, sg * (hl - 2.45), 0, 0.3, 0, 2 * math.pi, 12)
        NETS.append((*[round(v, 2) for v in c], round(A, 4), wd + 0.6))
# ---- swimming pool: tiled deck, blue water, dark lane lines with T-ends
rect((PO["cx"], PO["cz"]), PO["ang"], -PO["len"] / 2, -PO["wid"] / 2, PO["len"] / 2, PO["wid"] / 2, fill=(214, 208, 196), outline=(170, 166, 158))
rect((PO["cx"], PO["cz"]), PO["ang"], -PO["wlen"] / 2, -PO["wwid"] / 2, PO["wlen"] / 2, PO["wwid"] / 2, fill=(70, 160, 214), outline=(240, 240, 236))
for k in range(1, 5):
    zz = -PO["wwid"] / 2 + k * PO["wwid"] / 5 - PO["wwid"] / 10
    dr.line([P(*L2W((PO["cx"], PO["cz"]), PO["ang"], -PO["wlen"] / 2 + 2, zz)), P(*L2W((PO["cx"], PO["cz"]), PO["ang"], PO["wlen"] / 2 - 2, zz))], fill=(30, 70, 140), width=2)
# ---- ring road markings: dashed centre line, solid edge lines, red/white kerbs, zebra at the gate
def offset_ring(d):
    r = L._inset(L.CAMPUS, -(RING_OFF + d))
    return r + [r[0]]


def dashed(poly, on, off, col, width=1, alt=None):
    for a, b in zip(poly[:-1], poly[1:]):
        Lg = math.hypot(b[0] - a[0], b[1] - a[1]); ux, uz = (b[0] - a[0]) / Lg, (b[1] - a[1]) / Lg
        t, k = 0.0, 0
        while t < Lg:
            t1 = min(Lg, t + on)
            c = col if (alt is None or k % 2 == 0) else alt
            dr.line([P(a[0] + ux * t, a[1] + uz * t), P(a[0] + ux * t1, a[1] + uz * t1)], fill=c, width=width)
            t = t1 + (off if alt is None else 0); k += 1


dashed(RING_C, 3.0, 4.5, (238, 238, 232))                         # centre line
for d in (-RING_HALF + 0.35, RING_HALF - 0.35):
    dr.line([P(*q) for q in offset_ring(d)], fill=(232, 232, 226), width=1)    # edge lines
for d in (-RING_HALF - 0.1, RING_HALF + 0.1):
    dashed(offset_ring(d), 1.5, 0, (200, 40, 44), width=2, alt=(245, 245, 245))   # red/white kerbs
# sidewalk paving joints
for d in (-RING_HALF - WALK / 2, RING_HALF + WALK / 2):
    dashed(offset_ring(d), 0.3, 2.2, (150, 146, 140))
# ---- main internal roads: centre dashes, edge lines, red/white kerbs, paving joints
def off_line(pts, d):
    out = []
    for a, b in zip(pts[:-1], pts[1:]):
        Lg = math.hypot(b[0] - a[0], b[1] - a[1]); nx_, nz_ = -(b[1] - a[1]) / Lg, (b[0] - a[0]) / Lg
        out.append([(a[0] + nx_ * d, a[1] + nz_ * d), (b[0] + nx_ * d, b[1] + nz_ * d)])
    return out


for pts, rw in L.MAIN_ROADS:
    dashed(pts, 2.5, 3.5, (238, 238, 232))
    for d in (-rw / 2 + 0.3, rw / 2 - 0.3):
        for seg in off_line(pts, d):
            dr.line([P(*seg[0]), P(*seg[1])], fill=(228, 228, 222), width=1)
    for d in (-rw / 2 - 0.1, rw / 2 + 0.1):
        for seg in off_line(pts, d):
            dashed(seg, 1.2, 0, (200, 40, 44), width=2, alt=(245, 245, 245))
    for d in (-rw / 2 - IWALK / 2, rw / 2 + IWALK / 2):
        for seg in off_line(pts, d):
            dashed(seg, 0.25, 1.8, (150, 146, 140))
# zebra crossings on the ring road in front of every gate: stripes run with the traffic,
# 0.5 m wide every 1.0 m across the carriageway, 4 m long, with stop lines 3 m before the crossing
CROSSINGS = []
for g_, (gx, gz) in zip(L.GATES, GATE_OUTS):
    best = None
    for i in range(len(RING)):
        a_, b_ = RING[i], RING[(i + 1) % len(RING)]
        d_ = seg_dist_pt = None
        ex, ez = b_[0] - a_[0], b_[1] - a_[1]; el = math.hypot(ex, ez)
        t_ = max(0, min(1, ((gx - a_[0]) * ex + (gz - a_[1]) * ez) / (el * el)))
        dd_ = math.hypot(gx - (a_[0] + ex * t_), gz - (a_[1] + ez * t_))
        if best is None or dd_ < best[0]: best = (dd_, ex / el, ez / el)
    _, ux_, uz_ = best
    nx_, nz_ = -uz_, ux_
    CROSSINGS.append(dict(x=round(gx, 2), z=round(gz, 2), ang=round(math.atan2(uz_, ux_), 4), half=RING_HALF, width=4.0))
    for k in range(-4, 5):                       # albedo copy of the stripes (for the engine pack)
        cxk, czk = gx + nx_ * k * 1.0, gz + nz_ * k * 1.0
        pts = [(cxk + ux_ * su * 2.0 + nx_ * sn * 0.25, czk + uz_ * su * 2.0 + nz_ * sn * 0.25) for su, sn in ((-1, -1), (1, -1), (1, 1), (-1, 1))]
        dr.polygon([P(*q) for q in pts], fill=(246, 246, 242))
img.convert("RGB").save(f"{OUT}/albedo_2048.jpg", quality=86)

sp = np.zeros((N, N, 3), np.float32)
pcol = [(120, 190, 80), (40, 200, 90), (230, 210, 150), (210, 70, 60), (60, 60, 70), (190, 190, 190), (60, 120, 220), (30, 90, 40)]
for i in range(8):
    sp += w[i][..., None] * np.array(pcol[i], np.float32)
Image.fromarray(np.clip(sp, 0, 255).astype(np.uint8)).save(f"{OUT}/splatmap_preview.png")

# ------------------------------------------------------------ vegetation, town, cars
occupied = (mat == ASPHALT) | (mat == CONCRETE) | (mat == TURF) | (mat == TRACK) | (mat == SAND) | (mat == WATER) | (mat == DIRT) & inside
occupied = ndimage.binary_dilation(occupied, iterations=3)


def free(x, z):
    r, c = rc(x, z)
    return 0 <= r < N and 0 <= c < N and not occupied[r, c]


def h_at(x, z):
    r, c = rc(x, z)
    return float(H[min(max(r, 0), N - 1), min(max(c, 0), N - 1)])


def hit_building(x, z, pad=3.0):
    for c in L.BUILDINGS + L.CANOPIES + L.SHEDS + L.WALKWAYS + [L.GUARD, L.SALA, L.DROPOFF, L.LED]:
        ca, sa = math.cos(c["ang"]), math.sin(c["ang"])
        u = (x - c["cx"]) * ca + (z - c["cz"]) * sa
        v = -(x - c["cx"]) * sa + (z - c["cz"]) * ca
        if abs(u) < c["len"] / 2 + pad and abs(v) < c["wid"] / 2 + pad:
            return True
    return (math.hypot(x - FP["x"], z - FP["z"]) < 7.0 or math.hypot(x - BU["x"], z - BU["z"]) < 6.0
            or math.hypot(x - WF["x"], z - WF["z"]) < 9.0 or math.hypot(x - L.SIGN["x"], z - L.SIGN["z"]) < 10.5
            or (abs((x - PO["cx"]) * math.cos(PO["ang"]) + (z - PO["cz"]) * math.sin(PO["ang"])) < PO["len"] / 2 + 3
                and abs(-(x - PO["cx"]) * math.sin(PO["ang"]) + (z - PO["cz"]) * math.cos(PO["ang"])) < PO["wid"] / 2 + 3))


houses = []
for _ in range(0):      # no town outside the school any more
    x, z = rng.uniform(-HALF + 8, HALF - 8, 2)
    r, c = rc(x, z)
    if inside[r, c] or d_campus[r, c] < 34 or not free(x, z) or forest_noise[r, c] > 0.45:
        continue
    ww, dd2 = rng.uniform(7, 16), rng.uniform(7, 14)
    if any(abs(x - hx) < (ww + hw) / 2 + 3 and abs(z - hz) < (dd2 + hd) / 2 + 3 for hx, hz, hw, hd, *_ in houses):
        continue
    corners_ok = all(free(x + sx_ * ww / 2, z + sz_ * dd2 / 2) for sx_ in (-1, 1) for sz_ in (-1, 1))
    if not corners_ok:
        continue
    fl = int(rng.choice([1, 2, 3, 4], p=[.55, .3, .1, .05]))
    houses.append((round(x, 1), round(z, 1), round(ww, 1), round(dd2, 1), fl, int(rng.integers(0, 6)), round(h_at(x, z), 2)))


def near_house(x, z):
    return any(abs(x - hx) < hw / 2 + 2 and abs(z - hz) < hd / 2 + 2 for hx, hz, hw, hd, *_ in houses)


trees = []


def _in_poly(x, z, P_):
    r = False
    for i in range(len(P_)):
        a, b = P_[i], P_[i - 1]
        if (a[1] > z) != (b[1] > z) and x < (b[0] - a[0]) * (z - a[1]) / (b[1] - a[1]) + a[0]: r = not r
    return r


def put(x, z, s, kind):
    r_, c_ = rc(x, z)
    if not (0 <= r_ < N and 0 <= c_ < N and bound_mask[r_, c_]): return
    if any(_in_poly(x, z, P_) for P_ in getattr(L, "NO_TREES", [])): return
    if free(x, z) and not hit_building(x, z) and not near_house(x, z):
        trees.append((round(x, 1), round(z, 1), round(s, 2), kind, round(h_at(x, z), 2)))


# dense rows hugging the fence and the perimeter road (signature look of the drawing)
def neat_row(ring, spacing, size, kind, jitter=0.0, skip_gate=True):
    for a, b in zip(ring, ring[1:] + ring[:1]):
        Lg = math.hypot(b[0] - a[0], b[1] - a[1]); n = max(1, int(Lg / spacing))
        for i in range(1, n):
            x = a[0] + (b[0] - a[0]) * i / n; z = a[1] + (b[1] - a[1]) * i / n
            if skip_gate and min(math.hypot(x - g[0], z - g[1]) for g in GATE_OUTS) < 14: continue
            put(x + rng.normal(0, jitter), z + rng.normal(0, jitter), size, kind)


# avenue trees: evenly spaced, same size, on both verges of the ring road
neat_row(L._inset(L.CAMPUS, -3.0), 10.0, 1.0, 0)
neat_row(L._inset(L.PERIM, 6.5), 7.5, 1.0, 0, jitter=0.4, skip_gate=False)

# street lights on the campus-side sidewalk, arm reaching over the road
LIGHTS = []
lring = L._inset(L.CAMPUS, -(RING_OFF - RING_HALF - 0.6))
for i, (a, b) in enumerate(zip(lring, lring[1:] + lring[:1])):
    Lg = math.hypot(b[0] - a[0], b[1] - a[1]); n = max(1, int(Lg / 30))
    ux, uz = (b[0] - a[0]) / Lg, (b[1] - a[1]) / Lg
    cxp = sum(p[0] for p in L.CAMPUS) / 5; czp = sum(p[1] for p in L.CAMPUS) / 5
    nx, nz = -uz, ux
    mx, mz = (a[0] + b[0]) / 2, (a[1] + b[1]) / 2
    if (mx - cxp) * nx + (mz - czp) * nz < 0: nx, nz = -nx, -nz          # outward (towards the road)
    for k in range(n):
        x = a[0] + ux * (k + 0.5) * Lg / n; z = a[1] + uz * (k + 0.5) * Lg / n
        LIGHTS.append((round(x, 1), round(z, 1), round(math.atan2(nz, nx), 3), round(h_at(x, z), 2)))
k_side = 1
for pts, rw in L.MAIN_ROADS:
    for a, b in zip(pts[:-1], pts[1:]):
        Lg = math.hypot(b[0] - a[0], b[1] - a[1]); ux, uz = (b[0] - a[0]) / Lg, (b[1] - a[1]) / Lg
        nx, nz = -uz, ux
        n = max(1, int(Lg / 25))
        for k in range(n):
            t_ = (k + 0.5) * Lg / n
            k_side = -k_side
            x = a[0] + ux * t_ + nx * k_side * (rw / 2 + 0.5); z = a[1] + uz * t_ + nz * k_side * (rw / 2 + 0.5)
            if hit_building(x, z, pad=0.5): continue
            LIGHTS.append((round(x, 1), round(z, 1), round(math.atan2(-nz * k_side, -nx * k_side), 3), round(h_at(x, z), 2)))
# road-side rows inside campus
for pts, wdt in L.ROADS:
    for a, b in zip(pts[:-1], pts[1:]):
        L_ = math.hypot(b[0] - a[0], b[1] - a[1]); n = int(L_ / 9)
        nx, nz = -(b[1] - a[1]) / L_, (b[0] - a[0]) / L_
        for i in range(n + 1):
            t_ = i / max(n, 1)
            for sg in (-1, 1):
                if rng.random() < 0.85:
                    put(a[0] + (b[0] - a[0]) * t_ + sg * nx * (wdt / 2 + 4.4), a[1] + (b[1] - a[1]) * t_ + sg * nz * (wdt / 2 + 4.4), rng.uniform(.8, 1.1), 0 if rng.random() > .2 else 2)
# scattered inside & forest outside
tries = 0
while len(trees) < 5200 and tries < 150000:
    tries += 1
    x, z = rng.uniform(-HALF + 2, HALF - 2, 2)
    r, c = rc(x, z)
    p = 0.9 if mat[r, c] == FOREST else (0.22 if inside[r, c] else 0.18)
    if 0 < d_campus[r, c] < RING_OFF + RING_HALF + WALK + 9: continue
    if rng.random() < p:
        kind = 2 if (inside[r, c] and rng.random() < 0.18) else int(rng.random() < 0.12)
        put(x, z, rng.uniform(0.75, 1.3) * (1.2 if mat[r, c] == FOREST else 1.0), kind)

cars = []
for (px, pz) in getattr(L, 'PARKING', [(-32 + i * 5.5, -10.6) for i in range(6)]):    # car park
    cars.append((round(px, 1), round(pz, 1), round(math.pi / 2, 3), int(rng.integers(0, 6))))

for i in range(len(RING)):          # a few cars driving on the ring road (left-hand traffic)
    a, b = RING[i], RING[(i + 1) % len(RING)]
    ang = math.atan2(b[1] - a[1], b[0] - a[0]); nx_, nz_ = -math.sin(ang), math.cos(ang)
    for _ in range(3):
        t_ = rng.uniform(0.15, 0.85); side = rng.choice([-1, 1])
        x = a[0] + (b[0] - a[0]) * t_ + nx_ * side * 2.4; z = a[1] + (b[1] - a[1]) * t_ + nz_ * side * 2.4
        cars.append((round(x, 1), round(z, 1), round(ang + (math.pi if side > 0 else 0), 3), int(rng.integers(0, 6))))

NW = 257
Hs = ndimage.zoom(H, NW / N, order=1)[:NW, :NW]
(np.clip((Hs - HMIN) / (HMAX - HMIN), 0, 1) * 65535).astype("<u2").tofile(f"{OUT}/height_257.u16")


def hb(b):
    return round(h_at(b["cx"], b["cz"]), 2)


# ---- road network for crisp 3D road meshes in the viewer
ROADS3D = [dict(pts=[list(p) for p in RING], half=RING_HALF, walk=WALK, closed=True, marks="ring")]
for pts, w in L.MAIN_ROADS:
    ROADS3D.append(dict(pts=[list(p) for p in pts], half=w / 2, walk=IWALK, closed=False, marks="main"))
for pts, w in L.SECONDARY_ROADS:
    ROADS3D.append(dict(pts=[list(p) for p in pts], half=w / 2, walk=0.0, closed=False, marks="edge"))
for (pts, w) in town_roads:
    ROADS3D.append(dict(pts=[list(p) for p in pts], half=w / 2, walk=0.0, closed=False, marks="none"))


def _segs(r):
    P_ = r["pts"] + ([r["pts"][0]] if r["closed"] else [])
    return list(zip(P_[:-1], P_[1:]))


def _pdist(p, a, b):
    ex, ez = b[0] - a[0], b[1] - a[1]; l2 = ex * ex + ez * ez
    t = max(0, min(1, ((p[0] - a[0]) * ex + (p[1] - a[1]) * ez) / l2))
    return math.hypot(p[0] - a[0] - ex * t, p[1] - a[1] - ez * t)


JUNCTIONS = []
for i, ra in enumerate(ROADS3D):
    for j, rb in enumerate(ROADS3D):
        if i >= j: continue
        rad = max(ra["half"] + ra["walk"], rb["half"] + rb["walk"]) + 1.0
        for a, b in _segs(ra):
            for c, d in _segs(rb):
                den = (b[0] - a[0]) * (d[1] - c[1]) - (b[1] - a[1]) * (d[0] - c[0])
                if abs(den) < 1e-9: continue
                t = ((c[0] - a[0]) * (d[1] - c[1]) - (c[1] - a[1]) * (d[0] - c[0])) / den
                u = ((c[0] - a[0]) * (b[1] - a[1]) - (c[1] - a[1]) * (b[0] - a[0])) / den
                if -0.02 <= t <= 1.02 and -0.02 <= u <= 1.02:
                    JUNCTIONS.append([round(a[0] + (b[0] - a[0]) * t, 2), round(a[1] + (b[1] - a[1]) * t, 2), round(rad, 2)])
    if not ra["closed"]:
        for e in (ra["pts"][0], ra["pts"][-1]):
            for j, rb in enumerate(ROADS3D):
                if j == i: continue
                if min(_pdist(e, a, b) for a, b in _segs(rb)) <= rb["half"] + 1.0:
                    JUNCTIONS.append([round(e[0], 2), round(e[1], 2), round(max(ra["half"] + ra["walk"], rb["half"] + rb["walk"]) + 1.0, 2)])
print("junctions", len(JUNCTIONS))

layout_out = dict(
    version=2, world=L.WORLD, hmin=HMIN, hmax=HMAX, grid=NW,
    campus=L.CAMPUS, bound=BOUND,
    buildings=[dict(b, y=hb(b)) for b in L.BUILDINGS],
    canopies=[dict(c, y=hb(c)) for c in L.CANOPIES],
    grandstand=dict(G, y=hb(G)),
    track=T, walkways=L.WALKWAYS, gate=L.GATE, gates=L.GATES, buddha=dict(BU, y=round(h_at(BU['x'], BU['z']), 2)), flagpole=dict(FP, y=round(h_at(FP['x'], FP['z']), 2)), sign=L.SIGN, waterfall=dict(WF, y=round(h_at(L.SIGN['x'], L.SIGN['z']), 2)),
    houses=houses, trees=trees, cars=cars,
    goals=[(T["cx"], T["cz"] - 50, 0), (T["cx"], T["cz"] + 50, 1)],
    crossings=CROSSINGS, plazas=L.PLAZAS, roads=ROADS3D, junctions=JUNCTIONS, hoops=HOOPS, futsal_goals=FGOALS, nets=NETS, skate=SKATES, pool=(PO if HAS_POOL else None), sheds=L.SHEDS, guard=L.GUARD, dropoff=L.DROPOFF, sala=L.SALA, led=L.LED, lights=LIGHTS,
    labels=[("สนามฟุตบอล + ลู่วิ่ง", T["cx"], T["cz"]), ("สนามฟุตซอล", *[round(v, 1) for v in L.SPORT[0][1]]), ("สนามบาสเกตบอล", *[round(v, 1) for v in L.SPORT[1][1]]), ("สนามเซปักตะกร้อ", *[round(v, 1) for v in L.SPORT[2][1]]), ("ลานสเก็ตบอร์ด", *[round(v, 1) for v in L.SPORT[3][1]]), ("ประตูโรงเรียน", L.GATE["x"], L.GATE["z"])] + ([("สระว่ายน้ำ", PO["cx"], PO["cz"])] if HAS_POOL else []),
)
with open(f"{OUT}/layout.json", "w") as f:
    json.dump(layout_out, f, ensure_ascii=False)
print("trees", len(trees), "houses", len(houses), "cars", len(cars))
