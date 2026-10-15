from dataclasses import replace
import numpy as np
import pytest
from optics_portfolio.fields import (ContourFields, ContractError, FIXTURE,
    signed_poynting, weighted_fourier, complex_scalar_fit)
from optics_portfolio.fixtures import circle_fixture


def test_flux_analytic_reference():
    d=circle_fixture();p,f=signed_poynting(d)
    np.testing.assert_allclose(p,3,rtol=0,atol=2e-15)
    np.testing.assert_allclose(f,6*np.pi*.25,rtol=1e-14)


@pytest.mark.parametrize('operation',['normal','H','phase'])
def test_power_sign_and_phase(operation):
    d=circle_fixture(); ref=signed_poynting(d)[1]
    if operation=='normal': t=replace(d,normal=-d.normal); expected=-ref
    elif operation=='H': t=replace(d,H=-d.H); expected=-ref
    else:
        phase=np.exp(.891j);t=replace(d,E=phase*d.E,H=phase*d.H);expected=ref
    np.testing.assert_allclose(signed_poynting(t)[1],expected,rtol=1e-14)


def test_radius_si_scaling():
    d=circle_fixture(radius_m=.003)
    np.testing.assert_allclose(signed_poynting(d)[1],6*np.pi*.003,rtol=1e-14)


def test_azimuthal_quadrature_flux_nonuniform():
    x,w=np.polynomial.legendre.leggauss(32)
    theta=(x+1)*np.pi;dt=w*np.pi;r=.125
    normal=np.column_stack([np.cos(theta),np.sin(theta)])
    e=np.zeros((1,32,3),complex);h=np.zeros_like(e)
    # Etheta=2, Hz=3(1+cos theta): integral is exactly 6*pi*r.
    e[0,:,0]=-2*normal[:,1];e[0,:,1]=2*normal[:,0]
    h[0,:,2]=3*(1+np.cos(theta))
    d=ContourFields(r*normal,normal,r*dt,e,h,FIXTURE)
    np.testing.assert_allclose(signed_poynting(d)[1],6*np.pi*r,rtol=1e-13)


def test_full_fourier_known_coefficients():
    n=64;t=(np.arange(n)+.5)*2*np.pi/n;w=np.full(n,2*np.pi/n)
    f=(2-1j)*np.exp(-3j*t)+(.5+.2j)*np.exp(2j*t)
    c=weighted_fourier(f,t,w,[-3,0,2])
    np.testing.assert_allclose(c,[2-1j,0,.5+.2j],atol=1e-14)
    recovered=np.exp(1j*np.outer(t,[-3,0,2]))@c
    np.testing.assert_allclose(recovered,f,atol=1e-14)


def test_c4_sector_and_no_automatic_full_circle_multiplier():
    period=np.pi/2;n=64;t=(np.arange(n)+.5)*period/n
    f=2*np.exp(2j*t)+3j*np.exp(6j*t)
    c=weighted_fourier(f,t,np.full(n,period/n),[2,6,10],period=period)
    np.testing.assert_allclose(c,[2,3j,0],atol=1e-14)


def test_nonuniform_fourier_complex_columns():
    x,w=np.polynomial.legendre.leggauss(80);t=(x+1)*np.pi
    f=np.column_stack([np.exp(2j*t),2j*np.exp(-1j*t)])
    c=weighted_fourier(f,t,w*np.pi,[-1,2])
    np.testing.assert_allclose(c,[[0,2j],[1,0]],atol=2e-14)


def test_truncation_is_not_false_convergence():
    t=(np.arange(64)+.5)*2*np.pi/64
    c=weighted_fourier(np.exp(8j*t),t,np.full(64,2*np.pi/64),[0,1,2])
    assert np.linalg.norm(c)<1e-14  # omitted mode is not a reconstructed field!


def test_flux_direct_and_finite_angular_sum():
    t=(np.arange(64)+.5)*2*np.pi/64;dt=np.full(64,2*np.pi/64);r=.2
    et=2*np.exp(2j*t)+np.exp(-2j*t)
    hz=3*np.exp(2j*t)-2*np.exp(-2j*t)
    n=np.column_stack([np.cos(t),np.sin(t)])
    e=np.zeros((1,64,3),complex);h=np.zeros_like(e)
    e[0,:,0]=-et*n[:,1];e[0,:,1]=et*n[:,0];h[0,:,2]=hz
    d=ContourFields(r*n,n,r*dt,e,h,FIXTURE)
    ce=weighted_fourier(et,t,dt,[-2,2]);ch=weighted_fourier(hz,t,dt,[-2,2])
    np.testing.assert_allclose(signed_poynting(d)[1],np.pi*r*np.vdot(ch,ce).real,atol=1e-14)


