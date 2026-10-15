"""Executable algebraic fixture demo; refuses overwrite and real-data claims."""
import argparse
from dataclasses import asdict
import hashlib
import json
from pathlib import Path
import sys
import numpy as np
from .fields import FIXTURE, complex_scalar_fit, signed_poynting, weighted_fourier
from .fixtures import circle_fixture


def demo(out):
    out = Path(out)
    out.mkdir(parents=True, exist_ok=False)
    try:
        data = circle_fixture()
        density, flux = signed_poynting(data)
        theta = np.arctan2(data.coords_m[:,1], data.coords_m[:,0]) % (2*np.pi)
        phase = np.exp(2j*theta)
        coefficients = weighted_fourier(phase,theta,np.full(len(theta),2*np.pi/len(theta)),[0,2,4])
        fit = complex_scalar_fit(phase, (1+2j)*phase, np.ones(len(theta)))
        expected = 6*np.pi*0.25
        checks = {'flux_reference': bool(np.isclose(flux[0],expected,rtol=1e-12,atol=1e-12)),
                  'fourier_reference': bool(np.allclose(coefficients,[0,1,0],rtol=0,atol=1e-12)),
                  'fit_reference': bool(abs(fit.alpha-(1+2j))<1e-12 and fit.relative_residual<1e-12)}
        f = asdict(fit); f['alpha']=[fit.alpha.real,fit.alpha.imag]
        result={'provenance':FIXTURE, 'status':'PASS' if all(checks.values()) else 'FAIL',
                'checks':checks,'signed_line_flux_W_per_m_arithmetic':float(flux[0]),
                'expected_arithmetic_flux':float(expected),'fit':f,
                'warning':'Manufactured arrays do not certify Maxwell equations, loss, radiation channels or convergence.'}
        np.savez_compressed(out/'fixture.npz',provenance=np.array(FIXTURE),coords_m=data.coords_m,
            normal=data.normal,ds_m=data.ds_m,E=data.E,H=data.H)
        (out/'result.json').write_text(json.dumps(result,indent=2,allow_nan=False),encoding='utf-8')
        hashes={p.name:hashlib.sha256(p.read_bytes()).hexdigest() for p in out.iterdir() if p.is_file()}
        (out/'manifest.json').write_text(json.dumps({'provenance':FIXTURE,'SHA256':hashes},indent=2),encoding='utf-8')
        print(json.dumps(result))
        return 0 if all(checks.values()) else 1
    except Exception as exc:
        (out/'failure.json').write_text(json.dumps({'provenance':FIXTURE,'error':repr(exc)}),encoding='utf-8')
        raise


def main():
    parser=argparse.ArgumentParser(description='M2 algebraic fixtures only; no COMSOL/real data')
    sub=parser.add_subparsers(dest='command',required=True)
    d=sub.add_parser('fields-demo');d.add_argument('--out',required=True)
    args=parser.parse_args()
    try:
        return demo(args.out)
    except (ValueError,OSError) as exc:
        print(f'ERROR: {exc}',file=sys.stderr)
        return 2

if __name__=='__main__':
    raise SystemExit(main())
