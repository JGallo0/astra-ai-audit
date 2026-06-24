from engine.requirement_logic_v1 import LOGIC_REGISTRY_V1
from engine.requirement_logic_puro_v2025 import (
    eval_puro_protocol_eligibility_v1, eval_puro_project_ownership_v1,
    eval_puro_technical_description_v1, eval_puro_project_participants_v1,
    eval_puro_project_locations_v1, eval_puro_removal_capacity_v1,
    eval_puro_feedstock_eligibility_v1, eval_puro_forest_sustainability_v1,
    eval_puro_land_clearing_v1, eval_puro_product_quality_v1,
    eval_puro_non_soil_application_v1,
    eval_puro_system_boundary_v1, eval_puro_ghg_statement_v1,
    eval_puro_baseline_v1, eval_puro_leakage_v1, eval_puro_uncertainty_v1,
    eval_puro_models_v1,
    eval_puro_financial_additionality_v1, eval_puro_common_practice_additionality_v1,
    eval_puro_environmental_additionality_v1, eval_puro_regulatory_additionality_v1,
    eval_puro_durability_selection_v1, eval_puro_durability_demonstration_v1,
    eval_puro_soil_temp_v1, eval_puro_reversals_v1,
    eval_puro_data_collection_v1, eval_puro_monitoring_parameters_v1,
    eval_puro_sampling_procedure_v1,
    eval_puro_regulatory_compliance_v1, eval_puro_env_social_impact_v1,
    eval_puro_no_net_env_harm_v1, eval_puro_no_net_social_harm_v1,
    eval_puro_pollution_prevention_v1, eval_puro_adaptive_management_v1,
    eval_puro_baseline_soil_v1, eval_puro_soil_quality_monitoring_v1,
    eval_puro_co_benefits_v1,
    eval_puro_stakeholder_consultation_v1, eval_puro_grievance_v1,
    eval_puro_reactor_design_v1, eval_puro_gas_sensors_v1,
    eval_puro_reactor_material_v1, eval_puro_maintenance_v1,
    eval_puro_characterization_standards_v1, eval_puro_biochar_chemical_v1,
    eval_puro_biochar_physical_v1, eval_puro_laboratory_v1,
    eval_puro_closure_plan_v1, eval_puro_sdg_alignment_v1,
)
from engine.requirement_logic_map_puro_v2025 import REQUIREMENT_LOGIC_MAP_PURO_V2025

LOGIC_REGISTRY_PURO_V2025 = {
    fn_name: globals()[fn_name]
    for fn_name in REQUIREMENT_LOGIC_MAP_PURO_V2025.values()
    if fn_name in globals()
}

from engine.requirement_logic_verra_v1 import (
    eval_verra_applicability_v1,
    eval_verra_feedstock_eligibility_v1,
    eval_verra_feedstock_category_v1,
    eval_verra_technology_class_v1,
    eval_verra_hcorg_gate_v1,
    eval_verra_application_type_v1,
    eval_verra_regulatory_surplus_v1,
    eval_verra_positive_list_v1,
    eval_verra_vt0008_investment_v1,
    eval_verra_baseline_v1,
    eval_verra_baseline_feedstock_v1,
    eval_verra_permanence_v1,
    eval_verra_temperature_monitoring_v1,
    eval_verra_carbon_content_v1,
    eval_verra_mass_monitoring_v1,
    eval_verra_process_emissions_v1,
    eval_verra_leakage_v1,
    eval_verra_application_emissions_v1,
    eval_verra_biochar_quality_v1,
    eval_verra_contaminants_v1,
    eval_verra_mineral_additives_v1,
    eval_verra_monitoring_plan_v1,
    eval_verra_chain_of_custody_v1,
    eval_verra_geographic_info_v1,
    eval_verra_data_management_v1,
    eval_verra_reversal_risk_v1,
)
from engine.requirement_logic_map_verra_v1 import REQUIREMENT_LOGIC_MAP_VERRA_V1

LOGIC_REGISTRY_VERRA_V1 = {
    fn_name: globals()[fn_name]
    for fn_name in REQUIREMENT_LOGIC_MAP_VERRA_V1.values()
    if fn_name in globals()
}
from engine.requirement_logic import (
    adaptive_management_plan,
    biochar_characterization_approach,
    biochar_chemical_analysis,
    biochar_incorporation_documentation,
    biochar_required_measurements,
    chain_of_custody_diagram,
    contaminant_monitoring_plan,
    crediting_activity_boundaries,
    deployment_method_selected,
    direct_soil_application_evidence,
    durability_option_declared,
    end_material_process_description,
    engineering_design_diagram,
    environmental_legal_requirements,
    eval_additionality_barriers,
    eval_additionality_core,
    eval_baseline_core,
    eval_baseline_evidence,
    eval_biochar_applicability,
    eval_carbon_accounting_structure,
    eval_emissions_accounting_method,
    eval_feedstock_counterfactual,
    eval_feedstock_origin,
    eval_feedstock_requirements,
    eval_feedstock_traceability,
    eval_leakage_sources,
    eval_leakage_treatment,
    eval_monitoring_requirements,
    eval_project_crediting_context,
    eval_project_ownership,
    eval_reactor_requirements,
    eval_storage_requirements,
    eval_system_boundary,
    feedstock_moisture_management,
    fuel_use_reversal_risk,
    product_standard_compliance,
    pyrolysis_gas_end_use_accounting,
    reactor_design_diagram,
    reactor_maintenance_plan,
    reactor_material_selection,
    regulatory_measurement_methods,
    sampling_batch_definition,
    sampling_plan_consistency,
    stack_emissions_monitoring_method,
    stockpiling_disclosure,
    storage_system_boundary,
    uncertainty_inputs,
    eval_lca_approach,
    eval_lca_scope_coverage,
    eval_lca_data_sources,
    eval_lca_net_removal_logic,
)

