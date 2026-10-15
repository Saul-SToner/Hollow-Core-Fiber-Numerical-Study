"""Replot authorized saved-solution derivatives; never runs COMSOL.

Figure contracts: (1) mesh-sampled geometry + observed modal intensity;
(2) three already-seen geometry responses; (3) mesh sensitivity + balance.
No interpolation, fitted response curve, statistical CI or mechanism claim.
"""
import argparse
from pathlib import Path
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.collections import LineCollection
from matplotlib.patches import Circle

ROOT=Path(__file__).resolve().parents[1]
DATA=ROOT/'data/derived'
def load(name):return np.genfromtxt(DATA/name,delimiter=',',names=True,encoding='utf-8')

def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--out',type=Path,required=True)
    out=parser.parse_args().out;out.mkdir(parents=True,exist_ok=False)
    plt.rcParams.update({'font.family':'DejaVu Sans','font.size':10,'axes.spines.top':False,'axes.spines.right':False,'svg.fonttype':'none','svg.hashsalt':'g07-portfolio-v1','pdf.fonttype':42})
    blue='#2166ac';orange='#c26b27';gray='#555555'
    def save(fig,name):
        fig.savefig(out/(name+'.png'),dpi=180)
        fig.savefig(out/(name+'.svg'),dpi=180,metadata={'Date':None,'Creator':'Hollow-Core Fiber Numerical Study'})
        # Normalize generated SVG whitespace without changing its geometry.
        svg=out/(name+'.svg')
        svg.write_bytes(('\n'.join(line.rstrip() for line in svg.read_text(encoding='utf-8').splitlines())+'\n').encode('utf-8'))
        plt.close(fig)
    # Geometry and scalar field come from the same source checkpoint identity.
    b=load('center_boundary_segments.csv');f=load('center_parent2_intensity.csv')
    seg=np.stack([np.c_[b['x1_um'],b['y1_um']],np.c_[b['x2_um'],b['y2_um']]],axis=1)
    fig,axes=plt.subplots(1,2,figsize=(11,5.6));fig.subplots_adjust(left=.08,right=.94,bottom=.20,top=.82,wspace=.32)
    for k in range(4):
        angle=k*np.pi/2;rot=np.array([[np.cos(angle),-np.sin(angle)],[np.sin(angle),np.cos(angle)]])
        axes[0].add_collection(LineCollection(seg@rot.T,colors=gray,linewidths=.45,rasterized=True))
    axes[0].add_patch(Circle((0,0),82.6,fill=False,color=orange,lw=1,ls='--'))
    limit=1.03*np.max(abs(seg))
    axes[0].set(xlim=(-limit,limit),ylim=(-limit,limit),xlabel='x [um]',ylabel='y [um]')
    axes[0].set_aspect('equal');axes[0].set_title('a  Mesh-sampled geometry (C4 reconstruction)',fontsize=10)
    # Samples only: no smooth field interpolation over glass or missing points.
    m=axes[1].scatter(f['x_um'],f['y_um'],c=f['normalized_E2'],s=10,marker='s',cmap='magma',vmin=0,vmax=1,rasterized=True)
    axes[1].set(xlabel='x [um]',ylabel='y [um]',xlim=(0,65),ylim=(0,65));axes[1].set_aspect('equal')
    axes[1].set_title('b  CENTER parent 2: original E samples',fontsize=10)
    fig.colorbar(m,ax=axes[1],shrink=.8,label='Normalized |E|² [1]')
    fig.suptitle('G07 | saved COMSOL mode at 1.540 um',fontsize=15)
    fig.text(.08,.085,'Dashed circle: 82.6 um physical-air contour. Left: boundary chords, not exact CAD curves.',fontsize=9)
    fig.text(.08,.035,'Right: original quadrant samples, cropped to 0-65 um; normalized |E|², not energy density.',fontsize=9)
    save(fig,'01_geometry_mode')
    r=load('rint_parent2.csv')
    fig,axes=plt.subplots(1,3,figsize=(12,4.7));fig.subplots_adjust(left=.07,right=.98,bottom=.25,top=.78,wspace=.45)
    for ax,key,label in zip(axes,['a_per_m','phi_low_over_pz_per_m','eta_low'],['a = -Re(s) [1/m]','Low-order net flux / Pz [1/m]','Low-order / total net flux [%]']):
        y=r[key]*(100 if key=='eta_low' else 1)
        ax.plot(r['q']*100,y,'o',color=blue,ms=7)
        ax.set(xlabel='Rint change [%]',ylabel=label,xticks=[-.5,0,.5]);ax.grid(axis='y',alpha=.2)
    fig.suptitle('Matched parent 2 | three already-seen geometries',fontsize=15)
    fig.text(.07,.10,'Mode mapping: CENTER sol2 -> each flank sol4. Negative-side full four-mode identity still fails.',fontsize=9)
    fig.text(.07,.045,'|l| <= 18, l = 2 mod 4; signed net flux at 82.6 um. Not a held-out loss prediction.',fontsize=9)
    save(fig,'02_geometry_response')
    mesh=load('mesh_comparison.csv');balance=load('power_balance_parent2.csv')
    fig,axes=plt.subplots(1,2,figsize=(11,4.9));fig.subplots_adjust(left=.09,right=.97,bottom=.25,top=.79,wspace=.38)
    y=100*mesh['relative_signed_change']
    axes[0].bar([1,2],y,color=[gray,blue],width=.5)
    axes[0].axhline(0,color='black',lw=.7)
    for x,v in zip([1,2],y):axes[0].annotate(f'{v:+.2f}%',(x,v),xytext=(0,7 if v>0 else -15),textcoords='offset points',ha='center')
    axes[0].set(xticks=[1,2],xticklabels=['Parent 1','Parent 2'],ylabel='Signed change in a: original -> M080 [%]',ylim=(-23,5))
    axes[0].set_title('a  One mesh refinement is not convergence',fontsize=10)
    for radius,marker,offset in [(79.6,'o',-.035),(82.6,'s',0),(85.6,'^',.035)]:
        rows=balance[balance['radius_um']==radius];x=rows['q']*100+offset
        for key,col,filled in [('radial_residual_over_pz_per_m',gray,False),('sector_residual_over_pz_per_m',blue,True)]:
            axes[1].scatter(x,100*rows[key]/(2*rows['a_per_m']),marker=marker,s=36,facecolors=col if filled else 'none',edgecolors=col,label=f'{radius} um '+('sector' if filled else 'radial'))
    axes[1].axhline(0,color='black',lw=.7);axes[1].set(xlabel='Rint change [%] (radius offsets for clarity)',ylabel='Signed balance residual / (2a Pz) [%]',xticks=[-.5,0,.5])
    axes[1].set_title('b  Radial and complete-sector residuals differ',fontsize=10)
    axes[1].legend(fontsize=7,ncol=2,loc='upper left',frameon=False)
    fig.suptitle('Numerical reliability | measured sensitivity, not absolute error bounds',fontsize=14)
    fig.text(.09,.035,'PML independence remains unresolved. Balance closure does not certify eigenvalue-loss convergence.',fontsize=9)
    save(fig,'03_numerical_reliability')
    print('Wrote three PNG/SVG figure pairs; actual saved-solution derivatives only.')

if __name__=='__main__':main()
