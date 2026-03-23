from versioning.methodology_manager import get_requirements
from engine.requirement_logic import run_engine
from schemas.project_schema import get_demo_project_data

project_data = get_demo_project_data()

requirements = get_requirements()
results = run_engine(project_data, requirements)

for r in results:
    print(f'{r["id"]} | {r["status"]} | {r["name"]}') run_engine

project_data = {
    "eligibility": {
        "net_negative_claim": True,
        "additionality_claim": True,
        "durability_years": 500
    },
    "production": {
        "pyrolysis_technology": "continuous"
    },
    "storage": {
        "storage_environment_stable": True
    }
}

requirements = get_requirements()
results = run_engine(project_data, requirements)

print(results)
