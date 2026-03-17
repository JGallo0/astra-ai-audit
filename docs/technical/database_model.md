# Database Model

## Main entities
- users
- projects
- project_documents
- audit_runs
- audit_results
- filler_runs
- filler_outputs
- standards
- methodologies
- modules
- criteria
- parameters

## users
- email
- name
- role
- status
- created_at
- last_login

## projects
- id
- owner_email
- project_name
- project_type
- country
- target_standard
- target_methodology
- created_at

## audit_runs
- id
- run_id
- project_id
- analysis_mode
- execution_mode
- overall_score
- overall_confidence
- estimated_cost
- summary_json
- trails_json
- created_at

## audit_results
- id
- run_id
- requirement_id
- module
- title
- status
- risk
- score
- confidence
- project_evidence
- methodology_basis
- gap
- recommendation
- notes

## filler_runs
- id
- project_id
- filler_type
- template_name
- created_at
- output_summary

## filler_outputs
- id
- filler_run_id
- output_type
- file_name
- file_path
- created_at
