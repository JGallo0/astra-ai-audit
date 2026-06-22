import sys, json, os, re
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.stdout.reconfigure(encoding="utf-8")

# Load env
with open(os.path.join(os.path.dirname(__file__), '..', 'comply_toml.txt')) as f:
    for line in f:
        m = re.match(r'^([A-Z_]+)\s*=\s*["\']?(.+?)["\']?\s*$', line.strip())
        if m:
            os.environ[m.group(1)] = m.group(2)

os.environ.setdefault("COPERNICUS_API_KEY", "8bd9e97f-61ca-4ea4-9edd-f0a0e799fc53")

from backend.copernicus_service import validate_project_soil_conditions, _parse_coordinates

print("=== _parse_coordinates ===")
tests = [["Scotia, CA"], ["Humboldt County, CA"], ["40.5, -124.0"]]
for t in tests:
    print(f"  {t} -> {_parse_coordinates(t)}")

print()
print("=== validate_project_soil_conditions (Scotia, CA) ===")
project_data = {
    "project": {"locations": ["Scotia, CA"]},
    "storage": {"soil": {"annual_avg_temp_celsius": 11.0}},
}
result = validate_project_soil_conditions(project_data)
print(json.dumps(result, indent=2, ensure_ascii=False, default=str))
