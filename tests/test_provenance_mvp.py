import hashlib
import json
from pathlib import Path
import pytest
from optics_portfolio.provenance import run_dummy,verify_manifest,write_atomic

@pytest.mark.parametrize('case,execution,code,validation',[
    ('success','COMPLETED',0,'PASS'),('failure','FAILED',7,'NOT_EVALUATED'),
    ('validation_failure','COMPLETED',0,'FAIL'),('timeout','TIMED_OUT',None,'NOT_EVALUATED')])
def test_fixed_workers(case,execution,code,validation,tmp_path):
    folder=tmp_path/case
    r=run_dummy(case,folder,timeout_s=.05 if case=='timeout' else 10)
    assert r['execution_status']==execution and r['exit_code']==code
    assert r['algorithmic_validation']==validation
    assert r['scientific_status']=='NOT_APPLICABLE'
    assert verify_manifest(folder)
    assert (folder/'stdout.log').exists() and (folder/'stderr.log').exists()
    assert 'environment' not in r

def test_failure_log_and_no_overwrite(tmp_path):
    folder=tmp_path/'failure';run_dummy('failure',folder)
    before=(folder/'state.json').read_bytes()
    assert 'Intentional dummy failure' in (folder/'stderr.log').read_text()
    with pytest.raises(FileExistsError):run_dummy('success',folder)
    assert (folder/'state.json').read_bytes()==before

def test_hash_tamper_detection(tmp_path):
    folder=tmp_path/'run';run_dummy('success',folder)
    (folder/'stdout.log').write_text('tampered test copy')
    with pytest.raises(ValueError,match='hash mismatch'):verify_manifest(folder)

@pytest.mark.parametrize('case',['cmd.exe','../worker','success & echo unsafe','unknown'])
def test_no_arbitrary_worker(case,tmp_path):
    with pytest.raises(ValueError,match='fixed dummy'):run_dummy(case,tmp_path/'no_create')
    assert not (tmp_path/'no_create').exists()

@pytest.mark.parametrize('timeout',[0,-1,float('nan'),float('inf'),True,'1'])
def test_bad_timeout(timeout,tmp_path):
    with pytest.raises(ValueError):run_dummy('success',tmp_path/'r',timeout_s=timeout)

def test_atomic_failure_retains_diagnostic(tmp_path,monkeypatch):
    import optics_portfolio.provenance as p
    def fail(*args):raise OSError('intentional replace failure')
    monkeypatch.setattr(p.os,'replace',fail)
    out=tmp_path/'failed'
    with pytest.raises(OSError):run_dummy('success',out)
    assert json.loads((out/'failure.json').read_text())['execution_status']=='RUNNER_ERROR'
    assert list(out.glob('*.tmp'))

def test_manifest_path_validation(tmp_path):
    folder=tmp_path/'run';run_dummy('success',folder)
    m=json.loads((folder/'manifest.json').read_text());m['SHA256']={'../outside':'0'*64}
    (folder/'manifest.json').write_text(json.dumps(m))
    with pytest.raises(ValueError,match='relative filename'):verify_manifest(folder)

def test_request_and_worker_hashes(tmp_path):
    r=run_dummy('success',tmp_path/'r')
    assert r['request_SHA256']==hashlib.sha256((tmp_path/'r/request.json').read_bytes()).hexdigest()
    assert len(r['worker_SHA256'])==64
