import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from methodology_requirements import get_requirements_for_methodology

reqs = get_requirements_for_methodology("isometric", engine_version="v1")
ops_only = [r for r in reqs if r.get("mode_applicability") == "operational_only"]
both = [r for r in reqs if r.get("mode_applicability", "both") == "both"]

print(f"Total: {len(reqs)}")
print(f"operational_only: {len(ops_only)} — excluidos do score em desenvolvimento")
print(f"both: {len(both)} — avaliados em ambos os modos")
print()
print("IDs operational_only:")
for r in ops_only:
    print(f"  {r['id']} — {r['title']}")

print()
print("Score em desenvolvimento (denominador):", len(both), "requisitos")
print("Score em operacional (denominador):", len(reqs), "requisitos")
