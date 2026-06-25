"""Gera compliance matrix + summary com rating para verificar o grade no PDF."""
import sys, os, json, re
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.stdout.reconfigure(encoding="utf-8")

# Load env
with open(os.path.join(os.path.dirname(__file__), '..', 'comply_toml.txt')) as f:
    for line in f:
        m = re.match(r'^([A-Z_]+)\s*=\s*["\']?(.+?)["\']?\s*$', line.strip())
        if m:
            os.environ[m.group(1)] = m.group(2)

# Load latest audit result
audit_file = os.path.join(os.path.dirname(__file__), 'audit_fb9c4bee-ec2e-488f-beb8-ef6f7dc7f0c8.json')
with open(audit_file, encoding='utf-8') as f:
    result = json.load(f)

results_list = result.get("results", result.get("findings", []))
score_data   = result.get("score_data", {})
audit_mode   = result.get("audit_mode", "development")
score_label  = result.get("score_label", "")

# Compute rating
from backend.rating_service import compute_readiness_rating
rating = compute_readiness_rating(results_list, float(score_data.get("score", 0)), audit_mode)
print(f"Grade: {rating['grade']} — {rating['label']} ({rating['overall_score']:.1f}%)")

from backend.report_generator import generate_compliance_matrix_pdf, generate_audit_summary_pdf

# Compliance Matrix
buf = generate_compliance_matrix_pdf(
    results=results_list,
    score_data={**score_data, "score_label": score_label},
    audit_mode=audit_mode,
    project_name="Pacific Biochar",
    rating=rating,
)
out1 = os.path.join(os.path.dirname(__file__), 'pdf_rating_matrix.pdf')
with open(out1, 'wb') as f:
    f.write(buf)
print(f"Compliance Matrix: {out1} ({len(buf)//1024} KB)")

# Summary
buf2 = generate_audit_summary_pdf(
    results=results_list,
    score_data={**score_data, "score_label": score_label},
    audit_mode=audit_mode,
    project_name="Pacific Biochar",
    rating=rating,
)
out2 = os.path.join(os.path.dirname(__file__), 'pdf_rating_summary.pdf')
with open(out2, 'wb') as f:
    f.write(buf2)
print(f"Summary PDF: {out2} ({len(buf2)//1024} KB)")
