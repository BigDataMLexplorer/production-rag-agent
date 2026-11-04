from __future__ import annotations
import argparse,json
from pathlib import Path
import matplotlib.pyplot as plt
ROOT=Path(__file__).resolve().parents[1]
def main()->None:
    p=argparse.ArgumentParser();p.add_argument("--input",type=Path,default=ROOT/"artifacts/retrieval_evaluation.json");p.add_argument("--output",type=Path,default=ROOT/"artifacts/retrieval_quality.png");args=p.parse_args()
    rows=json.loads(args.input.read_text(encoding="utf-8"))["summary"];modes=[r["mode"] for r in rows];values=[r["mrr"] for r in rows]
    args.output.parent.mkdir(parents=True,exist_ok=True);fig,ax=plt.subplots(figsize=(8,4.5));ax.bar(modes,values);ax.set_ylim(0,1);ax.set_ylabel("Mean Reciprocal Rank");ax.set_title("Retrieval quality by pipeline");ax.grid(axis="y",alpha=.2);fig.tight_layout();fig.savefig(args.output,dpi=180);print(f"Saved chart to {args.output}")
if __name__=="__main__":main()
