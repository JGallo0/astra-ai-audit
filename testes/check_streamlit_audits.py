import psycopg2, psycopg2.extras, json

conn = psycopg2.connect(
    host='aws-1-us-east-1.pooler.supabase.com', dbname='postgres',
    user='postgres.frspdiilcstqtytmjgbe', password='@CarbonAuditor2026', port=5432,
    cursor_factory=psycopg2.extras.RealDictCursor
)
cur = conn.cursor()

# Todos os audit_outputs disponíveis
cur.execute("""
    SELECT ao.project_id, p.project_name, ao.output_type, ao.created_at,
           LEFT(ao.content, 600) as preview
    FROM audit_outputs ao
    JOIN projects p ON ao.project_id::text = p.id::text
    ORDER BY ao.created_at DESC
    LIMIT 20
""")
rows = cur.fetchall()
print(f"=== {len(rows)} auditorias salvas no Streamlit ===")
for r in rows:
    print(f"\nProjeto: {r['project_name']} | Tipo: {r['output_type']} | Data: {r['created_at']}")
    print(r['preview'][:400])
    print("---")

conn.close()
