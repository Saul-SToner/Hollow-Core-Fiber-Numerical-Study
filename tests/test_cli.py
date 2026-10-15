import json
from pathlib import Path
import subprocess
import sys
import numpy as np
from optics_portfolio.fields import FIXTURE


def test_cli_runs_outside_project_and_preserves_outputs(tmp_path):
    out=tmp_path/'demo';cwd=tmp_path/'unrelated';cwd.mkdir()
    cmd=[sys.executable,'-I','-B','-m','optics_portfolio.cli','fields-demo','--out',str(out)]
    p=subprocess.run(cmd,cwd=cwd,capture_output=True,text=True)
    assert p.returncode==0,(p.stdout,p.stderr)
    r=json.loads((out/'result.json').read_text())
    assert r['provenance']==FIXTURE and r['status']=='PASS'
    assert all(r['checks'].values())
    with np.load(out/'fixture.npz',allow_pickle=False) as f:
        assert str(f['provenance'])==FIXTURE
    before=(out/'result.json').read_bytes()
    q=subprocess.run(cmd,cwd=cwd,capture_output=True,text=True)
    assert q.returncode!=0
    assert (out/'result.json').read_bytes()==before


def test_package_has_no_research_or_solver_imports():
    import ast
    import optics_portfolio
    root=Path(optics_portfolio.__file__).parent
    banned={'mph','jpype','scipy','ngsolve','pyeigfeast','dnanf'}
    for p in root.glob('*.py'):
        tree=ast.parse(p.read_text(encoding='utf-8'))
        for node in ast.walk(tree):
            if isinstance(node,ast.Import):names=[a.name.split('.')[0] for a in node.names]
            elif isinstance(node,ast.ImportFrom):names=[(node.module or '').split('.')[0]]
            else:continue
            assert not banned.intersection(names)
