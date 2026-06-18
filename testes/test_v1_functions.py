import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from engine.requirement_logic_v1 import (
    eval_biochar_chemical_properties_v1,
    eval_sampling_procedure_v1,
    eval_pollution_prevention_v1,
    eval_reversals_v1,
    eval_durability_selection_v1,
    eval_adaptive_management_v1,
    eval_reactor_design_v1,
    eval_stakeholder_consultation_v1,
    eval_data_collection_v1,
)

PASS = 0
FAIL = 0

def check(label, got, expected_status, expected_score_min=None):
    global PASS, FAIL
    ok = got["status"] == expected_status
    if expected_score_min is not None:
        ok = ok and (got.get("requirement_score") or 0) >= expected_score_min
    if ok:
        PASS += 1
        print(f"  OK  {label}: {got['status']} score={got.get('requirement_score')}")
    else:
        FAIL += 1
        print(f"  FAIL {label}: got {got['status']} score={got.get('requirement_score')}, expected {expected_status} gap={got.get('gap','')[:50]}")

print("=== Biochar chemical properties ===")
data_ok = {"biochar": {"characterization": {"h_c_ratio": 0.43, "lab_reports": True,
    "chemical_analysis_performed": True, "pollutants": {"PCBs": 0.1, "dioxins": 15}}}}
data_fail_hc = {"biochar": {"characterization": {"h_c_ratio": 0.62}}}
data_fail_pcb = {"biochar": {"characterization": {"h_c_ratio": 0.3, "pollutants": {"PCBs": 0.5}}}}

check("H/C=0.43 dev", eval_biochar_chemical_properties_v1(data_ok, "development"), "compliant")
check("H/C=0.43 ops", eval_biochar_chemical_properties_v1(data_ok, "operational"), "compliant")
check("H/C=0.62 FAIL", eval_biochar_chemical_properties_v1(data_fail_hc, "operational"), "non_compliant", 0)
check("PCB=0.5 FAIL", eval_biochar_chemical_properties_v1(data_fail_pcb, "operational"), "non_compliant", 0)

print("\n=== Sampling procedure ===")
data_ok_s = {"sampling": {"sampling_plan_defined": True, "sampling_method": "method_a", "samples_per_batch": 3}}
data_fail_mb = {"sampling": {"sampling_plan_defined": True, "sampling_method": "method_b",
    "sample_count": 15, "samples_per_batch": 3}}
data_fail_batch = {"sampling": {"sampling_plan_defined": True, "sampling_method": "method_a", "samples_per_batch": 1}}

check("Method A ok dev", eval_sampling_procedure_v1(data_ok_s, "development"), "compliant")
check("Method B <30 FAIL ops", eval_sampling_procedure_v1(data_fail_mb, "operational"), "non_compliant")
check("1 sample/batch FAIL ops", eval_sampling_procedure_v1(data_fail_batch, "operational"), "non_compliant")

print("\n=== Pollution prevention ===")
# Dados químicos ok mas sem safeguards.mitigation_plan → partial (correto)
check("PAH ok dev (sem plano mitigacao=partial)", eval_pollution_prevention_v1(data_ok, "development"), "partial")
check("PCB=0.5 FAIL ops", eval_pollution_prevention_v1(data_fail_pcb, "operational"), "non_compliant")

print("\n=== Reversals ===")
data_r = {"methodology": {"storage_pathway": "soil"}, "management": {
    "adaptive_management_plan": True, "pause_or_stop_conditions": True}}
check("Reversals ok soil", eval_reversals_v1(data_r, "development"), "compliant")

print("\n=== Durability ===")
data_d = {"eligibility": {"durability_years": 200, "permanence_claim": True},
    "methodology": {"durability_option": "200"},
    "biochar": {"characterization": {"h_c_ratio": 0.43}}}
data_fail_dur = {"eligibility": {"durability_years": 100}}
check("Durability 200yr ok", eval_durability_selection_v1(data_d, "development"), "compliant")
check("Durability 100yr FAIL", eval_durability_selection_v1(data_fail_dur, "development"), "non_compliant")

print("\n=== Adaptive management ===")
data_am = {"management": {"adaptive_management_plan": True, "emergency_response_plan": True,
    "pause_or_stop_conditions": True, "information_sharing_plan": True}}
check("Adaptive mgmt ok", eval_adaptive_management_v1(data_am, "development"), "compliant")
check("Adaptive mgmt empty", eval_adaptive_management_v1({}, "operational"), "non_compliant")

print("\n=== Reactor design ===")
data_rr = {"production": {"reactor_design_diagram": True, "maintenance_plan": True,
    "end_material_process_description": True, "system_description": "BST-30 pyrolysis system"}}
check("Reactor design ok", eval_reactor_design_v1(data_rr, "development"), "compliant")

print("\n=== Stakeholder consultation ===")
data_sh = {"safeguards": {"stakeholder_input_process": True},
    "management": {"information_sharing_plan": True}}
check("Stakeholder ok", eval_stakeholder_consultation_v1(data_sh, "development"), "compliant")
check("Stakeholder empty ops", eval_stakeholder_consultation_v1({}, "operational"), "non_compliant")

print(f"\n{'='*40}")
print(f"TOTAL: {PASS} passou, {FAIL} falhou")
