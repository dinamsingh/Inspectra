"""Pinhole camera with Brown-Conrady distortion, poses, and plane homographies.

Conventions
-----------
* World / "plane" coordinates are millimetres in the fiducial frame's coordinate
  system: X right, Y up, Z out of the printed surface towards the camera.
* A *surface* is always a plane in P0-min: either z = 0 (the fiducial plane), a
  plane offset by `d`, or a plane tilted by `alpha` about the X axis and offset
  by `d`.  Planes keep every mapping an exact homography (no iterative inverse),
  and a small glyph patch on a bowed carton is to first order exactly such a
  tilted + offset plane.  See docs/P0_ASSUMPTIONS.md A-05.
"""
from __future__ import annotations

import math

from .core import apply_h, cross3, mat3_inv, mat3_mul, svals2


class Camera:
    __slots__ = ("fx", "fy", "cx", "cy", "dist", "width", "height")

    def __init__(self, fx, fy, cx, cy, dist=(0.0, 0.0, 0.0, 0.0, 0.0), width=0, height=0):
        self.fx = float(fx)
        self.fy = float(fy)
        self.cx = float(cx)
        self.cy = float(cy)
        self.dist = tuple(float(v) for v in dist)
        self.width = int(width)
        self.height = int(height)

    # ---- serialisation --------------------------------------------------
    def to_dict(self):
        return {"fx": self.fx, "fy": self.fy, "cx": self.cx, "cy": self.cy,
                "dist": list(self.dist), "width": self.width, "height": self.height}

    @staticmethod
    def from_dict(d):
        return Camera(d["fx"], d["fy"], d["cx"], d["cy"], d.get("dist", (0,) * 5),
                      d.get("width", 0), d.get("height", 0))

    @property
    def K(self):
        return [[self.fx, 0.0, self.cx], [0.0, self.fy, self.cy], [0.0, 0.0, 1.0]]

    @property
    def f_px(self):
        return 0.5 * (self.fx + self.fy)

    @property
    def has_distortion(self):
        return any(abs(c) > 1e-12 for c in self.dist)

    # ---- distortion -----------------------------------------------------
    def distort_norm(self, x, y):
        k1, k2, p1, p2, k3 = self.dist
        r2 = x * x + y * y
        rad = 1.0 + k1 * r2 + k2 * r2 * r2 + k3 * r2 * r2 * r2
        xd = x * rad + 2.0 * p1 * x * y + p2 * (r2 + 2.0 * x * x)
        yd = y * rad + p1 * (r2 + 2.0 * y * y) + 2.0 * p2 * x * y
        return xd, yd

    def undistort_norm(self, xd, yd, iters=12):
        x, y = xd, yd
        for _ in range(iters):
            ex, ey = self.distort_norm(x, y)
            dx = xd - ex
            dy = yd - ey
            x += dx
            y += dy
            if abs(dx) < 1e-12 and abs(dy) < 1e-12:
                break
        return x, y

    # ---- pixel <-> normalised ------------------------------------------
    def to_px(self, xn, yn):
        return self.fx * xn + self.cx, self.fy * yn + self.cy

    def to_norm(self, u, v):
        return (u - self.cx) / self.fx, (v - self.cy) / self.fy

    def undistort_px(self, u, v):
        """Distorted pixel -> ideal pixel (equivalent of cv2.undistortPoints with P=K)."""
        if not self.has_distortion:
            return u, v
        xn, yn = self.to_norm(u, v)
        x, y = self.undistort_norm(xn, yn)
        return self.to_px(x, y)

    def distort_px(self, u, v):
        """Ideal pixel -> distorted pixel."""
        if not self.has_distortion:
            return u, v
        xn, yn = self.to_norm(u, v)
        xd, yd = self.distort_norm(xn, yn)
        return self.to_px(xd, yd)

    # ---- projection -----------------------------------------------------
    def project(self, R, t, P):
        xc = R[0][0] * P[0] + R[0][1] * P[1] + R[0][2] * P[2] + t[0]
        yc = R[1][0] * P[0] + R[1][1] * P[1] + R[1][2] * P[2] + t[1]
        zc = R[2][0] * P[0] + R[2][1] * P[1] + R[2][2] * P[2] + t[2]
        if zc <= 1e-9:
            raise ValueError("point behind camera")
        xd, yd = self.distort_norm(xc / zc, yc / zc)
        return self.to_px(xd, yd)


# --------------------------------------------------------------------------
# poses and plane homographies
# --------------------------------------------------------------------------


def rot_x(a):
    c, s = math.cos(a), math.sin(a)
    return [[1.0, 0.0, 0.0], [0.0, c, -s], [0.0, s, c]]


def rot_y(a):
    c, s = math.cos(a), math.sin(a)
    return [[c, 0.0, s], [0.0, 1.0, 0.0], [-s, 0.0, c]]


def rot_z(a):
    c, s = math.cos(a), math.sin(a)
    return [[c, -s, 0.0], [s, c, 0.0], [0.0, 0.0, 1.0]]


