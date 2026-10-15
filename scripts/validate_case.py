"""Small independent checks on the published derivatives, not a Maxwell solve."""
import hashlib,json
from pathlib import Path
import numpy as np
ROOT=Path(__file__).resolve().parents[1]
def load(n):return np.genfromtxt(ROOT/'data/derived'/n,delimiter=',',names=True,encoding='utf-8')
def validate():
    r=load('rint_parent2.csv');b=load('power_balance_parent2.csv');c=load('low_order_tangential_coefficients.csv')
    assert len(r)==3 and len(b)==9 and len(c)==30
    np.testing.assert_array_equal(r['q'],[-.005,0,.005])
    np.testing.assert_array_equal(r['solution_index_1based'],[4,2,4])
    assert np.all(r['parent2_overlap']>=.8)
    np.testing.assert_allclose(r['a_per_m'],-r['s_real_per_m'],rtol=1e-14)
    np.testing.assert_allclose(r['beta_real_per_m'],-r['s_imag_per_m'],rtol=1e-14)
    np.testing.assert_allclose(r['eta_low'],r['phi_low_over_pz_per_m']/r['phi_total_over_pz_per_m'],rtol=1e-12)
    for row in r:
        z=c[c['q']==row['q']];assert np.all(z['l']%4==2) and np.all(abs(z['l'])<=18)
        values={n:z[n+'_real']+1j*z[n+'_imag'] for n in ['Etheta','Ez','Htheta','Hz']}
        phi=np.pi*82.6e-6*np.real(values['Etheta']*values['Hz'].conj()-values['Ez']*values['Htheta'].conj()).sum()
        np.testing.assert_allclose(phi,row['phi_low_over_pz_per_m'],rtol=2e-12,atol=1e-13)
    np.testing.assert_allclose(b['sector_residual_over_pz_per_m'],b['radial_residual_over_pz_per_m']-b['side_over_pz_per_m'],rtol=1e-12,atol=1e-15)
    m=load('mesh_comparison.csv')
    np.testing.assert_allclose(m['relative_signed_change'],m['a_m080_per_m']/m['a_original_per_m']-1,atol=1e-15)
    assert np.all(m['squared_overlap']>.99)
    f=load('center_parent2_intensity.csv');assert len(f)==2304
    assert np.isfinite(f['normalized_E2']).all() and np.min(f['normalized_E2'])>=0 and f['normalized_E2'].max()==1
    p=ROOT/'manifest.json'
    if p.exists():
        for name,h in json.loads(p.read_text())['SHA256'].items():assert hashlib.sha256((ROOT/name).read_bytes()).hexdigest()==h,name
    return {'status':'DERIVED_DATA_CONSISTENCY_PASS','max_published_closure_relative':float(b['closure_relative'].max()),'new_physics_solves':0}
if __name__=='__main__':print(json.dumps(validate(),indent=2))
