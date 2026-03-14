# isometric_requirements.py

ISOMETRIC_REQUIREMENTS = [
    {
        "id": "PROJECT_001",
        "module": "Project Eligibility",
        "title": "Project activity eligibility",
        "description": (
            "Verificar se a atividade do projeto é elegível dentro do escopo da metodologia "
            "e se a descrição do sistema, fronteira e atividade principal está suficientemente clara."
        ),
        "keywords_project": [
            "project description", "project activity", "biochar project", "system boundary",
            "technology", "pyrolysis reactor", "Nova Esperança", "descrição do projeto",
            "fronteira do projeto", "atividade do projeto"
        ],
        "keywords_methodology": [
            "project eligibility", "eligible activity", "system boundary", "project boundary"
        ],
        "severity": "high",
        "expected_documents": ["PDD", "Project Description", "Annexes"]
    },
    {
        "id": "FEEDSTOCK_001",
        "module": "Feedstock",
        "title": "Feedstock eligibility",
        "description": (
            "Verificar se a biomassa utilizada é elegível segundo a metodologia e se não viola "
            "restrições de origem, sustentabilidade ou uso proibido."
        ),
        "keywords_project": [
            "feedstock", "biomassa", "origem da biomassa", "sustentabilidade",
            "eucalyptus residues", "forest residues", "resíduo florestal",
            "cadeia de custódia", "residual biomass", "waste biomass"
        ],
        "keywords_methodology": [
            "eligible feedstock", "feedstock eligibility", "sustainable sourcing",
            "waste biomass", "residues", "feedstock restrictions"
        ],
        "severity": "high",
        "expected_documents": ["PDD", "Feedstock Dossier", "Annexes", "Supply Docs"]
    },
    {
        "id": "FEEDSTOCK_002",
        "module": "Feedstock",
        "title": "Sustainable sourcing and evidence of origin",
        "description": (
            "Verificar se há documentação robusta que comprove a origem da biomassa e a sua "
            "condição de resíduo ou subproduto elegível."
        ),
        "keywords_project": [
            "origin of biomass", "proof of origin", "supplier", "forest management",
            "harvest residues", "documentação da biomassa", "origem da biomassa",
            "cadeia de fornecimento", "resíduo de colheita"
        ],
        "keywords_methodology": [
            "proof of origin", "sustainable sourcing", "chain of custody", "evidence of feedstock origin"
        ],
        "severity": "high",
        "expected_documents": ["Biomass Dossier", "Declarations", "PDD", "Annexes"]
    },
    {
        "id": "ADDITIONALITY_001",
        "module": "Additionality",
        "title": "Project additionality",
        "description": (
            "Verificar se o projeto demonstra adicionalidade regulatória, financeira e/ou de "
            "prática comum, conforme aplicável."
        ),
        "keywords_project": [
            "additionality", "adicionalidade", "investment analysis",
            "financial analysis", "common practice", "barrier analysis",
            "IRR", "NPV", "VPL", "TIR", "business as usual"
        ],
        "keywords_methodology": [
            "additionality", "financial additionality", "barrier analysis",
            "common practice", "regulatory surplus"
        ],
        "severity": "high",
        "expected_documents": ["PDD", "Financial Model", "Additionality Memo"]
    },
    {
        "id": "BASELINE_001",
        "module": "Baseline",
        "title": "Baseline and counterfactual scenario",
        "description": (
            "Verificar se o cenário de linha de base e o contrafactual estão claramente definidos, "
            "justificados e coerentes com a metodologia."
        ),
        "keywords_project": [
            "baseline", "counterfactual", "business as usual", "without project",
            "linha de base", "cenário sem projeto", "contrafactual"
        ],
        "keywords_methodology": [
            "baseline scenario", "counterfactual", "without-project scenario"
        ],
        "severity": "high",
        "expected_documents": ["PDD", "Baseline Memo", "Financial Model"]
    },
    {
        "id": "PROCESS_001",
        "module": "Process",
        "title": "Eligible conversion process",
        "description": (
            "Verificar se o processo de conversão termoquímica descrito é elegível e se a operação "
            "do sistema está adequadamente documentada."
        ),
        "keywords_project": [
            "pyrolysis", "reactor", "process description", "operating conditions",
            "combustion of gases", "temperature", "residence time",
            "pirólise", "reator", "condições operacionais"
        ],
        "keywords_methodology": [
            "eligible process", "pyrolysis", "thermochemical conversion", "process requirements"
        ],
        "severity": "high",
        "expected_documents": ["PDD", "Technical Specs", "SOP", "Process Description"]
    },
    {
        "id": "BIOCHAR_001",
        "module": "Biochar Quality",
        "title": "Biochar characterization and quality evidence",
        "description": (
            "Verificar se há caracterização laboratorial do biochar e se os parâmetros críticos "
            "exigidos pela metodologia estão demonstrados."
        ),
        "keywords_project": [
            "biochar analysis", "laboratory report", "fixed carbon", "H/C", "ash",
            "carbon content", "lab results", "análise laboratorial", "carbono fixo",
            "relação H/C", "qualidade do biochar"
        ],
        "keywords_methodology": [
            "biochar characterization", "quality requirements", "H/Corg", "fixed carbon", "lab testing"
        ],
        "severity": "high",
        "expected_documents": ["Lab Report", "PDD", "Annexes"]
    },
    {
        "id": "DURABILITY_001",
        "module": "Durability",
        "title": "Durability / permanence of carbon storage",
        "description": (
            "Verificar se o projeto demonstra durabilidade da remoção com base nas exigências "
            "metodológicas e nos parâmetros do biochar."
        ),
        "keywords_project": [
            "durability", "permanence", "H/C", "biochar stability", "stability",
            "durabilidade", "permanência", "estabilidade do biochar"
        ],
        "keywords_methodology": [
            "durability", "permanence", "biochar stability", "long-term storage", "H/Corg"
        ],
        "severity": "high",
        "expected_documents": ["PDD", "Lab Report", "Durability Memo"]
    },
    {
        "id": "STORAGE_001",
        "module": "Storage/End Use",
        "title": "Eligible storage pathway or end use",
        "description": (
            "Verificar se o destino final do biochar é elegível e se existem evidências sobre "
            "armazenamento, aplicação ou uso final conforme a metodologia aplicável."
        ),
        "keywords_project": [
            "soil application", "built environment", "storage pathway", "end use",
            "destino do biochar", "aplicação em solo", "uso final", "armazenamento"
        ],
        "keywords_methodology": [
            "storage pathway", "end use", "eligible storage", "soil storage", "built environment"
        ],
        "severity": "high",
        "expected_documents": ["PDD", "Offtake Docs", "Application Plan", "Annexes"]
    },
    {
        "id": "LCA_001",
        "module": "LCA",
        "title": "Net removal quantification / LCA consistency",
        "description": (
            "Verificar se a quantificação de remoção líquida está suportada por LCA consistente, "
            "transparente e aderente à metodologia."
        ),
        "keywords_project": [
            "LCA", "life cycle assessment", "net removals", "project emissions",
            "scope 1", "scope 2", "scope 3", "remoção líquida", "ACV"
        ],
        "keywords_methodology": [
            "life cycle assessment", "net removal", "project emissions", "quantification"
        ],
        "severity": "high",
        "expected_documents": ["LCA", "PDD", "Quantification Annex"]
    },
    {
        "id": "LEAKAGE_001",
        "module": "Leakage",
        "title": "Leakage assessment",
        "description": (
            "Verificar se potenciais emissões de leakage foram avaliadas e tratadas de forma "
            "consistente com a metodologia."
        ),
        "keywords_project": [
            "leakage", "emissions leakage", "market leakage", "activity shifting",
            "vazamento", "deslocamento de atividade"
        ],
        "keywords_methodology": [
            "leakage", "activity shifting", "market leakage"
        ],
        "severity": "medium",
        "expected_documents": ["PDD", "LCA", "Leakage Memo"]
    },
    {
        "id": "MRV_001",
        "module": "MRV",
        "title": "Monitoring, reporting and verification plan",
        "description": (
            "Verificar se existe plano de MRV robusto com parâmetros, frequência, instrumentos, "
            "QA/QC e rastreabilidade."
        ),
        "keywords_project": [
            "MRV", "monitoring plan", "reporting", "verification", "rastreabilidade",
            "QA/QC", "sampling", "frequency", "monitoramento", "plano de monitoramento"
        ],
        "keywords_methodology": [
            "MRV", "monitoring", "verification", "quality assurance", "sampling frequency"
        ],
        "severity": "high",
        "expected_documents": ["MRV Plan", "PDD", "SOP", "Monitoring Annex"]
    },
    {
        "id": "MRV_002",
        "module": "MRV",
        "title": "Calibration and measurement controls",
        "description": (
            "Verificar se o projeto define controles de medição, calibração, manutenção e "
            "integridade dos dados."
        ),
        "keywords_project": [
            "calibration", "measurement equipment", "scale", "weighing", "sensor",
            "maintenance", "instrument calibration", "calibração", "balança", "sensor"
        ],
        "keywords_methodology": [
            "calibration", "measurement controls", "instrument accuracy", "quality assurance"
        ],
        "severity": "high",
        "expected_documents": ["MRV Plan", "QAQC", "SOP"]
    },
    {
        "id": "TRACEABILITY_001",
        "module": "Traceability",
        "title": "Batch traceability and chain of custody",
        "description": (
            "Verificar se há rastreabilidade por lote da biomassa ao biochar e ao destino final."
        ),
        "keywords_project": [
            "batch", "lot", "traceability", "chain of custody", "lote",
            "rastreabilidade", "batch records", "inventory"
        ],
        "keywords_methodology": [
            "traceability", "chain of custody", "batch records", "record keeping"
        ],
        "severity": "high",
        "expected_documents": ["MRV", "PDD", "Batch Records", "SOP"]
    },
    {
        "id": "DATA_001",
        "module": "Data & Evidence",
        "title": "Record keeping and evidence retention",
        "description": (
            "Verificar se o projeto possui estratégia de retenção documental e registros "
            "suficientes para auditoria e verificação."
        ),
        "keywords_project": [
            "record retention", "document retention", "evidence", "audit trail",
            "registros", "retenção documental", "evidências"
        ],
        "keywords_methodology": [
            "record keeping", "evidence retention", "documentation requirements"
        ],
        "severity": "medium",
        "expected_documents": ["PDD", "MRV", "QAQC", "Annexes"]
    },
]