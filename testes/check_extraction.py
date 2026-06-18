import json, sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.stdout.reconfigure(encoding="utf-8")

path = sys.argv[1] if len(sys.argv) > 1 else "testes/audit_68b28733-ac74-45d8-8703-f78ede7095ea.json"

with open(path, encoding="utf-8") as f:
    data = json.load(f)

pd = data.get("project_data", {})

fields_to_check = [
    "production.system_description",
    "eligibility.eligible_pathway",
    "legal.applicable_environmental_requirements",
    "project.name",
    "project.description",
    "ghg_accounting.leakage_emissions",
    "ghg_accounting.net_cdr",
    "safeguards.environmental_risk_assessment",
    "safeguards.permits_documented",
    "eligibility.additionality_evidence",
]

print("=== CAMPOS EXTRAIDOS DO PROJECT_DATA ===\n")
for field in fields_to_check:
    parts = field.split(".")
    val = pd
    for p in parts:
        val = val.get(p, {}) if isinstance(val, dict) else None

    status = "OK" if val not in (None, [], {}, False, "") else "NULL/VAZIO"
    print(f"  [{status}] {field}: {repr(val)[:80]}")

print("\n=== PROJETO ===")
print(f"  name: {pd.get('project', {}).get('name')}")
print(f"  production.system_description: {str(pd.get('production', {}).get('system_description', ''))[:100]}")
