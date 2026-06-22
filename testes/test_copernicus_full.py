import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.stdout.reconfigure(encoding="utf-8")

os.environ["COPERNICUS_API_KEY"] = "8bd9e97f-61ca-4ea4-9edd-f0a0e799fc53"

from backend.copernicus_service import get_soil_temperature, validate_project_soil_temp

print("=== Teste 1: get_soil_temperature (Pacific Biochar / Humboldt CA) ===")
r = get_soil_temperature(40.5, -124.0, year=2023)
print("  Resultado:", r)

print()
print("=== Teste 2: validacao com temperatura reportada consistente ===")
pd_ok = {
    "project": {"locations": ["40.5, -124.0"]},
    "storage": {"soil": {"annual_avg_temp_celsius": 10.0}},  # muito proximo do C3S
}
v = validate_project_soil_temp(pd_ok)
print("  Status:", v["status"])
print("  C3S:", v["c3s_temp"], "C | Reportada:", v["reported_temp"], "C")
print("  Mensagem:", v["message"][:120])

print()
print("=== Teste 3: validacao com divergencia (temperatura errada) ===")
pd_bad = {
    "project": {"locations": ["40.5, -124.0"]},
    "storage": {"soil": {"annual_avg_temp_celsius": 25.0}},  # muito diferente
}
v2 = validate_project_soil_temp(pd_bad)
print("  Status:", v2["status"])
print("  Divergencia:", v2.get("divergence_c"), "C")
print("  Mensagem:", v2["message"][:120])
