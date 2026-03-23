# scripts/test_engine.py

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
from versioning.methodology_manager import get_requirements
from engine.requirement_logic import run_engine

requirements = get_requirements()

results = run_engine(project_data, requirements)

print(results)
