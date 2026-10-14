import argparse
import json
from pathlib import Path
from .store import Store, canonical
from .quality import report
from .features import rolling


def main():
    p=argparse.ArgumentParser(); p.add_argument('--db',default='data/historical/edge.sqlite')
    subs=p.add_subparsers(dest='action',required=True)
    imp=subs.add_parser('import'); imp.add_argument('file'); imp.add_argument('--parent')
    quality=subs.add_parser('quality'); quality.add_argument('version')
    for name in ('state','features'):
        sub=subs.add_parser(name); sub.add_argument('version'); sub.add_argument('match_id'); sub.add_argument('as_of')
    args=p.parse_args(); store=Store(args.db)
    try:
        if args.action=='import': result={'dataset_version':store.ingest([json.loads(line) for line in Path(args.file).read_text().splitlines() if line.strip()],args.parent)}
        elif args.action=='quality': result=report(store,args.version)
        elif args.action=='features': result=rolling(store,args.version,args.match_id,args.as_of)
        else: result=store.get_state(args.match_id,args.as_of,args.version)
        print(canonical(result))
    finally: store.close()


if __name__=='__main__': main()
