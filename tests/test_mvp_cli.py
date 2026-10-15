import json
from pathlib import Path
import subprocess
import sys
import pytest

ROOT=Path(__file__).resolve().parents[1]

@pytest.mark.parametrize('name,expected', [('toy_valid.json',0),('toy_invalid.json',2)])
def test_parameters_cli_unrelated_cwd(name,expected,tmp_path):
    out=tmp_path/'params'
    args=[sys.executable,'-I','-B','-m','optics_portfolio.mvp_cli','parameters',
          '--config',str(ROOT/'examples/configs'/name),'--out',str(out)]
    r=subprocess.run(args,cwd=tmp_path,capture_output=True,text=True)
    assert r.returncode==expected,(r.stdout,r.stderr)
    if expected==0:
        assert json.loads((out/'result.json').read_text())['values_si']['half_width']==pytest.approx(.004)
    else:assert 'unknown' in json.loads((out/'failure.json').read_text())['reason']
    before={p.name:p.read_bytes() for p in out.iterdir()}
    assert subprocess.run(args,cwd=tmp_path,capture_output=True).returncode==2
    assert before=={p.name:p.read_bytes() for p in out.iterdir()}

@pytest.mark.parametrize('case,expected',[('success',0),('failure',1),('validation_failure',1)])
def test_task_cli(case,expected,tmp_path):
    args=[sys.executable,'-I','-B','-m','optics_portfolio.mvp_cli','task-demo','--case',case,'--out',str(tmp_path/'run')]
    r=subprocess.run(args,cwd=tmp_path,capture_output=True,text=True)
    assert r.returncode==expected,(r.stdout,r.stderr)
    state=json.loads((tmp_path/'run/state.json').read_text())
    assert state['provenance']=='ALGORITHMIC_FIXTURE_NOT_COMSOL'

def test_m2_via_unified_cli(tmp_path):
    r=subprocess.run([sys.executable,'-I','-B','-m','optics_portfolio.mvp_cli','fields-demo','--out',str(tmp_path/'m2')],cwd=tmp_path,capture_output=True)
    assert r.returncode==0,r.stderr

def test_module_dependency_separation():
    import ast
    import optics_portfolio
    root=Path(optics_portfolio.__file__).parent
    for name in ['parameters.py','provenance.py','dummy_worker.py']:
        tree=ast.parse((root/name).read_text())
        for node in ast.walk(tree):
            modules=[]
            if isinstance(node,ast.Import):modules=[n.name for n in node.names]
            elif isinstance(node,ast.ImportFrom):modules=[node.module or '']
            assert all(not x.startswith(('numpy','fields','cli','mph','jpype','dnanf')) for x in modules)
