from methodology_requirements import get_requirements_for_methodology
from engine.requirement_logic_map_v1 import REQUIREMENT_LOGIC_MAP_V1
from engine.requirement_logic_v1 import LOGIC_REGISTRY_V1
from engine.logic_registry import LOGIC_REGISTRY

reqs = get_requirements_for_methodology("isometric", engine_version="v1")
print("Requisitos v1 carregados:", len(reqs))
print("Primeiro ID:", reqs[0]["id"])
print("Ultimo ID:", reqs[-1]["id"])
print("Logic map v1:", len(REQUIREMENT_LOGIC_MAP_V1), "entradas")
print("Logic registry total:", len(LOGIC_REGISTRY), "funcoes")

missing = [k for k in REQUIREMENT_LOGIC_MAP_V1.values() if k not in LOGIC_REGISTRY]
print("Funcoes faltando no registry:", missing if missing else "nenhuma")

# Todos os requisitos têm logic?
no_logic = [r["id"] for r in reqs if not r.get("logic")]
print("Requisitos sem logic:", no_logic if no_logic else "nenhum")

# Legacy ainda funciona?
legacy = get_requirements_for_methodology("isometric", engine_version="legacy")
print("Requisitos legacy:", len(legacy))