def transpose3(M):
    return [[M[j][i] for j in range(3)] for i in range(3)]


def matvec3(M, v):
    return [M[i][0] * v[0] + M[i][1] * v[1] + M[i][2] * v[2] for i in range(3)]


# Base orientation: world +X -> cam +x, world +Y -> cam -y (image y down),
# world +Z -> cam -z, so a surface at z = 0 seen from z = +Z is in front.
R_BASE = [[1.0, 0.0, 0.0], [0.0, -1.0, 0.0], [0.0, 0.0, -1.0]]


def pose_looking_at_origin(z_mm, tilt_deg, azimuth_deg=0.0, roll_deg=0.0,
                           shift_mm=(0.0, 0.0)):
    """Camera orbiting the plane origin at distance `z_mm`, oblique by `tilt_deg`.

    The optical axis always passes through the world origin (plus an optional
    lateral `shift_mm` of the camera centre, which makes the view off-centre and
    therefore exercises lens distortion away from the principal point).
    Returns (R, t) mapping world -> camera coordinates.
    """
    Rw = mat3_mul(rot_y(math.radians(azimuth_deg)), rot_x(math.radians(tilt_deg)))
    C = matvec3(Rw, [0.0, 0.0, z_mm])
    C = [C[0] + shift_mm[0], C[1] + shift_mm[1], C[2]]
    R = mat3_mul(rot_z(math.radians(roll_deg)), mat3_mul(R_BASE, transpose3(Rw)))
    t = [-v for v in matvec3(R, C)]
    return R, t


def plane_pose(R, t, d_mm=0.0, alpha_deg=0.0):
    """Pose of a surface plane offset by `d_mm` along +Z and tilted by `alpha_deg`.

    Returns (R_s, t_s) such that a point (X, Y) on the surface maps to camera
    coordinates R_s @ (X, Y, 1).
    """
    Rl = rot_x(math.radians(alpha_deg))
    Rs = mat3_mul(R, Rl)
    origin = [0.0, 0.0, d_mm]
    ts = [R[i][0] * origin[0] + R[i][1] * origin[1] + R[i][2] * origin[2] + t[i]
          for i in range(3)]
    return Rs, ts


def homography_for_plane(cam: Camera, R, t, d_mm=0.0, alpha_deg=0.0):
    """Ideal (distortion-free) homography plane(X,Y,1) -> pixel."""
    Rs, ts = plane_pose(R, t, d_mm, alpha_deg)
    M = [[Rs[0][0], Rs[0][1], ts[0]],
         [Rs[1][0], Rs[1][1], ts[1]],
         [Rs[2][0], Rs[2][1], ts[2]]]
    return mat3_mul(cam.K, M)


def plane_to_distorted_px(cam: Camera, H, x_mm, y_mm):
    u, v = apply_h(H, x_mm, y_mm)
    return cam.distort_px(u, v)


def distorted_px_to_plane(cam: Camera, Hinv, u, v):
    ui, vi = cam.undistort_px(u, v)
    return apply_h(Hinv, ui, vi)


# --------------------------------------------------------------------------
# homography derived quantities
# --------------------------------------------------------------------------


def jacobian(H, x, y):
    w = H[2][0] * x + H[2][1] * y + H[2][2]
    u = (H[0][0] * x + H[0][1] * y + H[0][2]) / w
    v = (H[1][0] * x + H[1][1] * y + H[1][2]) / w
    return [[(H[0][0] - u * H[2][0]) / w, (H[0][1] - u * H[2][1]) / w],
            [(H[1][0] - v * H[2][0]) / w, (H[1][1] - v * H[2][1]) / w]]


def rho_at(H, x, y):
    """(rho_geometric_mean, rho_min, jacobian_ratio) in px/mm at a plane point."""
    s1, s2 = svals2(jacobian(H, x, y))
    if s2 <= 1e-12:
        return 0.0, 0.0, float("inf")
    return math.sqrt(s1 * s2), s2, s1 / s2


def view_tilt_deg(cam: Camera, H):
    """Angle between the plane normal and the camera optical axis, from H."""
    Hn = mat3_mul(mat3_inv(cam.K), H)
    h1 = [Hn[0][0], Hn[1][0], Hn[2][0]]
    h2 = [Hn[0][1], Hn[1][1], Hn[2][1]]
    n1 = math.sqrt(sum(c * c for c in h1))
    n2 = math.sqrt(sum(c * c for c in h2))
    if n1 < 1e-12 or n2 < 1e-12:
        return float("nan")
    lam = 2.0 / (n1 + n2)
    r1 = [c * lam for c in h1]
    r2 = [c * lam for c in h2]
    r3 = cross3(r1, r2)
    nr = math.sqrt(sum(c * c for c in r3)) or 1.0
    cosang = min(1.0, abs(r3[2] / nr))
    return math.degrees(math.acos(cosang))


def z_estimate_mm(cam: Camera, H, x, y):
    rho, _, _ = rho_at(H, x, y)
    if rho <= 1e-9:
        return float("nan")
    return cam.f_px / rho
