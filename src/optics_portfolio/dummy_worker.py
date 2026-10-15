"""Only fixed toy tasks. No external command, user code, input file or solver."""
import argparse
import json
from pathlib import Path
import sys
import time

def main():
    p=argparse.ArgumentParser();p.add_argument('--case',choices=['success','failure','validation_failure','timeout'],required=True)
    case=p.parse_args().case
    print('ALGORITHMIC_FIXTURE_NOT_COMSOL',flush=True)
    if case=='timeout':time.sleep(30)
    if case=='failure':
        print('Intentional dummy failure, exit 7',file=sys.stderr,flush=True)
        return 7
    data={'provenance':'ALGORITHMIC_FIXTURE_NOT_COMSOL','value':sum([1,2,3]),
          'algorithmic_validation':'FAIL' if case=='validation_failure' else 'PASS'}
    with Path('worker_result.json').open('x',encoding='utf-8') as f:json.dump(data,f)
    return 0

if __name__=='__main__':raise SystemExit(main())
