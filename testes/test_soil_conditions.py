import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.stdout.reconfigure(encoding="utf-8")

os.environ["COPERNICUS_API_KEY"] = "8bd9e97f-61ca-4ea4-9edd-f0a0e799fc53"

from backend.copernicus_service import get_soil_moisture, validate_project_soil_conditions

print("=== Teste 1: get_soil_moisture (Pacific Biochar, Humboldt CA) ===")
m = get_soil_moisture(40.5, -124.0, year=2023)
print(f"  moisture: {m.get('moisture_m3_m3')} m3/m3")
print(f"  risk: {m.get('permanence_risk')}")
print(f"  note: {m.get('risk_note', '')[:100]}")

print()
print("=== Teste 2: validate_project_soil_conditions (ambas as variaveis) ===")
pd = {
    "project": {"locations": ["40.5, -124.0"]},
    "storage": {"soil": {"annual_avg_temp_celsius": 11.0}},
}
v = validate_project_soil_conditions(pd)
print(f"  status: {v['status']}")
print(f"  risk_flags: {v['risk_flags']}")
print(f"  temperatura: {v['temperature']['message']}")
print(f"  umidade: {v['moisture']['risk_note'][:100]}")
