# engine/logic_registry.py

from engine.requirement_logic import (
    eval_biochar_applicability,
    eval_feedstock_requirements,
    eval_reactor_requirements,
    eval_storage_requirements,
    eval_monitoring_requirements,
)

LOGIC_REGISTRY = {
    "eval_biochar_applicability": eval_biochar_applicability,
    "eval_feedstock_requirements": eval_feedstock_requirements,
    "eval_reactor_requirements": eval_reactor_requirements,
    "eval_storage_requirements": eval_storage_requirements,
    "eval_monitoring_requirements": eval_monitoring_requirements,
}
