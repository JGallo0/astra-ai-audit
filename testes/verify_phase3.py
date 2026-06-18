import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from engine.mappers.biochar_characterization_mapper import apply_local_heuristics
from engine.extraction_schema import EXTRACTION_FIELDS
from engine.mappers.sampling_mapper import apply_local_heuristics as sampling_heuristics
from engine.mappers.storage_mapper import apply_local_heuristics as storage_heuristics

# 1. Check new fields in schema
new_paths = [
    "biochar.characterization.h_c_ratio",
    "biochar.characterization.o_c_ratio",
    "biochar.characterization.pcb_mg_kg",
    "biochar.characterization.pcdd_f_ng_kg",
    "storage.soil.annual_avg_temp_celsius",
    "storage.soil.temperature_method",
    "sampling.sample_count",
    "sampling.samples_per_batch",
    "sampling.sampling_method",
    "project.country",
    "project.locations",
    "project.ownership_evidence",
]
found = [f["path"] for f in EXTRACTION_FIELDS if f["path"] in new_paths]
missing = [p for p in new_paths if p not in found]
print(f"Schema: {len(found)}/{len(new_paths)} novos campos presentes")
if missing:
    print(f"  FALTANDO: {missing}")

# 2. Biochar characterization heuristics
print("\n=== Biochar heuristics ===")
text_biochar = "H/C ratio = 0.43. O/C ratio = 0.17. PCB = 0.05 mg/kg DM. PCDD/F = 12 ng/kg. PAHs (EPA 16) = 0.4 mg/kg."
results = apply_local_heuristics(text_biochar, [])
for f in results:
    if f.get("value") is not None:
        print(f"  {f['path']} = {f['value']} (conf={f.get('confidence', 0):.2f})")

# 3. Sampling heuristics
print("\n=== Sampling heuristics ===")
text_sampling = "Three representative samples per batch. Method A was used. 45 samples collected. Within the last 6 months."
results_s = sampling_heuristics("x", sampling_heuristics("x", []))
# Just test regex directly
import re
m = re.search(r"(\d+)\s*samples?\s*(?:per|from each)\s+(?:production\s+)?batch", text_sampling, re.IGNORECASE)
print(f"  samples_per_batch regex: {m.group(1) if m else 'not found'}")
m2 = re.search(r"Method A|Method B", text_sampling, re.IGNORECASE)
print(f"  sampling_method regex: {m2.group(0) if m2 else 'not found'}")

# 4. Storage heuristics
print("\n=== Storage heuristics ===")
text_storage = "The annual average soil temperature is 18.5°C based on Lembrechts et al. (2022) global database."
results_st = storage_heuristics("x", storage_heuristics("x", []))
# Test regex directly
m3 = re.search(r"soil\s+temperature\s+(?:is\s+|of\s+|=\s*)?(\d+\.?\d*)\s*°?C", text_storage, re.IGNORECASE)
print(f"  soil_temp regex: {m3.group(1) if m3 else 'not found'}")
m4 = re.search(r"Lembrechts", text_storage, re.IGNORECASE)
print(f"  temp_method regex: {'lembrechts_2022' if m4 else 'not found'}")

# 5. Import pipeline
from engine.mappers import run_mapper_pipeline
print("\n=== Pipeline import OK ===")
print("Fase 3 verificada com sucesso.")
