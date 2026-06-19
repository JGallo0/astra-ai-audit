import sys, json, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.stdout.reconfigure(encoding="utf-8")

from backend.rating_service import compute_readiness_rating

with open("testes/audit_fb9c4bee-ec2e-488f-beb8-ef6f7dc7f0c8.json", encoding="utf-8") as f:
    data = json.load(f)

rating = compute_readiness_rating(
    results=data.get("results", []),
    overall_score=data.get("score_data", {}).get("score", 0),
    audit_mode=data.get("audit_mode", "development"),
)

print(f"Grade: {rating['grade']} — {rating['label']}")
print(f"Score: {rating['overall_score']}%")
print(f"Descricao: {rating['description'][:80]}")
print()
print("Dimensoes:")
for k, d in rating["dimensions"].items():
    print(f"  {d['label']}: {d['score']}% ({d['applicable_count']} req, {d['na_count']} N/A)")
