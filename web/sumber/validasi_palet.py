import math
import sys

BAND = {"light": (0.43, 0.77), "dark": (0.48, 0.67)}
CHROMA_FLOOR = 0.10
CVD_TARGET, CVD_FLOOR = 8.0, 6.0
NORMAL_FLOOR = 15.0
CONTRAST_MIN = 3.0

MACHADO = {
    "protan": ((0.152286, 1.052583, -0.204868),
               (0.114503, 0.786281, 0.099216),
               (-0.003882, -0.048116, 1.051998)),
    "deutan": ((0.367322, 0.860646, -0.227968),
               (0.280085, 0.672501, 0.047413),
               (-0.011820, 0.042940, 0.968881)),
    "tritan": ((1.255528, -0.076749, -0.178779),
               (-0.078411, 0.930809, 0.147602),
               (0.004733, 0.691367, 0.303900)),
}

def _srgb(h):
    h = h.strip().lstrip("#")
    return [int(h[i:i + 2], 16) / 255 for i in (0, 2, 4)]

def _s2lin(c):
    return c / 12.92 if c <= 0.04045 else ((c + 0.055) / 1.055) ** 2.4

def lin(h):
    return [_s2lin(c) for c in _srgb(h)]

def rel_lum(h):
    r, g, b = lin(h)
    return 0.2126 * r + 0.7152 * g + 0.0722 * b

def contrast(a, b):
    hi, lo = sorted((rel_lum(a), rel_lum(b)), reverse=True)
    return (hi + 0.05) / (lo + 0.05)

def oklab_from_lin(rgb):
    r, g, b = rgb
    l = (0.4122214708 * r + 0.5363325363 * g + 0.0514459929 * b) ** (1 / 3)
    m = (0.2119034982 * r + 0.6806995451 * g + 0.1073969566 * b) ** (1 / 3)
    s = (0.0883024619 * r + 0.2817188376 * g + 0.6299787005 * b) ** (1 / 3)
    return (0.2104542553 * l + 0.7936177850 * m - 0.0040720468 * s,
            1.9779984951 * l - 2.4285922050 * m + 0.4505937099 * s,
            0.0259040371 * l + 0.7827717662 * m - 0.8086757660 * s)

def oklch(h):
    L, a, b = oklab_from_lin(lin(h))
    return L, math.hypot(a, b)

def simulate(h, kind):
    r, g, b = lin(h)
    M = MACHADO[kind]
    return [min(1.0, max(0.0, M[i][0] * r + M[i][1] * g + M[i][2] * b))
            for i in range(3)]

def delta_e(h1, h2, kind=None):
    a = oklab_from_lin(simulate(h1, kind) if kind else lin(h1))
    b = oklab_from_lin(simulate(h2, kind) if kind else lin(h2))
    return 100 * math.dist(a, b)

def validate(palette, mode="light", surface=None, pairs="adjacent"):
    surface = surface or ("#fcfcfb" if mode == "light" else "#1a1a19")
    lo, hi = BAND[mode]
    rep, ok = [], True

    off = [(c, round(oklch(c)[0], 3)) for c in palette
           if not (lo <= oklch(c)[0] <= hi)]
    ok &= not off
    rep.append(("Lightness band", "pass" if not off else "FAIL",
                ("di luar band: %s" % off) if off
                else "semua %d dalam L %s-%s" % (len(palette), lo, hi)))

    lowc = [(c, round(oklch(c)[1], 3)) for c in palette
            if oklch(c)[1] < CHROMA_FLOOR]
    ok &= not lowc
    rep.append(("Chroma floor", "pass" if not lowc else "FAIL",
                ("di bawah floor (terbaca abu): %s" % lowc) if lowc
                else "semua %d >= %s" % (len(palette), CHROMA_FLOOR)))

    n = len(palette)
    if pairs == "all":
        pl = [(i, j) for i in range(n) for j in range(i + 1, n)]
    else:
        pl = [(i, i + 1) for i in range(n - 1)]

    worst = None
    for kind in ("protan", "deutan"):
        for i, j in pl:
            d = delta_e(palette[i], palette[j], kind)
            if worst is None or d < worst[0]:
                worst = (d, kind, palette[i], palette[j])
    tri = min((delta_e(palette[i], palette[j], "tritan") for i, j in pl),
              default=99)
    wd = worst[0] if worst else 99
    st = "pass" if wd >= CVD_TARGET else ("floor" if wd >= CVD_FLOOR else "FAIL")
    ok &= st != "FAIL"
    rep.append(("CVD separation", st,
                "terburuk %s<->%s dE %.1f (%s) - tritan %.1f"
                % (worst[3], worst[2], wd, worst[1], tri)))

    nw = None
    for i, j in pl:
        d = delta_e(palette[i], palette[j])
        if nw is None or d < nw[0]:
            nw = (d, palette[i], palette[j])
    nd = nw[0] if nw else 99
    nst = "pass" if nd >= NORMAL_FLOOR else "FAIL"
    ok &= nst != "FAIL"
    rep.append(("Normal-vision floor", nst,
                "terburuk %s<->%s dE %.1f%s"
                % (nw[2], nw[1], nd,
                   "" if nd >= NORMAL_FLOOR else "  << di bawah %d" % NORMAL_FLOOR)))

    low = [(c, round(contrast(c, surface), 2)) for c in palette
           if contrast(c, surface) < CONTRAST_MIN]
    rep.append(("Contrast vs surface", "relief" if low else "pass",
                ("di bawah %s:1 -> wajib label/tabel: %s" % (CONTRAST_MIN, low))
                if low else "semua %d >= %s:1" % (len(palette), CONTRAST_MIN)))
    return rep, ok

def laporan(nama, palette, mode, surface, pairs="adjacent"):
    rep, ok = validate(palette, mode, surface, pairs)
    print("\n== %s (%s, surface %s, %s) ==" % (nama, mode, surface, pairs))
    for k, s, d in rep:
        print("  %-21s %-6s %s" % (k, s, d))
    print("  HASIL: %s" % ("LOLOS" if ok else "GAGAL"))
    return ok

if __name__ == "__main__":
    TERANG = ["#0b7f8c", "#4a7fa5", "#7a6bab", "#a85f8e",
              "#b2683f", "#7d8f3a", "#3f8f72", "#8a7a5c"]
    GELAP = ["#3fb8c4", "#6fa6cc", "#9f8fd4", "#cf85b4",
             "#d98a5f", "#a8bc5a", "#5fba97", "#b3a07c"]
    a = laporan("palet saat ini", TERANG, "light", "#ffffff")
    b = laporan("palet saat ini", GELAP, "dark", "#141c1f")
    sys.exit(0 if (a and b) else 1)
