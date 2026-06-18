import json, sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.stdout.reconfigure(encoding="utf-8")

path = sys.argv[1] if len(sys.argv) > 1 else "testes/audit_cbd93c7e-96f9-44ff-bb88-c72ac6b3468d.json"

with open(path, encoding="utf-8") as f:
    data = json.load(f)

results = data.get("results", [])
partials = [r for r in results if r["status"] in ("partial", "future_evidence_required")]

print(f"=== {len(partials)} GAPS (partial + future_evidence) ===\n")

for r in sorted(partials, key=lambda x: x.get("requirement_score") or 0):
    rid = r["requirement_id"]
    status = r["status"]
    score = r.get("requirement_score") or 0
    title = r["title"]
    gap = (r.get("gap") or "")[:120]
    rec = (r.get("recommendation") or "")[:120]
    missing = r.get("missing_fields") or []
    failed = r.get("failed_fields") or []
    notes = [n for n in (r.get("notes") or [])
             if not n.startswith("[Protocolo]") and "desenvolvimento" not in n.lower()
             and "operacional" not in n.lower()]

    print(f"[{rid}] {status} score={score}")
    print(f"  {title}")
    if missing:
        print(f"  Missing: {missing}")
    if failed:
        print(f"  Failed:  {failed}")
    if gap:
        print(f"  Gap: {gap}")
    if rec and rec != gap:
        print(f"  Rec: {rec}")
    if notes:
        for n in notes:
            print(f"  Note: {n[:100]}")
    print()
