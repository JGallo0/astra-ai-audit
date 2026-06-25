import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.stdout.reconfigure(encoding='utf-8')

from backend.report_generator import generate_readiness_certificate_pdf

# Simula B+ para verificar o encaixe
for grade in ["A+", "A", "B+", "B", "C"]:
    rating = {
        "grade": grade, "label": "Prontidão Sólida",
        "description": "O projeto apresenta boa aderência ao protocolo.",
        "overall_score": 74.5, "audit_mode": "development", "phase": "PDD Audit",
        "dimensions": {
            "carbon":       {"score": 80, "na_count": 0},
            "additionality":{"score": 70, "na_count": 1},
            "permanence":   {"score": 75, "na_count": 2},
            "safeguards":   {"score": 72, "na_count": 0},
            "integrity":    {"score": 78, "na_count": 0},
        }
    }
    buf = generate_readiness_certificate_pdf(rating, "Projeto Teste", "Isometric Biochar v1.2")
    out = os.path.join(os.path.dirname(__file__), f'cert_grade_{grade.replace("+","plus")}.pdf')
    with open(out, 'wb') as f:
        f.write(buf)
    print(f"Grade {grade}: {out} ({len(buf)//1024} KB)")
