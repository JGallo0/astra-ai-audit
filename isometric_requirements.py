ISOMETRIC_REQUIREMENTS = [
    {
        "id": "ELIG_001",
        "module": "Eligibility",
        "title": "Project activity clearly defined",
        "description": (
            "The project documentation must clearly define the project activity, including "
            "feedstock conversion into biochar, intended storage or end use pathway, project "
            "boundary, operational flow, participating entities, and implementation context."
        ),
        "rationale": (
            "A clearly defined project activity is necessary to determine whether the project "
            "fits the methodology scope and whether subsequent claims, monitoring and carbon "
            "accounting are traceable and auditable."
        ),
        "keywords": [
            "project description",
            "project activity",
            "project boundary",
            "implementation",
            "facility description",
            "process description",
            "biochar production",
            "storage pathway",
            "end use"
        ],
    },
    {
        "id": "ELIG_002",
        "module": "Eligibility",
        "title": "Project location and ownership identified",
        "description": (
            "The project documentation must identify where the project is implemented and "
            "which entity owns or controls the project activity, site, equipment, and relevant "
            "operational decisions."
        ),
        "rationale": (
            "Location and control are necessary to establish accountability, rights to operate, "
            "and auditability of the carbon removal activity."
        ),
        "keywords": [
            "project location",
            "site",
            "ownership",
            "operator",
            "legal entity",
            "project participant",
            "control of activity",
            "project proponent"
        ],
    },
    {
        "id": "ELIG_003",
        "module": "Eligibility",
        "title": "Project start date and crediting context documented",
        "description": (
            "The project must document start date, implementation timeline, operational status, "
            "and the relevant certification or crediting context under which carbon removal is claimed."
        ),
        "rationale": (
            "A documented timeline is necessary to assess eligibility, additionality, data relevance, "
            "and the applicable period for monitoring and issuance."
        ),
        "keywords": [
            "start date",
            "implementation timeline",
            "commissioning",
            "operational status",
            "crediting period",
            "project timeline",
            "monitoring period"
        ],
    },
    {
        "id": "FEED_001",
        "module": "Feedstock",
        "title": "Eligible feedstock type identified",
        "description": (
            "The project must identify the type of biomass feedstock used and demonstrate that "
            "it is eligible under the methodology and not derived from prohibited sources."
        ),
        "rationale": (
            "Feedstock eligibility is fundamental because the permanence, baseline, sustainability, "
            "and emissions profile of the project depend on what biomass enters the system."
        ),
        "keywords": [
            "feedstock",
            "biomass type",
            "residue",
            "eligible biomass",
            "source material",
            "eucalyptus residue",
            "wood residue",
            "agricultural residue"
        ],
    },
    {
        "id": "FEED_002",
        "module": "Feedstock",
        "title": "Feedstock origin documented",
        "description": (
            "The documentation must describe the geographic and operational origin of the biomass, "
            "including suppliers, sites, properties, forestry units, farms, or industrial origin."
        ),
        "rationale": (
            "Origin documentation is required to evaluate traceability, double counting risk, "
            "land-use risk, and sustainability claims."
        ),
        "keywords": [
            "feedstock origin",
            "supplier",
            "source farm",
            "forest unit",
            "horto",
            "property",
            "origin of biomass",
            "traceability of biomass"
        ],
    },
    {
        "id": "FEED_003",
        "module": "Feedstock",
        "title": "Feedstock counterfactual fate described",
        "description": (
            "The project must describe what would likely happen to the feedstock in the absence "
            "of the project, such as decay, burning, mulching, industrial use, soil return, or disposal."
        ),
        "rationale": (
            "The baseline and net carbon removal depend materially on the counterfactual treatment "
            "of the feedstock if the project were not implemented."
        ),
        "keywords": [
            "counterfactual",
            "baseline fate",
            "without project",
            "business as usual",
            "decay",
            "burning",
            "mulching",
            "alternative use",
            "residue fate"
        ],
    },
    {
        "id": "FEED_004",
        "module": "Feedstock",
        "title": "Feedstock sustainability safeguards documented",
        "description": (
            "The project should document safeguards showing the feedstock is sourced in a manner "
            "consistent with sustainability claims, including residue status, harvesting context, "
            "land-use considerations, and risk controls."
        ),
        "rationale": (
            "Unsustainable sourcing can invalidate carbon removal claims by introducing leakage, "
            "land-use change risk, or reputational and methodological concerns."
        ),
        "keywords": [
            "sustainability",
            "sustainable biomass",
            "residue status",
            "land use",
            "forest management",
            "harvest residue",
            "safeguards",
            "no deforestation",
            "feedstock eligibility"
        ],
    },
    {
        "id": "FEED_005",
        "module": "Feedstock",
        "title": "Feedstock traceability system defined",
        "description": (
            "The project must describe how feedstock is tracked from origin through receipt, storage, "
            "processing, and conversion, including documentation and batch-level controls where applicable."
        ),
        "rationale": (
            "Traceability is required to ensure that only eligible biomass contributes to issued removals "
            "and that data can be verified by an auditor."
        ),
        "keywords": [
            "traceability",
            "chain of custody",
            "feedstock tracking",
            "batch",
            "supplier records",
            "delivery note",
            "weighbridge",
            "material receipt"
        ],
    },
    {
        "id": "TECH_001",
        "module": "Technology",
        "title": "Pyrolysis technology described",
        "description": (
            "The project must describe the pyrolysis technology or reactor system, including type, "
            "operating principle, material flow, thermal profile, gas handling and process configuration."
        ),
        "rationale": (
            "Technology description is necessary to assess whether the project activity is within scope "
            "and whether process emissions, yields and biochar quality can be robustly monitored."
        ),
        "keywords": [
            "pyrolysis reactor",
            "technology description",
            "reactor type",
            "continuous pyrolysis",
            "process flow",
            "gas handling",
            "thermal process",
            "equipment specification"
        ],
    },
    {
        "id": "TECH_002",
        "module": "Technology",
        "title": "Operational parameters and control strategy documented",
        "description": (
            "The project should document key operating parameters such as temperature range, residence time, "
            "moisture management, throughput, and process control logic relevant to biochar formation."
        ),
        "rationale": (
            "Operational controls are central to product consistency, carbon permanence, emissions performance "
            "and defensibility of production data."
        ),
        "keywords": [
            "temperature",
            "residence time",
            "throughput",
            "moisture",
            "operating parameters",
            "process control",
            "SCADA",
            "PLC",
            "monitoring"
        ],
    },
    {
        "id": "TECH_003",
        "module": "Technology",
        "title": "Non-condensable gases and process emissions handling documented",
        "description": (
            "The project must explain how syngas, off-gases, particulates and other relevant process emissions "
            "are managed, combusted, treated or released."
        ),
        "rationale": (
            "Gas handling and emissions treatment materially affect project emissions, local compliance, "
            "safety and net carbon removal calculations."
        ),
        "keywords": [
            "syngas",
            "off-gas",
            "flare",
            "burner",
            "combustion chamber",
            "process emissions",
            "particulates",
            "air emissions",
            "gas handling"
        ],
    },
    {
        "id": "TECH_004",
        "module": "Technology",
        "title": "Mass balance approach documented",
        "description": (
            "The project should document how biomass input, process losses, co-products and biochar output "
            "are quantified in a coherent mass balance framework."
        ),
        "rationale": (
            "A defensible mass balance is essential for carbon accounting and for validating production claims."
        ),
        "keywords": [
            "mass balance",
            "input biomass",
            "biochar output",
            "yield",
            "process loss",
            "co-products",
            "conversion efficiency",
            "material balance"
        ],
    },
    {
        "id": "BIOCHAR_001",
        "module": "Biochar Quality",
        "title": "Biochar specification and characterization documented",
        "description": (
            "The project must document the properties of the biochar produced, including carbon content and "
            "other relevant laboratory or product quality parameters required by the methodology."
        ),
        "rationale": (
            "Carbon removal claims depend on the quantity and stability-relevant quality of the biochar."
        ),
        "keywords": [
            "biochar quality",
            "laboratory analysis",
            "fixed carbon",
            "carbon content",
            "ash",
            "volatile matter",
            "moisture",
            "product specification"
        ],
    },
    {
        "id": "BIOCHAR_002",
        "module": "Biochar Quality",
        "title": "Biochar stability or permanence proxy documented",
        "description": (
            "The project must present the parameter or test used to demonstrate long-term carbon stability, "
            "such as H/Corg or another methodology-accepted permanence proxy."
        ),
        "rationale": (
            "The permanence of stored carbon is one of the core determinants of removals eligibility."
        ),
        "keywords": [
            "H/Corg",
            "hydrogen to carbon ratio",
            "permanence",
            "stability",
            "biochar permanence",
            "durability",
            "recalcitrance"
        ],
    },
    {
        "id": "BIOCHAR_003",
        "module": "Biochar Quality",
        "title": "Sampling and laboratory protocol documented",
        "description": (
            "The project should explain how biochar samples are collected, preserved, sent to laboratory, "
            "tested, and linked to specific production batches or periods."
        ),
        "rationale": (
            "Sampling quality directly affects the credibility of test results used in carbon accounting."
        ),
        "keywords": [
            "sampling plan",
            "laboratory protocol",
            "sample collection",
            "chain of custody",
            "batch sample",
            "quality assurance",
            "QAQC"
        ],
    },
    {
        "id": "BIOCHAR_004",
        "module": "Biochar Quality",
        "title": "Batch-to-quality linkage documented",
        "description": (
            "The project should demonstrate how biochar quality results are linked to production lots, batches, "
            "or monitoring periods relevant to crediting."
        ),
        "rationale": (
            "Without a defensible linkage between lab results and production records, carbon claims may not be auditable."
        ),
        "keywords": [
            "batch linkage",
            "production lot",
            "quality by batch",
            "lab result linkage",
            "traceability of product",
            "batch records"
        ],
    },
    {
        "id": "STOR_001",
        "module": "Storage/End Use",
        "title": "Storage or end-use pathway identified",
        "description": (
            "The project must clearly identify where and how the biochar will be stored or used in a way that "
            "meets methodology requirements for durable carbon storage."
        ),
        "rationale": (
            "Carbon removal only occurs if the produced biochar is directed to an eligible storage or use pathway."
        ),
        "keywords": [
            "end use",
            "storage pathway",
            "soil application",
            "built environment",
            "durable storage",
            "biochar destination",
            "application pathway"
        ],
    },
    {
        "id": "STOR_002",
        "module": "Storage/End Use",
        "title": "Controls against reversal or ineligible use documented",
        "description": (
            "The project should describe the controls used to prevent biochar from being diverted to ineligible uses "
            "or from experiencing conditions that would undermine claimed permanence."
        ),
        "rationale": (
            "Durable carbon storage claims require confidence that the product is not misused or later reversed."
        ),
        "keywords": [
            "reversal risk",
            "ineligible use",
            "storage control",
            "end-use control",
            "chain of custody",
            "delivery confirmation",
            "application evidence"
        ],
    },
    {
        "id": "STOR_003",
        "module": "Storage/End Use",
        "title": "Evidence of transfer, delivery or application documented",
        "description": (
            "The project should maintain evidence showing transfer of custody, delivery, sale, storage, or application "
            "of the biochar to the eligible destination."
        ),
        "rationale": (
            "Evidence of destination is necessary to support the claim that carbon has actually entered the qualifying storage pathway."
        ),
        "keywords": [
            "invoice",
            "delivery note",
            "application record",
            "offtake",
            "customer record",
            "storage confirmation",
            "transfer of custody"
        ],
    },
    {
        "id": "LCA_001",
        "module": "LCA",
        "title": "Life cycle assessment approach documented",
        "description": (
            "The project must describe the life cycle accounting approach used to estimate project emissions, "
            "including boundaries, relevant processes, assumptions and sources."
        ),
        "rationale": (
            "Net removals depend on a transparent and auditable accounting of project emissions across the relevant system boundary."
        ),
        "keywords": [
            "LCA",
            "life cycle assessment",
            "boundary",
            "system boundary",
            "assumptions",
            "emissions accounting",
            "net removal"
        ],
    },
    {
        "id": "LCA_002",
        "module": "LCA",
        "title": "Emission sources and sinks included",
        "description": (
            "The LCA or equivalent emissions accounting should identify all material sources and sinks relevant to "
            "the methodology, including feedstock handling, transport, energy use, process emissions, and storage effects."
        ),
        "rationale": (
            "Incomplete emissions accounting may overstate net carbon removal."
        ),
        "keywords": [
            "emission sources",
            "transport emissions",
            "diesel",
            "electricity",
            "process emissions",
            "feedstock handling",
            "storage emissions",
            "system boundary"
        ],
    },
    {
        "id": "LCA_003",
        "module": "LCA",
        "title": "Input data sources and emission factors documented",
        "description": (
            "The project should document the activity data sources, conversion factors, laboratory inputs and "
            "emission factors used in life cycle calculations."
        ),
        "rationale": (
            "Auditable data provenance is required to support reproducibility and verification of net removal estimates."
        ),
        "keywords": [
            "emission factor",
            "input data",
            "data source",
            "activity data",
            "assumption",
            "calculation parameter",
            "inventory"
        ],
    },
    {
        "id": "LCA_004",
        "module": "LCA",
        "title": "Net removal calculation logic documented",
        "description": (
            "The documentation should explain how gross carbon stored is translated into net carbon removed after "
            "accounting for relevant deductions, emissions, leakage or uncertainty adjustments."
        ),
        "rationale": (
            "The credibility of issued removals depends on transparent conversion from gross storage to net removals."
        ),
        "keywords": [
            "net removal",
            "gross removal",
            "deduction",
            "calculation logic",
            "leakage",
            "uncertainty",
            "credit calculation"
        ],
    },
    {
        "id": "MRV_001",
        "module": "MRV",
        "title": "Monitoring plan documented",
        "description": (
            "The project must document a monitoring plan that defines what data are measured, at what frequency, "
            "using which equipment, by whom, and under what QA/QC controls."
        ),
        "rationale": (
            "A monitoring plan is necessary for consistent data generation and auditability of carbon removal claims."
        ),
        "keywords": [
            "monitoring plan",
            "measurement frequency",
            "SOP",
            "QAQC",
            "quality control",
            "sensor",
            "monitoring protocol"
        ],
    },
    {
        "id": "MRV_002",
        "module": "MRV",
        "title": "Measurement equipment and calibration documented",
        "description": (
            "The project should describe the equipment used for weighing, temperature monitoring, sampling or other "
            "material measurements, including calibration or verification routines."
        ),
        "rationale": (
            "Reliable instrumentation is essential to generate verifiable project data."
        ),
        "keywords": [
            "calibration",
            "weighbridge",
            "scale",
            "temperature sensor",
            "instrument",
            "measurement device",
            "monitoring equipment"
        ],
    },
    {
        "id": "MRV_003",
        "module": "MRV",
        "title": "Data management and record retention documented",
        "description": (
            "The project should define how operational, quality and traceability records are stored, versioned, "
            "protected, and retained for audit purposes."
        ),
        "rationale": (
            "Data governance affects the integrity and availability of evidence required for verification."
        ),
        "keywords": [
            "data management",
            "record retention",
            "database",
            "MRV system",
            "data integrity",
            "audit trail",
            "version control"
        ],
    },
    {
        "id": "MRV_004",
        "module": "MRV",
        "title": "Quality assurance and quality control procedures documented",
        "description": (
            "The project should describe QA/QC procedures for measurements, calculations, document control, sample handling "
            "and reconciliation of inconsistencies."
        ),
        "rationale": (
            "QA/QC procedures reduce error risk and support confidence in the resulting carbon accounting."
        ),
        "keywords": [
            "QAQC",
            "quality assurance",
            "quality control",
            "verification",
            "cross-check",
            "reconciliation",
            "data validation"
        ],
    },
    {
        "id": "TRACE_001",
        "module": "Traceability",
        "title": "Unique batch or lot identification system documented",
        "description": (
            "The project should identify how feedstock, production lots, quality samples and final biochar batches "
            "are uniquely identified and linked."
        ),
        "rationale": (
            "Batch-level linkage is central to proving that the credited output corresponds to eligible inputs and verified quality."
        ),
        "keywords": [
            "batch ID",
            "lot ID",
            "production batch",
            "traceability code",
            "chain of custody",
            "batch linkage"
        ],
    },
    {
        "id": "TRACE_002",
        "module": "Traceability",
        "title": "Input-to-output reconciliation documented",
        "description": (
            "The project should demonstrate how biomass receipts, processing records, production output, laboratory results "
            "and end-use evidence are reconciled within one traceable system."
        ),
        "rationale": (
            "Traceable reconciliation helps ensure the removals claim is grounded in one coherent evidentiary chain."
        ),
        "keywords": [
            "reconciliation",
            "input output linkage",
            "mass balance",
            "batch reconciliation",
            "inventory control",
            "production records"
        ],
    },
    {
        "id": "TRACE_003",
        "module": "Traceability",
        "title": "Documentation for external verification available",
        "description": (
            "The project should maintain records in a format that can be reviewed by a third-party verifier, including "
            "supporting documents, logs, source records and explanatory metadata."
        ),
        "rationale": (
            "Even strong operational systems may fail audit if evidence cannot be retrieved and interpreted externally."
        ),
        "keywords": [
            "audit package",
            "verification evidence",
            "supporting documents",
            "source records",
            "third-party verification",
            "documentation package"
        ],
    },
]
