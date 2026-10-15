"""Standard peak-phasor cross products, quadrature and complex projection.

No Maxwell solver, model adapter, real-field importer, or hidden data path.
"""
from dataclasses import dataclass
import numpy as np

FIXTURE = "ALGORITHMIC_FIXTURE_NOT_COMSOL"


class ContractError(ValueError):
    """Invalid numerical input, units or explicit provenance."""


def _real(value, name):
    a = np.asarray(value)
    if a.dtype.kind not in "fiu" or not np.all(np.isfinite(a)):
        raise ContractError(f"{name}: finite real numeric array required")
    return a.astype(float, copy=True)


def _complex(value, name):
    a = np.asarray(value)
    if a.dtype.kind != "c" or not np.all(np.isfinite(a)):
        raise ContractError(f"{name}: finite explicit complex array required")
    return a.astype(np.complex128, copy=True)


@dataclass(frozen=True)
class ContourFields:
    """Transverse line integral per unit z; Cartesian xyz E/H, peak phasors.

    Values carry declared SI units, but numeric magnitudes cannot certify units.
    Normals are supplied independently, not inferred from point ordering.
    No automatic C4 replication or Pz normalization is performed.
    """
    coords_m: np.ndarray
    normal: np.ndarray
    ds_m: np.ndarray
    E: np.ndarray
    H: np.ndarray
    provenance: str
    length_unit: str = "m"
    electric_unit: str = "V/m"
    magnetic_unit: str = "A/m"
    phasor: str = "peak_exp_positive_iwt"

    def __post_init__(self):
        if self.provenance != FIXTURE:
            raise ContractError("This private prototype accepts algebraic fixtures only")
        if (self.length_unit, self.electric_unit, self.magnetic_unit, self.phasor) != (
            "m", "V/m", "A/m", "peak_exp_positive_iwt"
        ):
            raise ContractError("SI units and peak exp(+i omega t) contract required")
        xy = _real(self.coords_m, "coords_m")
        n = _real(self.normal, "normal")
        w = _real(self.ds_m, "ds_m")
        e = _complex(self.E, "E")
        h = _complex(self.H, "H")
        if xy.ndim != 2 or xy.shape[1] != 2 or len(xy) < 2:
            raise ContractError("coords_m must have shape (N,2), N>=2")
        if n.shape != xy.shape or w.shape != (len(xy),):
            raise ContractError("normal (N,2), ds_m (N,) must match coordinates")
        if not np.all(w > 0) or not np.allclose(np.linalg.norm(n, axis=1), 1, rtol=0, atol=1e-12):
            raise ContractError("positive ds_m and unit normals required")
        if e.ndim != 3 or e.shape != h.shape or e.shape[1:] != (len(xy), 3) or e.shape[0] < 1:
            raise ContractError("E and H must share shape (M,N,3), M>=1")
        for key, val in [("coords_m", xy), ("normal", n), ("ds_m", w), ("E", e), ("H", h)]:
            val.setflags(write=False)
            object.__setattr__(self, key, val)


def signed_poynting(data):
    """Return normal density (M,N), W/m², and transverse line flux (M,), W/m.

    Manufactured samples only: units describe arithmetic, not physical validity.
    """
    if not isinstance(data, ContourFields):
        raise ContractError("ContourFields required")
    with np.errstate(over="raise", invalid="raise"):
        cross = np.cross(data.E, np.conjugate(data.H))
        density = 0.5 * np.sum(cross[..., :2].real * data.normal, axis=-1)
        flux = density @ data.ds_m
    if not np.all(np.isfinite(flux)):
        raise ContractError("nonfinite flux")
    return density, flux


def _quadrature(theta, weights, period, origin):
    t = _real(theta, "theta_rad")
    w = _real(weights, "dtheta")
    if not np.isscalar(period) or not np.isfinite(period) or period <= 0:
        raise ContractError("positive finite angular period required")
    if not np.isscalar(origin) or not np.isfinite(origin):
        raise ContractError("finite origin required")
    if t.ndim != 1 or len(t) < 2 or w.shape != t.shape or not np.all(w > 0):
        raise ContractError("positive angular weights must match 1D theta")
    if not np.all(np.diff(t) > 0) or np.any(t < origin) or np.any(t >= origin + period):
        raise ContractError("strictly increasing nodes in half-open angular interval required")
    if not np.isclose(w.sum(), period, rtol=1e-12, atol=1e-14):
        raise ContractError("angular weight sum must equal declared period")
    return t, w


def weighted_fourier(values, theta_rad, dtheta, orders, *, period=2*np.pi, origin=0.0):
    """Quadrature coefficients c_l=integral(f exp(-il theta))/period.

    values shape (N,) or (N,C); result shape (L,) or (L,C).
    This is a moment integral, not a least-squares inverse for arbitrary grids.
    Orthogonal reconstruction/Parseval require an appropriate angular family.
    """
    t, w = _quadrature(theta_rad, dtheta, period, origin)
    f = _complex(values, "values")
    o = np.asarray(orders)
    if o.ndim != 1 or not len(o) or o.dtype.kind not in "iu" or len(np.unique(o)) != len(o):
        raise ContractError("unique integer angular orders required")
    if f.ndim not in (1, 2) or f.shape[0] != len(t):
        raise ContractError("values must have shape (N,) or (N,C)")
    kernel = np.exp(-1j * np.outer(o, t)) * (w / period)
    return kernel @ f


@dataclass(frozen=True)
class ScalarFit:
    alpha: complex
    overlap: float | None
    relative_residual: float | None
    residual_norm: float
    orthogonality_defect: float


def complex_scalar_fit(reference, target, weights):
    """Positive weighted least squares target≈alpha*reference, no physics metric.

    Stable normalization removes absolute vector scale. Near-zero has no universal
    physical cutoff: exact zero reference raises; exact zero target has undefined
    overlap/relative residual. Caller supplies any application-specific floor.
    """
    b = _complex(reference, "reference")
    t = _complex(target, "target")
    w = _real(weights, "weights")
    if b.ndim != 1 or not len(b) or t.shape != b.shape or w.shape != b.shape or not np.all(w > 0):
        raise ContractError("nonempty matching 1D vectors and positive weights required")
    sb = np.max(np.abs(b)); st = np.max(np.abs(t))
    if sb == 0:
        raise ContractError("zero reference: alpha is not identifiable")
    if st == 0:
        return ScalarFit(0j, None, None, 0.0, 0.0)
    v = w / np.max(w)
    bn = b/sb; tn = t/st
    bb = np.vdot(bn, v*bn).real
    tt = np.vdot(tn, v*tn).real
    cross = np.vdot(bn, v*tn)
    a = cross / bb
    delta = tn-a*bn
    rr = np.sqrt(np.vdot(delta, v*delta).real / tt)
    overlap = float(np.clip(abs(cross)/np.sqrt(bb*tt), 0, 1))
    alpha = a * (st/sb)
    norm = st * np.sqrt(np.vdot(delta, w*delta).real)
    defect = abs(np.vdot(bn, v*delta))/np.sqrt(bb*tt)
    if not all(np.isfinite(x) for x in (alpha, rr, norm, defect)):
        raise ContractError("fit exceeds finite floating-point range")
    return ScalarFit(complex(alpha), overlap, float(rr), float(norm), float(defect))
