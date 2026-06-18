import json, sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

path = sys.argv[1] if len(sys.argv) > 1 else "testes/audit_cbd93c7e-96f9-44ff-bb88-c72ac6b3468d.json"

with open(path) as f:
    data = json.load(f)

results = data.get("results", [])
score_data = data.get("score_data", {})
audit_mode = data.get("audit_mode", "unknown")

# Contagens por status
counts = {}
for r in results:
    s = r.get("status", "unknown")
    counts[s] = counts.get(s, 0) + 1

print(f"=== AUDIT RESULT ===")
print(f"Modo: {audit_mode}")
print(f"Score: {score_data.get('score', 0):.1f}%")
print(f"Requisitos aplicáveis: {score_data.get('applicable_requirements', len(results))}")
print(f"")
print("Status breakdown:")
for s, n in sorted(counts.items()):
    print(f"  {s}: {n}")

# not_applicable breakdown
na = [r for r in results if r.get("status") == "not_applicable"]
print(f"\nnot_applicable ({len(na)} total):")
for r in na:
    note = next((n for n in (r.get("notes") or []) if "operacional" in n.lower()), "")
    marker = "[operational_only]" if "operacional" in note else "[project config]"
    print(f"  {marker} {r['requirement_id']} — {r['title']}")

# Problemas reais (non_compliant e future_evidence com score baixo)
issues = [r for r in results if r.get("status") in ("non_compliant", "future_evidence_required")
          and (r.get("requirement_score") or 0) < 50]
print(f"\nGaps prioritários ({len(issues)} requisitos com score < 50):")
for r in sorted(issues, key=lambda x: x.get("requirement_score") or 0):
    print(f"  {r['requirement_id']} [{r['status']}] score={r.get('requirement_score',0)} — {r['title']}")
    if r.get("gap"):
        print(f"    Gap: {r['gap'][:80]}")
