import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from backend.main import _load_requirements

reqs = _load_requirements("isometric")
print("Requisitos carregados:", len(reqs))
if reqs:
    print("Primeiro ID:", reqs[0].get("id"))
    print("Logic:", reqs[0].get("logic"))
has_logic = sum(1 for r in reqs if r.get("logic"))
print("Com logic binding:", has_logic, "/", len(reqs))
