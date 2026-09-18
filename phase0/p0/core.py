"""Core utilities: linear algebra, sRGB linearisation, image buffer, PNG IO, hashing.

Pure standard library on purpose: this sandbox has no network access, so numpy /
OpenCV cannot be installed.  Every numerical routine used by the measurement
pipeline is therefore implemented explicitly and is unit tested.  See
docs/P0_ASSUMPTIONS.md item A-01 for the consequences of this decision.
"""
from __future__ import annotations

import hashlib
import json
import math
import struct
import zlib
from array import array

# --------------------------------------------------------------------------
# hashing / canonical json
# --------------------------------------------------------------------------


def canonical_json(obj) -> str:
    return json.dumps(obj, sort_keys=True, separators=(",", ":"), ensure_ascii=False)


def sha256_hex(data) -> str:
    if isinstance(data, str):
        data = data.encode("utf-8")
    return hashlib.sha256(data).hexdigest()


def obj_hash(obj) -> str:
    return sha256_hex(canonical_json(obj))


def seed_from(*parts) -> int:
    """Deterministic 64-bit seed from arbitrary strings."""
    h = sha256_hex("|".join(str(p) for p in parts))
    return int(h[:16], 16)


class Rng:
    """Deterministic PRNG (SplitMix64) -- independent of Python version."""

    __slots__ = ("s",)

    def __init__(self, seed: int):
        self.s = seed & 0xFFFFFFFFFFFFFFFF

    def next_u64(self) -> int:
        self.s = (self.s + 0x9E3779B97F4A7C15) & 0xFFFFFFFFFFFFFFFF
        z = self.s
        z = ((z ^ (z >> 30)) * 0xBF58476D1CE4E5B9) & 0xFFFFFFFFFFFFFFFF
        z = ((z ^ (z >> 27)) * 0x94D049BB133111EB) & 0xFFFFFFFFFFFFFFFF
        return z ^ (z >> 31)

    def uniform(self) -> float:
        return (self.next_u64() >> 11) * (1.0 / 9007199254740992.0)

    def between(self, a: float, b: float) -> float:
        return a + (b - a) * self.uniform()

    def normal(self, mu: float = 0.0, sigma: float = 1.0) -> float:
        u1 = max(self.uniform(), 1e-12)
        u2 = self.uniform()
        return mu + sigma * math.sqrt(-2.0 * math.log(u1)) * math.cos(2.0 * math.pi * u2)

    def randint(self, n: int) -> int:
        return self.next_u64() % n


# --------------------------------------------------------------------------
# small dense linear algebra
# --------------------------------------------------------------------------


def solve(A, b):
    """Gauss-Jordan with partial pivoting.  A: list of rows, b: list."""
    n = len(A)
    M = [list(A[i]) + [b[i]] for i in range(n)]
    for c in range(n):
        piv = max(range(c, n), key=lambda r: abs(M[r][c]))
        if abs(M[piv][c]) < 1e-14:
            raise ZeroDivisionError("singular system")
        M[c], M[piv] = M[piv], M[c]
        d = M[c][c]
        for j in range(c, n + 1):
            M[c][j] /= d
        for r in range(n):
            if r == c:
                continue
            f = M[r][c]
            if f == 0.0:
                continue
            for j in range(c, n + 1):
                M[r][j] -= f * M[c][j]
    return [M[i][n] for i in range(n)]


def lstsq(rows, rhs):
    """Least squares via normal equations (rows: m x n, rhs: m)."""
    m = len(rows)
    n = len(rows[0])
    ATA = [[0.0] * n for _ in range(n)]
    ATb = [0.0] * n
    for i in range(m):
        ri = rows[i]
        yi = rhs[i]
        for a in range(n):
            ra = ri[a]
            if ra == 0.0:
                continue
            ATb[a] += ra * yi
            Aa = ATA[a]
            for bb in range(a, n):
                Aa[bb] += ra * ri[bb]
    for a in range(n):
        for bb in range(a):
            ATA[a][bb] = ATA[bb][a]
    return solve(ATA, ATb)


def mat3_mul(A, B):
    return [[sum(A[i][k] * B[k][j] for k in range(3)) for j in range(3)] for i in range(3)]


