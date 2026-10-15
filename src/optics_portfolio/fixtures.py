"""Manufactured arrays; NOT numerical or analytical Maxwell solutions."""
import numpy as np
from .fields import ContourFields, FIXTURE


def circle_fixture(n=64, radius_m=0.25):
    # E_theta=2*exp(2i theta), Hz=3*exp(2i theta).
    # Algebraic normal S=3; line flux=6*pi*R, without a physical mode claim.
    theta = (np.arange(n)+0.5)*2*np.pi/n
    normal = np.column_stack((np.cos(theta), np.sin(theta)))
    phase = np.exp(2j*theta)
    e = np.zeros((1,n,3), dtype=complex)
    h = np.zeros_like(e)
    e[0,:,0] = -2*np.sin(theta)*phase
    e[0,:,1] = 2*np.cos(theta)*phase
    h[0,:,2] = 3*phase
    return ContourFields(radius_m*normal, normal, np.full(n, radius_m*2*np.pi/n), e,h,FIXTURE)
