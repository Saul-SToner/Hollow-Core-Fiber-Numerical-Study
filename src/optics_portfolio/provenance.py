"""Minimal fixed-dummy task trace; not a general command runner or scheduler."""
from datetime import datetime,timezone
import hashlib
import importlib.metadata
import json
import math
import os
from pathlib import Path
import subprocess
import sys
import uuid

LABEL='ALGORITHMIC_FIXTURE_NOT_COMSOL'
CASES=frozenset({'success','failure','validation_failure','timeout'})

def digest(path):
    with Path(path).open('rb') as f:return hashlib.file_digest(f,'sha256').hexdigest()

def write_atomic(path,data):
    path=Path(path);temp=path.with_name(path.name+'.'+uuid.uuid4().hex+'.tmp')
    with temp.open('x',encoding='utf-8') as f:json.dump(data,f,indent=2,allow_nan=False)
    os.replace(temp,path)  # retain temp if replacement fails; no transactional claim

def _time():return datetime.now(timezone.utc).isoformat()

def run_dummy(case,out,*,timeout_s=10):
    if case not in CASES:raise ValueError('only fixed dummy cases allowed')
    if isinstance(timeout_s,bool) or not isinstance(timeout_s,(int,float)) or not math.isfinite(timeout_s) or timeout_s<=0:
        raise ValueError('positive finite timeout required')
    out=Path(out);out.mkdir(parents=True,exist_ok=False)
    state={'provenance':LABEL,'execution_status':'RUNNING','algorithmic_validation':'NOT_EVALUATED',
           'scientific_status':'NOT_APPLICABLE','case':case,'exit_code':None,'started_utc':_time(),
           'resource_monitoring':'UNAVAILABLE_NOT_IMPLEMENTED'}
    try:
        write_atomic(out/'request.json',{'provenance':LABEL,'case':case,'timeout_s':timeout_s})
        write_atomic(out/'state.json',state)
        worker=Path(__file__).with_name('dummy_worker.py')
        state['worker_SHA256']=digest(worker);state['request_SHA256']=digest(out/'request.json')
        # No arbitrary command arguments, shell, full environment or research path.
        env={k:os.environ[k] for k in ['SystemRoot','WINDIR','TEMP','TMP','LANG'] if k in os.environ}
        env.update(PYTHONIOENCODING='utf-8',PYTHONDONTWRITEBYTECODE='1')
        cmd=[sys.executable,'-I','-B','-m','optics_portfolio.dummy_worker','--case',case]
        with (out/'stdout.log').open('xb') as stdout,(out/'stderr.log').open('xb') as stderr:
            try:
                proc=subprocess.run(cmd,cwd=out,env=env,shell=False,stdout=stdout,stderr=stderr,timeout=timeout_s)
                state['exit_code']=proc.returncode
                state['execution_status']='COMPLETED' if proc.returncode==0 else 'FAILED'
            except subprocess.TimeoutExpired:
                state['execution_status']='TIMED_OUT'
        if state['execution_status']=='COMPLETED':
            result=json.loads((out/'worker_result.json').read_text(encoding='utf-8'))
            if result.get('provenance')!=LABEL or result.get('algorithmic_validation') not in ['PASS','FAIL']:
                raise ValueError('invalid dummy result contract')
            state['algorithmic_validation']=result['algorithmic_validation']
        state['ended_utc']=_time()
        state['runtime']={'python':sys.version.split()[0],
            'package_version':importlib.metadata.version('hollow-core-fiber-numerical-study')}
        write_atomic(out/'state.json',state)
        artifacts={p.name:digest(p) for p in out.iterdir() if p.is_file()}
        write_atomic(out/'manifest.json',{'provenance':LABEL,'SHA256':artifacts})
        return state
    except Exception as exc:
        with (out/'failure.json').open('x',encoding='utf-8') as f:
            json.dump({'provenance':LABEL,'execution_status':'RUNNER_ERROR','error_type':type(exc).__name__,
                       'note':'Diagnostic and partials preserved; not a valid completed task'},f,indent=2)
        raise

def verify_manifest(folder):
    folder=Path(folder).resolve()
    manifest=json.loads((folder/'manifest.json').read_text(encoding='utf-8'))
    if manifest.get('provenance')!=LABEL:raise ValueError('unsupported manifest provenance')
    table=manifest.get('SHA256')
    if not isinstance(table,dict) or not table:raise ValueError('nonempty SHA256 table required')
    for name,expected in table.items():
        if not isinstance(name,str) or '/' in name or '\\' in name or name in ('.','..') or Path(name).name!=name:
            raise ValueError('manifest path must be a single relative filename')
        p=folder/name
        if p.is_symlink() or p.resolve().parent!=folder:raise ValueError('manifest path escapes folder')
        if not isinstance(expected,str) or len(expected)!=64 or any(c not in '0123456789abcdef' for c in expected):
            raise ValueError('invalid SHA256 digest')
        if digest(p)!=expected:raise ValueError(f'hash mismatch: {name}')
    return True