@pytest.mark.parametrize('scale',[1.,1e-100,1e100])
def test_exact_complex_fit(scale):
    b=np.array([1+1j,2-3j,-2j])*scale;a=1.2-.7j
    fit=complex_scalar_fit(b,a*b,[1,2,3])
    assert abs(fit.alpha-a)<1e-14
    assert fit.relative_residual<1e-14
    assert fit.overlap==pytest.approx(1)


def test_fit_known_orthogonal_error():
    b=np.array([1,0],complex);t=np.array([2+3j,4],complex)
    f=complex_scalar_fit(b,t,[1,1])
    assert f.alpha==pytest.approx(2+3j)
    assert f.relative_residual==pytest.approx(4/np.sqrt(29))
    assert f.orthogonality_defect<1e-15
    assert f.relative_residual**2+f.overlap**2==pytest.approx(1)


def test_fit_phase_covariance_and_weighted_reference():
    b=np.array([1+2j,3-1j]);t=np.array([2-1j,4+2j]);w=np.array([2.,7.])
    f=complex_scalar_fit(b,t,w);phase=np.exp(.51j)
    expected=np.sum(w*b.conj()*t)/np.sum(w*abs(b)**2)
    assert f.alpha==pytest.approx(expected)
    g=complex_scalar_fit(b,phase*t,w)
    assert g.alpha==pytest.approx(phase*f.alpha)
    assert g.relative_residual==pytest.approx(f.relative_residual)


def test_zero_handling():
    with pytest.raises(ContractError,match='zero reference'):
        complex_scalar_fit(np.zeros(2,complex),np.ones(2,complex),[1,1])
    f=complex_scalar_fit(np.ones(2,complex),np.zeros(2,complex),[1,1])
    assert f.alpha==0 and f.relative_residual is None and f.overlap is None


@pytest.mark.parametrize('key,value',[
    ('length_unit','um'),('electric_unit','kV/m'),('magnetic_unit','V/m'),
    ('phasor','rms'),('provenance','COMSOL_SAVED_SOLUTION'),
    ('coords_m',np.zeros((3,3))),('normal',np.zeros((64,2))),
    ('normal',np.full((64,2),np.nan)),('ds_m',np.zeros(64)),
    ('ds_m',np.ones(63)),('ds_m',np.ones(64,dtype=complex)),
    ('E',np.ones((1,64,3))),('E',np.ones((64,3),complex)),
    ('H',np.ones((2,64,3),complex)),('E',np.full((1,64,3),np.inf+0j)),
])
def test_contract_rejects(key,value):
    with pytest.raises(ContractError): replace(circle_fixture(),**{key:value})


def test_defensive_copy_and_read_only_arrays():
    d=circle_fixture();a=d.E.copy();e=replace(d,E=a);a[:]=0
    assert np.any(e.E!=0)
    with pytest.raises(ValueError): e.E[0,0,0]=1


@pytest.mark.parametrize('args',[
    (np.ones(2),np.ones(2,complex),[1,1]),
    (np.ones(2,complex),np.ones(3,complex),[1,1]),
    (np.ones(2,complex),np.ones(2,complex),[-1,1]),
    (np.ones(2,complex),np.array([complex(np.nan),1]),[1,1]),
])
def test_fit_rejects(args):
    with pytest.raises(ContractError):complex_scalar_fit(*args)


@pytest.mark.parametrize('bad', ['weight','node','order','value','period','origin'])
def test_fourier_rejects(bad):
    t=np.array([.2,3.]);w=np.full(2,np.pi);f=np.ones(2,complex);o=[0,1];kw={}
    if bad=='weight':w[0]=-1
    if bad=='node':t=t[::-1]
    if bad=='order':o=[1,1]
    if bad=='value':f=f.real
    if bad=='period':kw['period']=0
    if bad=='origin':kw['origin']=np.nan
    with pytest.raises(ContractError):weighted_fourier(f,t,w,o,**kw)