LOGIC_REGISTRY = {
    # =========================
    # CANONICAL KEYS USED BY REQUIREMENT_LOGIC_MAP
    # =========================
    "eval_biochar_applicability": eval_biochar_applicability,
    "eval_project_ownership": eval_project_ownership,
    "eval_project_crediting_context": eval_project_crediting_context,
    "durability_option_declared": durability_option_declared,

    "eval_feedstock_requirements": eval_feedstock_requirements,
    "eval_feedstock_origin": eval_feedstock_origin,
    "eval_feedstock_counterfactual": eval_feedstock_counterfactual,
    "feedstock_moisture_management": feedstock_moisture_management,
    "eval_feedstock_traceability": eval_feedstock_traceability,

    "eval_reactor_requirements": eval_reactor_requirements,
    "reactor_maintenance_plan": reactor_maintenance_plan,
    "stack_emissions_monitoring_method": stack_emissions_monitoring_method,
    "crediting_activity_boundaries": crediting_activity_boundaries,

    "biochar_chemical_analysis": biochar_chemical_analysis,
    "biochar_required_measurements": biochar_required_measurements,
    "sampling_plan_consistency": sampling_plan_consistency,
    "biochar_characterization_approach": biochar_characterization_approach,
    "product_standard_compliance": product_standard_compliance,

    "eval_storage_requirements": eval_storage_requirements,
    "stockpiling_disclosure": stockpiling_disclosure,
    "deployment_method_selected": deployment_method_selected,

    "eval_monitoring_requirements": eval_monitoring_requirements,
    "regulatory_measurement_methods": regulatory_measurement_methods,
    "contaminant_monitoring_plan": contaminant_monitoring_plan,

    "chain_of_custody_diagram": chain_of_custody_diagram,

    "eval_additionality_core": eval_additionality_core,
    "eval_additionality_barriers": eval_additionality_barriers,
    "eval_baseline_core": eval_baseline_core,
    "eval_baseline_evidence": eval_baseline_evidence,
    "eval_system_boundary": eval_system_boundary,

    "eval_leakage_sources": eval_leakage_sources,
    "eval_leakage_treatment": eval_leakage_treatment,
    "uncertainty_inputs": uncertainty_inputs,
    "eval_carbon_accounting_structure": eval_carbon_accounting_structure,
    "eval_emissions_accounting_method": eval_emissions_accounting_method,

    "fuel_use_reversal_risk": fuel_use_reversal_risk,
    "adaptive_management_plan": adaptive_management_plan,
    "environmental_legal_requirements": environmental_legal_requirements,

    "reactor_design_diagram": reactor_design_diagram,
    "engineering_design_diagram": engineering_design_diagram,
    "reactor_material_selection": reactor_material_selection,
    "end_material_process_description": end_material_process_description,
    "direct_soil_application_evidence": direct_soil_application_evidence,
    "storage_system_boundary": storage_system_boundary,

    "eval_lca_approach": eval_lca_approach,
    "eval_lca_scope_coverage": eval_lca_scope_coverage,
    "eval_lca_data_sources": eval_lca_data_sources,
    "eval_lca_net_removal_logic": eval_lca_net_removal_logic,
    
    # =========================
    # BACKWARD-COMPATIBLE LEGACY ALIASES
    # =========================
    "biochar_applicability": eval_biochar_applicability,
    "reactor_definition": eval_reactor_requirements,
    "storage_pathway": eval_storage_requirements,
    "feedstock_compliance": eval_feedstock_requirements,
    "monitoring_system": eval_monitoring_requirements,

    # =========================
    # IMPLEMENTED BUT NOT YET MAPPED TO A REQUIREMENT ID
    # =========================
    "sampling_batch_definition": sampling_batch_definition,
    "pyrolysis_gas_end_use_accounting": pyrolysis_gas_end_use_accounting,
    "biochar_incorporation_documentation": biochar_incorporation_documentation,
    # engine v1 — Isometric (R-XXXX protocol-native)
    **LOGIC_REGISTRY_V1,
    # engine v1 — Puro.Earth (P-XXXX protocol-native)
    **LOGIC_REGISTRY_PURO_V2025,
    # engine v1 — Verra VCS VM0044 (V-XXXX protocol-native)
    **LOGIC_REGISTRY_VERRA_V1,
}

