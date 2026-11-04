from __future__ import annotations
import argparse,json
from pathlib import Path
from app.db.session import SessionLocal
from app.evaluation.retrieval_eval import run_retrieval_evaluation,serialize_results
ROOT=Path(__file__).resolve().parents[1]
def main()->None:
    p=argparse.ArgumentParser();p.add_argument("--dataset",type=Path,default=ROOT/"data/evaluation_cases.json");p.add_argument("--output",type=Path,default=ROOT/"artifacts/retrieval_evaluation.json");args=p.parse_args();args.output.parent.mkdir(parents=True,exist_ok=True);db=SessionLocal()
    try:
        results,summaries=run_retrieval_evaluation(db,args.dataset);payload=serialize_results(results,summaries);args.output.write_text(json.dumps(payload,indent=2),encoding="utf-8");print(json.dumps(payload["summary"],indent=2));print(f"Saved detailed evaluation to {args.output}")
    finally:db.close()
if __name__=="__main__":main()
