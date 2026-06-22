import json, sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.stdout.reconfigure(encoding="utf-8")

ADD_IDS = {"R-NK7R-0", "R-53Y5-0", "R-RRST-0", "R-CDNF-0", "R-983D-0", "R-KQCS-0"}

with open("testes/audit_fb9c4bee-ec2e-488f-beb8-ef6f7dc7f0c8.json", encoding="utf-8") as f:
    data = json.load(f)

results = data.get("results", [])
pd = data.get("project_data", {})

print("=== ADDITIONALITY DIMENSION ===\n")
for r in results:
    rid = r.get("requirement_id", "")
    if rid not in ADD_IDS:
        continue
    status = r.get("status", "")
    score  = r.get("requirement_score", 0)
    miss   = r.get("missing_fields", [])
    fail   = r.get("failed_fields", [])
    notes  = [n for n in (r.get("notes") or []) if not n.startswith("[Protocolo]")]

    print(f"[{rid}] {status} score={score}")
    print(f"  {r.get('title', '')}")
    if miss: print(f"  Missing: {miss}")
    if fail: print(f"  Failed:  {fail}")
    for n in notes[:2]: print(f"  Note: {n[:90]}")
    print()

print("=== CAMPOS CHAVE NO PROJECT_DATA ===")
legal = pd.get("legal", {})
elig  = pd.get("eligibility", {})
safeg = pd.get("safeguards", {})
print(f"legal.applicable_environmental_requirements: {legal.get('applicable_environmental_requirements')}")
print(f"safeguards.permits_documented:              {safeg.get('permits_documented')}")
print(f"eligibility.additionality_claim:            {elig.get('additionality_claim')}")
print(f"eligibility.additionality_evidence:         {elig.get('additionality_evidence')}")
print(f"eligibility.net_negative_claim:             {elig.get('net_negative_claim')}")
