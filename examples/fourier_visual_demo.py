"""Python-only, unitless algebraic illustration; not an electromagnetic field.

Figure contract: known finite Fourier coefficients are recovered by weighted
quadrature. Quantitative two-panel grid (coefficient reference + reconstruction).
PNG for README, SVG with editable text; no statistical or physical claims.
"""
import argparse
import json
from pathlib import Path
import numpy as np
from optics_portfolio.fields import FIXTURE,weighted_fourier

def main():
    parser=argparse.ArgumentParser(description='Artificial Fourier arithmetic only')
    parser.add_argument('--out',required=True)
    out=Path(parser.parse_args().out);out.mkdir(parents=True,exist_ok=False)
    # Independently manufactured function, no research data or geometric input.
    n=64;theta=(np.arange(n)+.5)*2*np.pi/n;weights=np.full(n,2*np.pi/n)
    orders=np.arange(-6,7,dtype=int)
    values=.8*np.exp(-3j*theta)+(1+.5j)*np.exp(2j*theta)
    expected=np.zeros(len(orders),complex)
    expected[orders==-3]=.8;expected[orders==2]=1+.5j
    coefficients=weighted_fourier(values,theta,weights,orders)
    recovered=np.exp(1j*np.outer(theta,orders))@coefficients
    coefficient_error=float(np.max(abs(coefficients-expected)))
    reconstruction_error=float(np.max(abs(recovered-values)))
    assert coefficient_error<1e-12 and reconstruction_error<1e-12

    import matplotlib
    matplotlib.use('Agg')
    import matplotlib.pyplot as plt
    plt.rcParams.update({'font.family':'DejaVu Sans','font.size':10,'axes.spines.top':False,
                         'axes.spines.right':False,'svg.fonttype':'none','pdf.fonttype':42})
    fig=plt.figure(figsize=(11.2,4.5))
    grid=fig.add_gridspec(1,2,left=.075,right=.98,bottom=.18,top=.76,wspace=.28,width_ratios=[1.2,1])
    ax=fig.add_subplot(grid[0]);bx=fig.add_subplot(grid[1])
    blue='#2166ac';gray='#515151'
    ax.vlines(orders,0,abs(coefficients),color=blue,linewidth=1.6)
    ax.plot(orders,abs(expected),'o',markerfacecolor='white',markeredgecolor=gray,markersize=7,label='Analytical reference')
    ax.plot(orders,abs(coefficients),'x',color=blue,markersize=5,label='Computed quadrature')
    ax.set(xlabel='Angular order l',ylabel='Coefficient magnitude [a.u.]',ylim=(-.055,1.45),xticks=np.arange(-6,7,2))
    ax.set_title('Known coefficients recovered',loc='left',fontsize=11)
    ax.legend(loc='upper left',frameon=False,fontsize=9)
    ax.text(.98,.96,f'Max error: {coefficient_error:.1e}',transform=ax.transAxes,ha='right',va='top',fontsize=9)
    bx.plot(theta/np.pi,values.real,color=gray,lw=2,label='Manufactured input')
    bx.plot(theta/np.pi,recovered.real,color=blue,lw=1.6,ls='--',label='Fourier reconstruction')
    bx.set(xlabel=r'Angle $\theta/\pi$',ylabel='Re(f) [a.u.]',xticks=[0,.5,1,1.5,2])
    bx.set_title('Finite-series reconstruction',loc='left',fontsize=11)
    bx.legend(loc='upper center',frameon=False,fontsize=9)
    fig.text(.075,.94,'Weighted Fourier computation',fontsize=16,weight='bold')
    fig.text(.075,.85,'ARTIFICIAL DATA - SOFTWARE ARITHMETIC ONLY',fontsize=11,color=blue,weight='bold')
    fig.text(.075,.035,'ALGORITHMIC_FIXTURE_NOT_COMSOL | 64 deterministic samples | Not a Maxwell solution',fontsize=9,color=gray)
    fig.canvas.draw();renderer=fig.canvas.get_renderer();canvas=fig.bbox
    for text in fig.findobj(match=matplotlib.text.Text):
        if text.get_visible() and text.get_text():
            bbox=text.get_window_extent(renderer)
            assert bbox.x0>=canvas.x0-1 and bbox.x1<=canvas.x1+1 and bbox.y0>=canvas.y0-1 and bbox.y1<=canvas.y1+1,'Text outside canvas'
    fig.savefig(out/'fourier_demo.png',dpi=180,metadata={'Title':'Artificial Fourier arithmetic demo'})
    fig.savefig(out/'fourier_demo.svg',metadata={'Title':'Artificial Fourier arithmetic demo','Creator':'Hollow-Core-Fiber-Numerical-Study','Date':None})
    plt.close(fig)
    payload={'provenance':FIXTURE,'function':'.8 exp(-3 i theta) + (1+.5i) exp(2 i theta)',
             'sample_count':n,'theta_rad':theta.tolist(),'weights_rad':weights.tolist(),
             'orders':orders.tolist(),'coefficients_real':coefficients.real.tolist(),
             'coefficients_imag':coefficients.imag.tolist(),'expected_real':expected.real.tolist(),
             'expected_imag':expected.imag.tolist(),'max_coefficient_error':coefficient_error,
             'max_reconstruction_error':reconstruction_error,'text_canvas_check':'PASS',
             'warning':'Unitless artificial test function, not E/H, radiation or loss data'}
    (out/'fourier_demo_data.json').write_text(json.dumps(payload,indent=2,allow_nan=False),encoding='utf-8')
    print(json.dumps({k:payload[k] for k in ['provenance','max_coefficient_error','max_reconstruction_error','text_canvas_check']}))

if __name__=='__main__':main()
