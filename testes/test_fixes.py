import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from engine.requirement_logic_v1 import eval_durability_selection_v1, eval_proxies_models_v1

# Dados do Pacific Biochar / Nova Esperança (durability_option=200, standard=Isometric)
data_dev = {
    "eligibility": {"durability_years": 200, "permanence_claim": True},
    "methodology": {"durability_option": "200", "standard": "Isometric"},
    "biochar": {"characterization": {}},  # sem H/C — operacional
}

data_ops = {
    "eligibility": {"durability_years": 200, "permanence_claim": True},
    "methodology": {"durability_option": "200", "standard": "Isometric"},
    "biochar": {"characterization": {"h_c_ratio": 0.43}},
    "storage": {"soil": {"annual_avg_temp_celsius": 18.5}},
}

data_fail = {
    "eligibility": {"durability_years": 100},  # < 200 anos — hard gate
    "methodology": {},
    "biochar": {"characterization": {}},
}

print("=== eval_durability_selection_v1 ===")
r = eval_durability_selection_v1(data_dev, "development")
print(f"dev (sem H/C): {r['status']} score={r['requirement_score']}")
assert r["status"] == "compliant", f"Expected compliant, got {r['status']}"

r = eval_durability_selection_v1(data_ops, "operational")
print(f"ops (com H/C=0.43): {r['status']} score={r['requirement_score']}")
assert r["status"] == "compliant"

r = eval_durability_selection_v1(data_fail, "development")
print(f"fail (100 anos): {r['status']} — {r.get('gap','')[:50]}")
assert r["status"] == "non_compliant"

print()
print("=== eval_proxies_models_v1 ===")
r = eval_proxies_models_v1(data_dev, "development")
print(f"dev (standard + option): {r['status']} score={r['requirement_score']}")
assert r["status"] == "compliant", f"Expected compliant, got {r['status']}"

r = eval_proxies_models_v1({"methodology": {}}, "development")
print(f"dev (vazio): {r['status']} score={r['requirement_score']}")
assert r["status"] in ("partial", "non_compliant", "future_evidence_required")

r = eval_proxies_models_v1(data_ops, "operational")
print(f"ops (H/C + temp): {r['status']} score={r['requirement_score']}")
assert r["status"] == "compliant"

print()
print("Todos os testes passaram.")
