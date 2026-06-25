import sys, os, dataclasses
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.stdout.reconfigure(encoding='utf-8')
from backend.viabilidade_engine import PremissasViabilidade, calcular_viabilidade
from backend.viabilidade_service import generate_financial_memo_pdf

p = PremissasViabilidade(
    feedstock_t_ano=5000, opex_anual=1734700, capex_total=5498000,
    preco_credito_usd=120, fx_rate=5.70, wacc=0.12,
    issuance_delay_months=6, buffer_pool_pct=0.02,
    rampup_ano1=0.6, rampup_ano2=0.8,
    financiamento_pct=0.60, taxa_juros=0.11, prazo_financiamento=12,
)
r = calcular_viabilidade(p)
premissas_dict = dataclasses.asdict(p)
premissas_dict['metodologia'] = 'Isometric Biochar v1.2'

buf = generate_financial_memo_pdf(premissas_dict, r, "Nova Esperança Biochar")
out = os.path.join(os.path.dirname(__file__), 'memo_test.pdf')
with open(out, 'wb') as f: f.write(buf)
print(f"Memo gerado: {out} ({len(buf)//1024} KB)")
print(f"IRR projeto: {r['irr']}% | IRR equity: {r['irr_equity']}%")
