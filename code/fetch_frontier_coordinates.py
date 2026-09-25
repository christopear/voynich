"""Fetch missing public coordinate files at the version used in our protocol."""
import concurrent.futures
import json
from pathlib import Path

import requests

ROOT=Path(__file__).resolve().parents[1]
TREE="956a7c4fc39981f4d116fa3f4edfccce6d065571"
BASE=f"https://raw.githubusercontent.com/lrozanova/voynich-units/{TREE}/"


def main():
    dest=ROOT/"data/frontier"
    (dest/"boxes").mkdir(parents=True,exist_ok=True)
    tree_path=dest/"source_tree.json"
    if not tree_path.exists():
        r=requests.get(f"https://api.github.com/repos/lrozanova/voynich-units/git/trees/{TREE}?recursive=1",timeout=60)
        r.raise_for_status()
        tree_path.write_text(json.dumps(r.json(),indent=2))
    tree=json.loads(tree_path.read_text())
    assert tree["sha"]==TREE
    paths=[x["path"] for x in tree["tree"] if "/voynichese_boxes/" in x["path"] and x["path"].endswith(".js")]
    def fetch(path):
        target=dest/"boxes"/Path(path).name
        if not target.exists():
            r=requests.get(BASE+path,timeout=60)
            r.raise_for_status()
            # Reject HTML/error payloads before saving as a coordinate file.
            assert len(r.json())==2
            target.write_bytes(r.content)
        return target
    with concurrent.futures.ThreadPoolExecutor(max_workers=8) as executor:
        completed=list(executor.map(fetch,paths))
    print(f"Ready: {len(completed)} coordinate files at tree {TREE}")


if __name__=="__main__":main()
