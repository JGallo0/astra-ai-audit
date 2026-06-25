import sys, os, json, re
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.stdout.reconfigure(encoding='utf-8')

from backend.viabilidade_engine import PremissasViabilidade, calcular_viabilidade
from backend.viabilidade_service import generate_viabilidade_excel

# Premissas com OPEX explícito
p = PremissasViabilidade(
    moeda_projeto='BRL',
    feedstock_t_ano=5000,
    yield_pirolise=0.28,
    fator_carbono=2.72,
    preco_credito_usd=120.0,
    fx_rate=5.70,
    preco_biochar=0.0,
    capex_total=5_500_000.0,
    opex_anual=1_800_000.0,
    wacc=0.12,
    aliquota_efetiva_ir=0.20,
    horizonte_anos=20,
    ano_investimento=2026,
)

resultado = calcular_viabilidade(p)
print(f"IRR: {resultado['irr']}%")
print(f"NPV: R$ {resultado['npv']:,.0f}")
print(f"OPEX yr1 no resultado: R$ {resultado['opex_yr1']:,.0f}")
print(f"EBITDA yr1: R$ {resultado['ebitda_yr1']:,.0f}")
print(f"Adicionalidade: {resultado['adicionalidade_financeira']}")
print(f"IRR sem carbono: {resultado['irr_sem_carbono']}%")

import dataclasses
premissas_dict = dataclasses.asdict(p)

buf = generate_viabilidade_excel(premissas_dict, resultado, "Projeto Teste OPEX")
out = os.path.join(os.path.dirname(__file__), 'test_excel_opex.xlsx')
with open(out, 'wb') as f:
    f.write(buf)
print(f"\nExcel gerado: {out} ({len(buf)//1024} KB)")
print("Verifique aba 'DRE + Fluxo de Caixa' — deve mostrar OPEX deduzido por ano")