def mat3_inv(M):
    a, b, c = M[0]
    d, e, f = M[1]
    g, h, i = M[2]
    det = a * (e * i - f * h) - b * (d * i - f * g) + c * (d * h - e * g)
    if abs(det) < 1e-18:
        raise ZeroDivisionError("singular 3x3")
    return [
        [(e * i - f * h) / det, (c * h - b * i) / det, (b * f - c * e) / det],
        [(f * g - d * i) / det, (a * i - c * g) / det, (c * d - a * f) / det],
        [(d * h - e * g) / det, (b * g - a * h) / det, (a * e - b * d) / det],
    ]


def apply_h(H, x, y):
    w = H[2][0] * x + H[2][1] * y + H[2][2]
    if abs(w) < 1e-18:
        raise ZeroDivisionError("point at infinity")
    return ((H[0][0] * x + H[0][1] * y + H[0][2]) / w,
            (H[1][0] * x + H[1][1] * y + H[1][2]) / w)


def cross3(a, b):
    return [a[1] * b[2] - a[2] * b[1], a[2] * b[0] - a[0] * b[2], a[0] * b[1] - a[1] * b[0]]


def svals2(J):
    """Singular values of a 2x2 matrix, descending."""
    a, b = J[0]
    c, d = J[1]
    m = [[a * a + c * c, a * b + c * d], [a * b + c * d, b * b + d * d]]
    tr = m[0][0] + m[1][1]
    det = m[0][0] * m[1][1] - m[0][1] * m[1][0]
    disc = max(tr * tr / 4.0 - det, 0.0)
    l1 = tr / 2.0 + math.sqrt(disc)
    l2 = max(tr / 2.0 - math.sqrt(disc), 0.0)
    return math.sqrt(l1), math.sqrt(l2)


def fit_line_tls(pts):
    """Total-least-squares line.  Returns (point_on_line, unit_direction, rms)."""
    n = len(pts)
    mx = sum(p[0] for p in pts) / n
    my = sum(p[1] for p in pts) / n
    sxx = syy = sxy = 0.0
    for x, y in pts:
        dx = x - mx
        dy = y - my
        sxx += dx * dx
        syy += dy * dy
        sxy += dx * dy
    tr = sxx + syy
    det = sxx * syy - sxy * sxy
    disc = max(tr * tr / 4.0 - det, 0.0)
    l1 = tr / 2.0 + math.sqrt(disc)
    if abs(sxy) > 1e-18:
        vx, vy = l1 - syy, sxy
    else:
        vx, vy = (1.0, 0.0) if sxx >= syy else (0.0, 1.0)
    norm = math.hypot(vx, vy) or 1.0
    vx, vy = vx / norm, vy / norm
    nx, ny = -vy, vx
    res = [abs((x - mx) * nx + (y - my) * ny) for x, y in pts]
    rms = math.sqrt(sum(r * r for r in res) / n)
    return (mx, my), (vx, vy), rms


def polyfit(xs, ys, deg):
    rows = [[x ** k for k in range(deg + 1)] for x in xs]
    return lstsq(rows, list(ys))


def polyval(c, x):
    return sum(ci * x ** i for i, ci in enumerate(c))


