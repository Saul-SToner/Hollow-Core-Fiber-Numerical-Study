"""Unified private CLI; original M2 CLI/code remains byte-identical."""
import argparse
import json
from pathlib import Path
import sys

def main():
    p=argparse.ArgumentParser(description='Private M1/M2/M3 algebraic demos only')
    sub=p.add_subparsers(dest='command',required=True)
    m1=sub.add_parser('parameters');m1.add_argument('--config',required=True);m1.add_argument('--out',required=True)
    m2=sub.add_parser('fields-demo');m2.add_argument('--out',required=True)
    m3=sub.add_parser('task-demo');m3.add_argument('--case',choices=['success','failure','validation_failure','timeout'],required=True)
    m3.add_argument('--out',required=True);m3.add_argument('--timeout',type=float,default=10)
    args=p.parse_args()
    try:
        if args.command=='fields-demo':
            from .cli import demo
            return demo(args.out)
        if args.command=='task-demo':
            from .provenance import run_dummy
            result=run_dummy(args.case,args.out,timeout_s=args.timeout)
            print(json.dumps(result))
            return 0 if result['execution_status']=='COMPLETED' and result['algorithmic_validation']=='PASS' else 1
        from .parameters import load_config,evaluate_config,LABEL
        out=Path(args.out);out.mkdir(parents=True,exist_ok=False)
        try:
            config=load_config(args.config);result=evaluate_config(config)
            (out/'result.json').write_text(json.dumps(result,indent=2,allow_nan=False),encoding='utf-8')
            print(json.dumps(result));return 0
        except Exception as exc:
            (out/'failure.json').write_text(json.dumps({'provenance':LABEL,'status':'FAIL',
                'error_type':type(exc).__name__,'reason':str(exc)},indent=2),encoding='utf-8')
            raise
    except (ValueError,OSError) as exc:
        print(f'ERROR: {exc}',file=sys.stderr);return 2

if __name__=='__main__':raise SystemExit(main())