def median(v):
    s = sorted(v)
    n = len(s)
    if n == 0:
        return float("nan")
    return s[n // 2] if n % 2 else 0.5 * (s[n // 2 - 1] + s[n // 2])


def percentile(v, q):
    if not v:
        return float("nan")
    s = sorted(v)
    idx = (len(s) - 1) * q
    lo = int(math.floor(idx))
    hi = min(lo + 1, len(s) - 1)
    frac = idx - lo
    return s[lo] * (1 - frac) + s[hi] * frac


def mean(v):
    return sum(v) / len(v) if v else float("nan")


def sd(v):
    n = len(v)
    if n < 2:
        return 0.0
    m = mean(v)
    return math.sqrt(sum((x - m) ** 2 for x in v) / (n - 1))


def mad_sigma(v):
    """Robust sigma estimate via median absolute deviation."""
    m = median(v)
    return 1.4826 * median([abs(x - m) for x in v])


# --------------------------------------------------------------------------
# sRGB linearisation
# --------------------------------------------------------------------------

_DECODE = []
for _i in range(256):
    _c = _i / 255.0
    _DECODE.append(_c / 12.92 if _c <= 0.04045 else ((_c + 0.055) / 1.055) ** 2.4)
SRGB_DECODE = tuple(_DECODE)


def srgb_encode(lin: float) -> float:
    lin = 0.0 if lin < 0.0 else (1.0 if lin > 1.0 else lin)
    return lin * 12.92 if lin <= 0.0031308 else 1.055 * lin ** (1.0 / 2.4) - 0.055


def encode_u8(lin: float) -> int:
    v = int(round(srgb_encode(lin) * 255.0))
    return 0 if v < 0 else (255 if v > 255 else v)


# --------------------------------------------------------------------------
# image buffer
# --------------------------------------------------------------------------


class Img:
    """Single channel image.  `lin` holds linear luminance in [0,1]."""

    __slots__ = ("w", "h", "lin")

    def __init__(self, w: int, h: int, fill: float = 1.0):
        self.w = w
        self.h = h
        self.lin = array("d", [fill]) * (w * h)

    # ---- sampling -------------------------------------------------------
    def at(self, x: int, y: int) -> float:
        if x < 0:
            x = 0
        elif x >= self.w:
            x = self.w - 1
        if y < 0:
            y = 0
        elif y >= self.h:
            y = self.h - 1
        return self.lin[y * self.w + x]

    def bilinear(self, u: float, v: float) -> float:
        x0 = int(math.floor(u))
        y0 = int(math.floor(v))
        fx = u - x0
        fy = v - y0
        a = self.at(x0, y0)
        b = self.at(x0 + 1, y0)
        c = self.at(x0, y0 + 1)
        d = self.at(x0 + 1, y0 + 1)
        return (a * (1 - fx) + b * fx) * (1 - fy) + (c * (1 - fx) + d * fx) * fy

    def inside(self, u: float, v: float, margin: float = 1.0) -> bool:
        return margin <= u < self.w - 1 - margin and margin <= v < self.h - 1 - margin

    # ---- operations -----------------------------------------------------
    def blur_rect(self, x0: int, y0: int, x1: int, y1: int, sigma: float,
                  sigma_y: float = None) -> None:
        """Separable Gaussian restricted to a rectangle (outside assumed flat)."""
        sy = sigma if sigma_y is None else sigma_y
        if sigma <= 1e-6 and sy <= 1e-6:
            return
        x0 = max(x0, 0)
        y0 = max(y0, 0)
        x1 = min(x1, self.w)
        y1 = min(y1, self.h)
        if x1 <= x0 or y1 <= y0:
            return
        for axis, s in ((0, sigma), (1, sy)):
            if s <= 1e-6:
                continue
            r = max(1, int(math.ceil(3.0 * s)))
            k = [math.exp(-0.5 * (i / s) ** 2) for i in range(-r, r + 1)]
            tot = sum(k)
            k = [v / tot for v in k]
            buf = array("d", [0.0]) * ((x1 - x0) * (y1 - y0))
            W = x1 - x0
            for y in range(y0, y1):
                base = (y - y0) * W
                for x in range(x0, x1):
                    acc = 0.0
                    if axis == 0:
                        for i in range(-r, r + 1):
                            acc += k[i + r] * self.at(x + i, y)
                    else:
                        for i in range(-r, r + 1):
                            acc += k[i + r] * self.at(x, y + i)
                    buf[base + (x - x0)] = acc
            for y in range(y0, y1):
                base = (y - y0) * W
                row = y * self.w
                for x in range(x0, x1):
                    self.lin[row + x] = buf[base + (x - x0)]

    def add_noise_rect(self, x0, y0, x1, y1, sigma, rng: Rng) -> None:
        if sigma <= 0.0:
            return
        x0 = max(x0, 0); y0 = max(y0, 0)
        x1 = min(x1, self.w); y1 = min(y1, self.h)
        for y in range(y0, y1):
            row = y * self.w
            for x in range(x0, x1):
                v = self.lin[row + x] + rng.normal(0.0, sigma)
                self.lin[row + x] = 0.0 if v < 0.0 else (1.0 if v > 1.0 else v)

    def quantize_u8(self) -> bytes:
        return bytes(encode_u8(v) for v in self.lin)

    def from_u8(self, data: bytes) -> None:
        dec = SRGB_DECODE
        self.lin = array("d", [dec[b] for b in data])


# --------------------------------------------------------------------------
# PNG (8-bit greyscale, non interlaced)
# --------------------------------------------------------------------------


def _chunk(tag: bytes, payload: bytes) -> bytes:
    return (struct.pack(">I", len(payload)) + tag + payload
            + struct.pack(">I", zlib.crc32(tag + payload) & 0xFFFFFFFF))


def write_png_gray(path, w: int, h: int, data: bytes) -> None:
    raw = bytearray()
    for y in range(h):
        raw.append(0)
        raw += data[y * w:(y + 1) * w]
    out = b"\x89PNG\r\n\x1a\n"
    out += _chunk(b"IHDR", struct.pack(">IIBBBBB", w, h, 8, 0, 0, 0, 0))
    out += _chunk(b"IDAT", zlib.compress(bytes(raw), 6))
    out += _chunk(b"IEND", b"")
    with open(path, "wb") as fh:
        fh.write(out)


def read_png_gray(path):
    with open(path, "rb") as fh:
        blob = fh.read()
    if blob[:8] != b"\x89PNG\r\n\x1a\n":
        raise ValueError("not a PNG")
    pos = 8
    w = h = depth = ctype = None
    idat = bytearray()
    while pos < len(blob):
        ln = struct.unpack(">I", blob[pos:pos + 4])[0]
        tag = blob[pos + 4:pos + 8]
        payload = blob[pos + 8:pos + 8 + ln]
        pos += 12 + ln
        if tag == b"IHDR":
            w, h, depth, ctype = struct.unpack(">IIBB", payload[:10])
        elif tag == b"IDAT":
            idat += payload
        elif tag == b"IEND":
            break
    if depth != 8 or ctype not in (0, 4):
        raise ValueError("only 8-bit greyscale PNG supported (got depth=%s ctype=%s)"
                         % (depth, ctype))
    nch = 1 if ctype == 0 else 2
    raw = zlib.decompress(bytes(idat))
    stride = w * nch
    out = bytearray(w * h)
    prev = bytearray(stride)
    p = 0
    for y in range(h):
        ft = raw[p]
        p += 1
        line = bytearray(raw[p:p + stride])
        p += stride
        if ft == 1:
            for i in range(nch, stride):
                line[i] = (line[i] + line[i - nch]) & 0xFF
        elif ft == 2:
            for i in range(stride):
                line[i] = (line[i] + prev[i]) & 0xFF
        elif ft == 3:
            for i in range(stride):
                a = line[i - nch] if i >= nch else 0
                line[i] = (line[i] + ((a + prev[i]) >> 1)) & 0xFF
        elif ft == 4:
            for i in range(stride):
                a = line[i - nch] if i >= nch else 0
                b = prev[i]
                c = prev[i - nch] if i >= nch else 0
                pa = abs(b - c); pb = abs(a - c); pc = abs(a + b - 2 * c)
                pr = a if (pa <= pb and pa <= pc) else (b if pb <= pc else c)
                line[i] = (line[i] + pr) & 0xFF
        elif ft != 0:
            raise ValueError("bad PNG filter %d" % ft)
        for x in range(w):
            out[y * w + x] = line[x * nch]
        prev = line
    img = Img(w, h)
    img.from_u8(bytes(out))
    return img


def load_json(path):
    with open(path, "r", encoding="utf-8") as fh:
        return json.load(fh)


def dump_json(path, obj) -> None:
    with open(path, "w", encoding="utf-8") as fh:
        fh.write(json.dumps(obj, indent=2, sort_keys=True, ensure_ascii=False))
        fh.write("\n")


def fmt(x, nd=4):
    """Decimal string for persisted numbers (no binary float in results)."""
    if x is None:
        return None
    if isinstance(x, bool):
        return x
    if isinstance(x, float) and (math.isnan(x) or math.isinf(x)):
        return None
    return ("%." + str(nd) + "f") % x
