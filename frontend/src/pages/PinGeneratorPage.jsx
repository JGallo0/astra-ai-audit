import { useState, useCallback } from "react";
import { useNavigate } from "react-router-dom";

const API = import.meta.env.VITE_API_BASE || "";

// ── Paleta ────────────────────────────────────────────────────────────────────
const GRADE_COLOR = {
  "A+": "#16a34a", A: "#22c55e", "B+": "#65a30d",
  B: "#ca8a04", C: "#dc2626",
};
const METHOD_COLOR = {
  isometric: "#1e40af", puro_earth: "#7c3aed", verra_vcs: "#0369a1",
};
const METHOD_LABEL = {
  isometric: "Isometric Biochar v1.2",
  puro_earth: "Puro.Earth Edition 2025",
  verra_vcs: "Verra VCS VM0044",
};
const DIM_LABEL = {
  feedstock_eligibility: "Elegibilidade do Feedstock",
  carbon_accounting:     "Contabilidade de Carbono",
  additionality:         "Adicionalidade",
  permanence:            "Permanência",
  monitoring:            "Monitoramento",
  environmental_social:  "Ambiental & Social",
};

// ── Definição dos passos ──────────────────────────────────────────────────────
const STEPS = [
  { id: "projeto",       label: "Projeto",        icon: "🏭" },
  { id: "feedstock",     label: "Feedstock",      icon: "🌿" },
  { id: "producao",      label: "Produção",        icon: "🔥" },
  { id: "biochar",       label: "Biochar",         icon: "⚗️" },
  { id: "carbono",       label: "Carbono",         icon: "📊" },
  { id: "adicionalidade",label: "Adicionalidade",  icon: "✅" },
  { id: "monitoramento", label: "Monitoramento",   icon: "📡" },
  { id: "social",        label: "Social & Ambiental", icon: "🤝" },
];

// ── Helpers de formulário ──────────────────────────────────────────────────────
function Field({ label, help, children, required }) {
  return (
    <div style={{ marginBottom: 18 }}>
      <label style={{ display: "block", fontWeight: 600, fontSize: 13, marginBottom: 4, color: "#1e293b" }}>
        {label}{required && <span style={{ color: "#dc2626", marginLeft: 3 }}>*</span>}
      </label>
      {help && <p style={{ fontSize: 11, color: "#64748b", margin: "0 0 6px" }}>{help}</p>}
      {children}
    </div>
  );
}

const inp = {
  width: "100%", boxSizing: "border-box", padding: "8px 10px", border: "1px solid #cbd5e1",
  borderRadius: 6, fontSize: 13, background: "#fff", color: "#1e293b",
  outline: "none", fontFamily: "inherit",
};

function TextInput({ name, value, onChange, placeholder, type = "text" }) {
  return (
    <input
      style={inp} type={type} name={name} value={value ?? ""}
      placeholder={placeholder}
      onChange={e => onChange(name, type === "number" ? (e.target.value === "" ? null : Number(e.target.value)) : e.target.value)}
    />
  );
}

function SelectInput({ name, value, onChange, options }) {
  return (
    <select style={inp} name={name} value={value ?? ""}
      onChange={e => onChange(name, e.target.value)}>
      <option value="">— Selecione —</option>
      {options.map(o => (
        <option key={o.value} value={o.value}>{o.label}</option>
      ))}
    </select>
  );
}

function Toggle({ name, value, onChange, label }) {
  return (
    <label style={{ display: "flex", alignItems: "center", gap: 10, cursor: "pointer", userSelect: "none" }}>
      <div
        onClick={() => onChange(name, !value)}
        style={{
          width: 40, height: 22, borderRadius: 11, background: value ? "#1e40af" : "#cbd5e1",
          position: "relative", transition: "background .2s", flexShrink: 0,
        }}
      >
        <div style={{
          position: "absolute", top: 3, left: value ? 21 : 3, width: 16, height: 16,
          borderRadius: "50%", background: "#fff", transition: "left .2s",
        }} />
      </div>
      <span style={{ fontSize: 13, color: "#1e293b" }}>{label}</span>
    </label>
  );
}

// ── Componentes por passo ──────────────────────────────────────────────────────

function StepProjeto({ form, set }) {
  return (
    <>
      <Field label="Nome do projeto" required>
        <TextInput name="project_name" value={form.project_name} onChange={set} placeholder="Ex: Biochar Norte MG" />
      </Field>
      <Field label="País" required help="Afeta o CPI (índice de percepção de corrupção) — relevante para Puro.Earth.">
        <SelectInput name="project_country" value={form.project_country} onChange={set} options={[
          { value: "brazil", label: "Brasil (CPI 36)" },
          { value: "germany", label: "Alemanha (CPI 79)" },
          { value: "usa", label: "EUA (CPI 69)" },
          { value: "india", label: "Índia (CPI 39)" },
          { value: "indonesia", label: "Indonésia (CPI 34)" },
          { value: "chile", label: "Chile (CPI 52)" },
          { value: "bolivia", label: "Bolívia (CPI 27)" },
          { value: "other", label: "Outro" },
        ]} />
      </Field>
      <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: 16 }}>
        <Field label="Produção anual estimada (t biochar seco/ano)" required>
          <TextInput name="biochar_t_dry_year" value={form.biochar_t_dry_year} onChange={set} type="number" placeholder="Ex: 1000" />
        </Field>
        <Field label="Créditos estimados (tCO₂e/ano)" help="Estimativa inicial, pode deixar em branco.">
          <TextInput name="estimated_credits_tco2" value={form.estimated_credits_tco2} onChange={set} type="number" placeholder="Ex: 750" />
        </Field>
      </div>
      <Field label="Via de aplicação" required>
        <SelectInput name="storage_pathway" value={form.storage_pathway} onChange={set} options={[
          { value: "soil", label: "Solo agrícola (mais comum)" },
          { value: "built_environment", label: "Construção civil" },
          { value: "water_filtration", label: "Filtração de água" },
          { value: "other", label: "Outra" },
        ]} />
      </Field>
    </>
  );
}

function StepFeedstock({ form, set }) {
  return (
    <>
      <Field label="Tipo de feedstock" required>
        <SelectInput name="feedstock_type" value={form.feedstock_type} onChange={set} options={[
          { value: "agricultural_residue", label: "Resíduo agrícola (palha, bagaço, casca)" },
          { value: "forest_biomass",       label: "Biomassa florestal (galhos, serragem, podas)" },
          { value: "urban_wood",           label: "Madeira urbana / resíduo de processamento" },
          { value: "food_waste",           label: "Resíduo de processamento alimentar" },
          { value: "sewage_sludge",        label: "Lodo de esgoto (biossólido)" },
          { value: "animal_manure",        label: "Esterco animal" },
          { value: "mixed",               label: "Misto (múltiplos tipos)" },
          { value: "other",               label: "Outro" },
        ]} />
      </Field>

      <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: 16 }}>
        <Toggle name="is_forest_biomass" value={form.is_forest_biomass} onChange={set}
          label="Feedstock de origem florestal?" />
        <Toggle name="is_purpose_grown" value={form.is_purpose_grown} onChange={set}
          label="Cultivado para este fim (não resíduo)?" />
        <Toggle name="feedstock_imported" value={form.feedstock_imported} onChange={set}
          label="Feedstock importado de outro país?" />
        <Toggle name="uses_mixed_waste" value={form.uses_mixed_waste} onChange={set}
          label="Mistura com plásticos / materiais fósseis?" />
        <Toggle name="uses_coal_ash" value={form.uses_coal_ash} onChange={set}
          label="Inclui cinzas de carvão (coal ash)?" />
        <Toggle name="from_land_clearing" value={form.from_land_clearing} onChange={set}
          label="Proveniente de desmatamento / limpeza de terra?" />
      </div>

      {form.is_forest_biomass && (
        <div style={{ marginTop: 20, padding: "14px 16px", background: "#eff6ff", borderRadius: 8, border: "1px solid #bfdbfe" }}>
          <p style={{ fontWeight: 600, fontSize: 13, margin: "0 0 12px", color: "#1e40af" }}>
            🌲 Certificação de sustentabilidade florestal
          </p>
          <p style={{ fontSize: 12, color: "#475569", margin: "0 0 12px" }}>
            Obrigatória para Puro.Earth. Relevante para Verra (PEFC/FSC ou definição CDM de biomassa renovável).
            CPI do Brasil = 36 → plano de manejo governamental não elegível na Puro.Earth (exige CPI ≥ 50).
          </p>
          <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: 12 }}>
            <Toggle name="has_fsc_certification" value={form.has_fsc_certification} onChange={set}
              label="Certificação FSC ativa" />
            <Toggle name="has_pefc_certification" value={form.has_pefc_certification} onChange={set}
              label="Certificação PEFC ativa" />
            <Toggle name="has_isae3000_dossier" value={form.has_isae3000_dossier} onChange={set}
              label="Dossiê auditado ISAE 3000" />
            <Toggle name="has_government_mgmt_plan" value={form.has_government_mgmt_plan} onChange={set}
              label="Plano de manejo governamental" />
          </div>
        </div>
      )}
    </>
  );
}

function StepProducao({ form, set }) {
  return (
    <>
      <Field label="Temperatura média de pirólise (°C)" help="Fator principal da permanência na Verra VCS (Tabela 3). Também informativo para Isometric/Puro.">
        <TextInput name="pyrolysis_temp_c" value={form.pyrolysis_temp_c} onChange={set} type="number" placeholder="Ex: 600 (ou deixe em branco se não souber)" />
      </Field>
      {form.pyrolysis_temp_c && (
        <div style={{ padding: "10px 14px", background: "#f0fdf4", borderRadius: 6, border: "1px solid #bbf7d0", fontSize: 12, color: "#15803d", marginTop: -8, marginBottom: 16 }}>
          {form.pyrolysis_temp_c > 600
            ? `✅ > 600°C → PRde Verra = 0.89 (máxima permanência)`
            : form.pyrolysis_temp_c >= 450
            ? `⚠️ 450–600°C → PRde Verra = 0.80`
            : form.pyrolysis_temp_c >= 350
            ? `⚠️ 350–450°C → PRde Verra = 0.65`
            : `❌ < 350°C → biochar não elegível para créditos`}
        </div>
      )}

      <Field label="Classe tecnológica da instalação">
        <SelectInput name="verra_tech_class" value={form.verra_tech_class} onChange={set} options={[
          { value: "high", label: "Alta tecnologia (controle automatizado, sensores contínuos)" },
          { value: "low",  label: "Baixa tecnologia (fornos simples, sem automação)" },
          { value: "",     label: "Não sei / não definido" },
        ]} />
      </Field>

      <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: 16 }}>
        <Toggle name="has_continuous_temp_monitoring" value={form.has_continuous_temp_monitoring} onChange={set}
          label="Monitoramento contínuo de temperatura?" />
        <Toggle name="has_pyrolysis_gas_recovery" value={form.has_pyrolysis_gas_recovery} onChange={set}
          label="Gases de pirólise recuperados / combustados?" />
        <Toggle name="has_engineering_diagram" value={form.has_engineering_diagram} onChange={set}
          label="Diagrama de engenharia do reator disponível?" />
        <Toggle name="has_maintenance_plan" value={form.has_maintenance_plan} onChange={set}
          label="Plano de manutenção do reator documentado?" />
      </div>

      <Field label="Tipo de reator" style={{ marginTop: 16 }}>
        <TextInput name="reactor_type" value={form.reactor_type} onChange={set} placeholder="Ex: forno retorta, TLUD, kiln rotativo, flash carbonization..." />
      </Field>
    </>
  );
}

function StepBiochar({ form, set }) {
  const hc = form.h_c_ratio;
  const oc = form.o_c_ratio;
  return (
    <>
      <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: 16 }}>
        <Field label="H/Corg (razão molar)" help="< 0.5 obrigatório para Isometric/Puro. ≤ 0.7 para solo na Verra. Determina permanência em Iso/Puro.">
          <TextInput name="h_c_ratio" value={form.h_c_ratio} onChange={set} type="number" placeholder="Ex: 0.28" />
        </Field>
        <Field label="O/Corg (razão molar)" help="< 0.2 obrigatório para Isometric e Puro.">
          <TextInput name="o_c_ratio" value={form.o_c_ratio} onChange={set} type="number" placeholder="Ex: 0.08" />
        </Field>
      </div>

      {(hc !== null && hc !== undefined) && (
        <div style={{ padding: "10px 14px", borderRadius: 6, border: "1px solid", marginBottom: 12, fontSize: 12,
          ...(hc >= 0.5 ? { background: "#fef2f2", borderColor: "#fca5a5", color: "#b91c1c" }
           : hc >= 0.3  ? { background: "#fffbeb", borderColor: "#fde68a", color: "#92400e" }
           :               { background: "#f0fdf4", borderColor: "#bbf7d0", color: "#15803d" }) }}>
          {hc >= 0.5
            ? `❌ H/Corg ${hc} ≥ 0.5 — permanência zero em Isometric e Puro.Earth (hard gate)`
            : hc > 0.7
            ? `⚠️ H/Corg ${hc} > 0.7 — inelegível para aplicação em solo na Verra VCS`
            : `✅ H/Corg ${hc} — dentro dos limites de elegibilidade`}
        </div>
      )}

      <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: 16 }}>
        <Field label="PAH (mg/kg)" help="Limite Isometric/Puro: 12 mg/kg. Limite IBI Premium: 6 mg/kg.">
          <TextInput name="pah_value" value={form.pah_value} onChange={set} type="number" placeholder="Ex: 4.2" />
        </Field>
        <Field label="PCB (mg/kg)" help="Limite: 0.2 mg/kg (Isometric) / 0.5 mg/kg (IBI).">
          <TextInput name="pcb_value" value={form.pcb_value} onChange={set} type="number" placeholder="Ex: 0.05" />
        </Field>
      </div>

      <Field label="Padrão de qualidade aplicável">
        <SelectInput name="quality_standard" value={form.quality_standard} onChange={set} options={[
          { value: "ibi",              label: "IBI Biochar Standard" },
          { value: "ebc",              label: "EBC (European Biochar Certificate)" },
          { value: "local_regulation", label: "Regulação local específica" },
          { value: "not_stated",       label: "Não definido / ainda em análise" },
        ]} />
      </Field>

      <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: 16 }}>
        <Toggle name="has_iso17025_lab" value={form.has_iso17025_lab} onChange={set}
          label="Laboratório ISO 17025 identificado?" />
        <Toggle name="has_pah_analysis" value={form.has_pah_analysis} onChange={set}
          label="Análise de PAH realizada ou planejada?" />
        <Toggle name="heavy_metals_documented" value={form.heavy_metals_documented} onChange={set}
          label="Metais pesados documentados?" />
      </div>
    </>
  );
}

function StepCarbono({ form, set }) {
  return (
    <>
      <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: 16 }}>
        <Toggle name="has_lca" value={form.has_lca} onChange={set}
          label="LCA iniciada ou disponível?" />
        <Toggle name="has_system_boundary" value={form.has_system_boundary} onChange={set}
          label="Fronteira do sistema definida?" />
        <Toggle name="has_baseline" value={form.has_baseline} onChange={set}
          label="Cenário baseline documentado?" />
        <Toggle name="has_baseline_fate_evidence" value={form.has_baseline_fate_evidence} onChange={set}
          label="Evidência do destino do feedstock sem o projeto?" />
        <Toggle name="has_leakage_assessment" value={form.has_leakage_assessment} onChange={set}
          label="Avaliação de leakage realizada?" />
        <Toggle name="has_uncertainty_analysis" value={form.has_uncertainty_analysis} onChange={set}
          label="Análise de incerteza documentada?" />
      </div>

      <Field label="Opção de durabilidade" help="Isometric e Puro exigem seleção explícita (200 ou 1000 anos)." style={{ marginTop: 16 }}>
        <SelectInput name="durability_option" value={form.durability_option} onChange={set} options={[
          { value: "200_years",  label: "200 anos (padrão mais comum)" },
          { value: "1000_years", label: "1000 anos (maior rigor, maior crédito potencial)" },
          { value: "not_stated", label: "Ainda não definido" },
        ]} />
      </Field>

      <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: 16 }}>
        <Toggle name="has_soil_temp_method" value={form.has_soil_temp_method} onChange={set}
          label="Método de temperatura do solo definido?" />
        <Toggle name="has_reversal_risk_assessment" value={form.has_reversal_risk_assessment} onChange={set}
          label="Avaliação de risco de reversão?" />
      </div>

      <Field label="Distância de transporte (km round-trip)" help="Feedstock → planta + planta → aplicação. Relevante para Verra: acima de 200km aciona CDM TOOL12." style={{ marginTop: 4 }}>
        <TextInput name="transport_distance_km" value={form.transport_distance_km} onChange={set} type="number" placeholder="Ex: 80" />
      </Field>
    </>
  );
}

function StepAdicionalidade({ form, set }) {
  return (
    <>
      <Toggle name="has_financial_additionality" value={form.has_financial_additionality} onChange={set}
        label="Análise de adicionalidade financeira realizada?" />

      <Field label="Método de adicionalidade" style={{ marginTop: 16 }}>
        <SelectInput name="additionality_method" value={form.additionality_method} onChange={set} options={[
          { value: "irr_npv",      label: "Análise de TIR/VPL (IRR/NPV)" },
          { value: "cost_analysis", label: "Análise de custo incremental" },
          { value: "barriers",     label: "Análise de barreiras" },
          { value: "none",         label: "Nenhuma / ainda não realizada" },
        ]} />
      </Field>

      {form.additionality_method === "irr_npv" && (
        <Field label="TIR do projeto sem receita de carbono (%)" help="Se TIR < custo de capital setorial → adicionalidade financeira demonstrada.">
          <TextInput name="irr_without_carbon" value={form.irr_without_carbon} onChange={set} type="number" placeholder="Ex: 8.5" />
        </Field>
      )}

      <Field label="Caminho de adicionalidade Verra (VT0008)" help="Específico para Verra VCS. Outros padrões usam abordagens diferentes.">
        <SelectInput name="vt0008_path" value={form.vt0008_path} onChange={set} options={[
          { value: "investment_comparison", label: "Option 1 — Comparação de investimento (IRR/VPL)" },
          { value: "benchmark",             label: "Option 2 — Análise de benchmark setorial" },
          { value: "not_stated",            label: "Não aplicável / não definido" },
        ]} />
      </Field>

      <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: 16, marginTop: 8 }}>
        <Toggle name="has_regulatory_additionality" value={form.has_regulatory_additionality} onChange={set}
          label="Projeto não exigido por lei ou regulação?" />
        <Toggle name="is_first_of_its_kind" value={form.is_first_of_its_kind} onChange={set}
          label="Projeto pioneiro / first-of-its-kind?" />
        <Toggle name="has_common_practice_evidence" value={form.has_common_practice_evidence} onChange={set}
          label="Evidência de que não é prática comum?" />
        <Toggle name="is_greenfield_facility" value={form.is_greenfield_facility} onChange={set}
          label="Instalação nova (greenfield, não retrofit)?" />
      </div>

      {form.is_first_of_its_kind && (
        <div style={{ marginTop: 16, padding: "12px 14px", background: "#fffbeb", borderRadius: 8, border: "1px solid #fde68a", fontSize: 12, color: "#92400e" }}>
          ⚠️ <strong>Atenção — Puro.Earth:</strong> alegar first-of-its-kind como isenção de adicionalidade financeira é bloqueado pela Clarificação 005 ADD. O projeto ainda precisa demonstrar adicionalidade por outra via.
        </div>
      )}
    </>
  );
}

function StepMonitoramento({ form, set }) {
  return (
    <>
      <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: 16 }}>
        <Toggle name="has_monitoring_table" value={form.has_monitoring_table} onChange={set}
          label="Tabela de parâmetros de monitoramento?" />
        <Toggle name="has_data_storage_plan" value={form.has_data_storage_plan} onChange={set}
          label="Plano de armazenamento de dados?" />
        <Toggle name="has_continuous_weighing" value={form.has_continuous_weighing} onChange={set}
          label="Sistema de pesagem contínua do biochar?" />
        <Toggle name="has_fc_lab_analysis" value={form.has_fc_lab_analysis} onChange={set}
          label="Análise laboratorial de carbono orgânico (FCp)?" />
        <Toggle name="has_chain_of_custody" value={form.has_chain_of_custody} onChange={set}
          label="Sistema de rastreabilidade feedstock → aplicação?" />
        <Toggle name="has_application_coordinates" value={form.has_application_coordinates} onChange={set}
          label="Coordenadas geodésicas dos locais de aplicação?" />
        <Toggle name="has_offsite_backup" value={form.has_offsite_backup} onChange={set}
          label="Backup eletrônico offsite dos dados?" />
      </div>

      <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: 16, marginTop: 16 }}>
        <Field label="Período de retenção de dados (anos)" help="Verra exige ≥ 2 anos após o fim do período de crédito.">
          <TextInput name="data_retention_years" value={form.data_retention_years} onChange={set} type="number" placeholder="Ex: 3" />
        </Field>
        <Field label="Método de amostragem do biochar">
          <SelectInput name="sampling_method" value={form.sampling_method} onChange={set} options={[
            { value: "method_a",    label: "Método A — amostra a cada lote" },
            { value: "method_b",    label: "Método B — 1 a cada 10 lotes" },
            { value: "not_described", label: "Não definido" },
          ]} />
        </Field>
      </div>
    </>
  );
}

function StepSocial({ form, set }) {
  return (
    <>
      <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: 16 }}>
        <Toggle name="has_env_compliance" value={form.has_env_compliance} onChange={set}
          label="Conformidade ambiental documentada?" />
        <Toggle name="has_no_net_env_harm" value={form.has_no_net_env_harm} onChange={set}
          label="Sem dano ambiental líquido demonstrado?" />
        <Toggle name="has_no_net_social_harm" value={form.has_no_net_social_harm} onChange={set}
          label="Sem dano social líquido demonstrado?" />
        <Toggle name="has_stakeholder_consultation" value={form.has_stakeholder_consultation} onChange={set}
          label="Consulta a stakeholders realizada?" />
        <Toggle name="has_grievance_mechanism" value={form.has_grievance_mechanism} onChange={set}
          label="Mecanismo de queixas documentado?" />
        <Toggle name="has_sdg_reporting" value={form.has_sdg_reporting} onChange={set}
          label="Alinhamento com ODS (SDG reporting)?" />
        <Toggle name="has_adaptive_management" value={form.has_adaptive_management} onChange={set}
          label="Plano de gestão adaptativa?" />
        <Toggle name="has_pollution_prevention" value={form.has_pollution_prevention} onChange={set}
          label="Medidas de prevenção de poluição (PAH, metais)?" />
      </div>

      {form.has_adaptive_management && (
        <Field label="Número de gatilhos de gestão adaptativa documentados" help="Puro.Earth exige ≥ 4 gatilhos explícitos." style={{ marginTop: 16 }}>
          <TextInput name="adaptive_management_triggers" value={form.adaptive_management_triggers} onChange={set} type="number" placeholder="Ex: 4" />
        </Field>
      )}

      {form.has_sdg_reporting && (
        <div style={{ marginTop: 12 }}>
          <Toggle name="has_puro_sdg_template" value={form.has_puro_sdg_template} onChange={set}
            label="Usa o template SDG específico da Puro.Earth?" />
        </div>
      )}
    </>
  );
}

const STEP_COMPONENTS = [
  StepProjeto, StepFeedstock, StepProducao, StepBiochar,
  StepCarbono, StepAdicionalidade, StepMonitoramento, StepSocial,
];

// ── Resultados ────────────────────────────────────────────────────────────────

function ResultsView({ result, onReset, projectId }) {
  const { results, recommendation, reasoning } = result;
  const [chosen, setChosen] = useState(recommendation);

  const methods = Object.entries(results).sort((a, b) => b[1].overall - a[1].overall);

  return (
    <div style={{ maxWidth: 900, margin: "0 auto", padding: "0 24px 60px" }}>
      <div style={{ textAlign: "center", marginBottom: 40 }}>
        <h1 style={{ fontSize: 26, fontWeight: 800, color: "#0f172a", margin: "0 0 8px" }}>
          Fit Metodológico — Resultado Preliminar
        </h1>
        <p style={{ color: "#64748b", fontSize: 14 }}>
          Baseado nos dados autodeclarados. Não substitui auditoria com PDD completo.
        </p>
      </div>

      {/* Recomendação */}
      <div style={{
        background: "#eff6ff", border: "2px solid #3b82f6", borderRadius: 12,
        padding: "20px 24px", marginBottom: 32,
      }}>
        <div style={{ fontSize: 12, fontWeight: 700, color: "#1e40af", textTransform: "uppercase", letterSpacing: 1, marginBottom: 8 }}>
          Metodologia Recomendada
        </div>
        <div style={{ fontSize: 22, fontWeight: 800, color: "#1e40af", marginBottom: 8 }}>
          {METHOD_LABEL[recommendation]}
        </div>
        <p style={{ fontSize: 13, color: "#334155", margin: 0, lineHeight: 1.6 }}>
          {reasoning.replace(/\*\*(.*?)\*\*/g, (_, t) => t)}
        </p>
      </div>

      {/* Cards de metodologia */}
      <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fit, minmax(260px, 1fr))", gap: 16, marginBottom: 32 }}>
        {methods.map(([method, data]) => {
          const isRec = method === recommendation;
          const isChosen = method === chosen;
          return (
            <div key={method}
              onClick={() => setChosen(method)}
              style={{
                background: "#fff", borderRadius: 12, padding: "20px 20px 16px",
                border: `2px solid ${isChosen ? METHOD_COLOR[method] : "#e2e8f0"}`,
                cursor: "pointer", position: "relative",
                boxShadow: isChosen ? `0 0 0 4px ${METHOD_COLOR[method]}22` : "none",
                transition: "all .15s",
              }}>
              {isRec && (
                <span style={{
                  position: "absolute", top: -10, right: 12, background: "#16a34a",
                  color: "#fff", fontSize: 10, fontWeight: 700, padding: "2px 8px",
                  borderRadius: 10, textTransform: "uppercase",
                }}>Recomendada</span>
              )}
              <div style={{ fontWeight: 700, fontSize: 14, color: METHOD_COLOR[method], marginBottom: 4 }}>
                {data.label}
              </div>
              <div style={{ display: "flex", alignItems: "baseline", gap: 8, marginBottom: 12 }}>
                <span style={{ fontSize: 36, fontWeight: 900, color: GRADE_COLOR[data.grade] }}>{data.grade}</span>
                <span style={{ fontSize: 20, fontWeight: 700, color: "#475569" }}>{data.overall}%</span>
              </div>
              <div style={{ marginBottom: 14 }}>
                {Object.entries(data.dimensions || {}).map(([dim, score]) => (
                  <div key={dim} style={{ marginBottom: 5 }}>
                    <div style={{ display: "flex", justifyContent: "space-between", fontSize: 11, color: "#64748b", marginBottom: 2 }}>
                      <span>{DIM_LABEL[dim] || dim}</span>
                      <span style={{ fontWeight: 600 }}>{score !== null ? `${Math.round(score)}%` : "—"}</span>
                    </div>
                    <div style={{ height: 4, background: "#e2e8f0", borderRadius: 2 }}>
                      <div style={{
                        height: 4, borderRadius: 2, width: `${score || 0}%`,
                        background: score >= 70 ? "#22c55e" : score >= 45 ? "#f59e0b" : "#ef4444",
                        transition: "width .3s",
                      }} />
                    </div>
                  </div>
                ))}
              </div>
              <div style={{ fontSize: 11, color: "#94a3b8" }}>
                {data.compliant}/{data.total} requisitos conformes
              </div>
            </div>
          );
        })}
      </div>

      {/* Top Gaps do método escolhido */}
      {results[chosen]?.top_gaps?.length > 0 && (
        <div style={{ marginBottom: 32 }}>
          <h2 style={{ fontSize: 16, fontWeight: 700, color: "#1e293b", marginBottom: 16 }}>
            Principais gaps — {METHOD_LABEL[chosen]}
          </h2>
          <div style={{ display: "flex", flexDirection: "column", gap: 10 }}>
            {results[chosen].top_gaps.map((gap, i) => (
              <div key={i} style={{
                background: "#fff", border: "1px solid #e2e8f0", borderRadius: 8,
                padding: "12px 14px", borderLeft: "3px solid #f59e0b",
              }}>
                <div style={{ fontWeight: 600, fontSize: 12, color: "#0f172a", marginBottom: 4 }}>
                  {gap.requirement_name || gap.title}
                </div>
                <div style={{ fontSize: 12, color: "#64748b", marginBottom: 4 }}>
                  {gap.gap || "—"}
                </div>
                {gap.recommendation && (
                  <div style={{ fontSize: 11, color: "#0369a1", fontStyle: "italic" }}>
                    → {gap.recommendation}
                  </div>
                )}
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Ações */}
      <div style={{ display: "flex", gap: 12, flexWrap: "wrap" }}>
        <button
          onClick={() => alert(`PDD Draft para ${METHOD_LABEL[chosen]} em breve!`)}
          style={{
            padding: "12px 24px", background: METHOD_COLOR[chosen], color: "#fff",
            border: "none", borderRadius: 8, fontWeight: 700, fontSize: 14,
            cursor: "pointer",
          }}>
          Gerar PDD Draft — {METHOD_LABEL[chosen]}
        </button>
        {projectId && (
          <a
            href={`/projects/${projectId}`}
            style={{
              padding: "12px 24px", background: "#fff", color: "#1e40af",
              border: "2px solid #1e40af", borderRadius: 8, fontWeight: 700,
              fontSize: 14, textDecoration: "none",
            }}>
            Ver Projeto
          </a>
        )}
        <button
          onClick={onReset}
          style={{
            padding: "12px 24px", background: "#f1f5f9", color: "#475569",
            border: "1px solid #cbd5e1", borderRadius: 8, fontWeight: 600,
            fontSize: 14, cursor: "pointer",
          }}>
          Nova Análise
        </button>
      </div>

      <p style={{ fontSize: 11, color: "#94a3b8", marginTop: 24 }}>
        ⚠️ Avaliação preliminar baseada em dados autodeclarados. Scores podem variar significativamente após auditoria com PDD completo.
      </p>
    </div>
  );
}

// ── Página principal ──────────────────────────────────────────────────────────

const EMPTY_FORM = {
  project_name: "", project_country: "brazil",
  biochar_t_dry_year: null, estimated_credits_tco2: null,
  storage_pathway: "soil",
  feedstock_type: "", is_forest_biomass: false,
  is_purpose_grown: false, feedstock_imported: false,
  uses_mixed_waste: false, uses_coal_ash: false, from_land_clearing: false,
  has_fsc_certification: false, has_pefc_certification: false,
  has_isae3000_dossier: false, has_government_mgmt_plan: false,
  pyrolysis_temp_c: null, verra_tech_class: "",
  has_continuous_temp_monitoring: false, has_pyrolysis_gas_recovery: false,
  has_engineering_diagram: false, has_maintenance_plan: false, reactor_type: "",
  h_c_ratio: null, o_c_ratio: null, pah_value: null, pcb_value: null,
  quality_standard: "not_stated", has_iso17025_lab: false,
  has_pah_analysis: false, heavy_metals_documented: false,
  has_lca: false, has_system_boundary: false, has_baseline: false,
  has_baseline_fate_evidence: false, has_leakage_assessment: false,
  has_uncertainty_analysis: false, durability_option: "not_stated",
  has_soil_temp_method: false, has_reversal_risk_assessment: false,
  transport_distance_km: null,
  has_financial_additionality: false, additionality_method: "none",
  irr_without_carbon: null, is_first_of_its_kind: false,
  financial_additionality_exemption_claimed: false,
  has_regulatory_additionality: false, has_common_practice_evidence: false,
  vt0008_path: "not_stated", is_greenfield_facility: true,
  has_monitoring_table: false, has_data_storage_plan: false,
  has_continuous_weighing: false, has_fc_lab_analysis: false,
  has_chain_of_custody: false, has_application_coordinates: false,
  has_offsite_backup: false, data_retention_years: null,
  sampling_method: "not_described",
  has_env_compliance: false, has_no_net_env_harm: false,
  has_no_net_social_harm: false, has_stakeholder_consultation: false,
  has_grievance_mechanism: false, has_sdg_reporting: false,
  has_adaptive_management: false, has_pollution_prevention: false,
  adaptive_management_triggers: 0, has_puro_sdg_template: false,
  soil_application: true,
};

export default function PinGeneratorPage() {
  const navigate = useNavigate();
  const [step, setStep]     = useState(0);
  const [form, setForm]     = useState(EMPTY_FORM);
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState(null);
  const [projectId, setProjectId] = useState(null);
  const [error, setError]   = useState(null);

  const set = useCallback((name, value) => {
    setForm(f => ({ ...f, [name]: value }));
  }, []);

  const StepComp = STEP_COMPONENTS[step];
  const isFirst  = step === 0;
  const isLast   = step === STEPS.length - 1;

  const handleSubmit = async () => {
    setLoading(true);
    setError(null);
    try {
      const res = await fetch(`${API}/api/pin/audit`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ form, save: !!form.project_name }),
      });
      if (!res.ok) throw new Error(await res.text());
      const data = await res.json();
      setResult(data);
      if (data.project_id) setProjectId(data.project_id);
    } catch (e) {
      setError(e.message);
    } finally {
      setLoading(false);
    }
  };

  if (result) {
    return (
      <ResultsView
        result={result}
        projectId={projectId}
        onReset={() => { setResult(null); setStep(0); setForm(EMPTY_FORM); setProjectId(null); }}
      />
    );
  }

  return (
    <div style={{ minHeight: "100vh", background: "#f8fafc" }}>
      {/* Header */}
      <div style={{ background: "#1e40af", padding: "16px 24px", display: "flex", alignItems: "center", gap: 16 }}>
        <button
          onClick={() => navigate("/")}
          style={{ background: "transparent", border: "none", color: "#93c5fd", cursor: "pointer", fontSize: 14 }}>
          ← Voltar
        </button>
        <div>
          <div style={{ color: "#fff", fontWeight: 800, fontSize: 16 }}>Novo Projeto — Análise Preliminar</div>
          <div style={{ color: "#93c5fd", fontSize: 12 }}>Project Idea Note + Fit Metodológico</div>
        </div>
      </div>

      {/* Progress */}
      <div style={{ background: "#fff", borderBottom: "1px solid #e2e8f0", padding: "0 24px" }}>
        <div style={{ maxWidth: 900, margin: "0 auto", display: "flex", gap: 0, overflowX: "auto" }}>
          {STEPS.map((s, i) => (
            <button
              key={s.id}
              onClick={() => i < step && setStep(i)}
              style={{
                padding: "14px 16px", border: "none", background: "transparent",
                borderBottom: `3px solid ${i === step ? "#1e40af" : "transparent"}`,
                color: i === step ? "#1e40af" : i < step ? "#22c55e" : "#94a3b8",
                fontWeight: i === step ? 700 : 500, fontSize: 12,
                cursor: i < step ? "pointer" : "default", whiteSpace: "nowrap",
                display: "flex", alignItems: "center", gap: 6,
              }}>
              <span>{i < step ? "✓" : s.icon}</span>
              <span>{s.label}</span>
            </button>
          ))}
        </div>
      </div>

      {/* Form */}
      <div style={{ maxWidth: 900, margin: "32px auto", padding: "0 24px" }}>
        <div style={{ background: "#fff", borderRadius: 12, border: "1px solid #e2e8f0", padding: "28px 32px" }}>
          <h2 style={{ fontSize: 18, fontWeight: 700, color: "#0f172a", margin: "0 0 6px" }}>
            {STEPS[step].icon} {STEPS[step].label}
          </h2>
          <p style={{ fontSize: 13, color: "#64748b", margin: "0 0 24px" }}>
            Passo {step + 1} de {STEPS.length} — preencha o que souber; campos em branco assumem valores conservadores.
          </p>

          <StepComp form={form} set={set} />

          {error && (
            <div style={{ marginTop: 16, padding: "10px 14px", background: "#fef2f2", border: "1px solid #fca5a5", borderRadius: 6, color: "#b91c1c", fontSize: 13 }}>
              {error}
            </div>
          )}

          <div style={{ display: "flex", justifyContent: "space-between", marginTop: 32, borderTop: "1px solid #f1f5f9", paddingTop: 24 }}>
            <button
              onClick={() => setStep(s => s - 1)}
              disabled={isFirst}
              style={{
                padding: "10px 20px", border: "1px solid #cbd5e1", borderRadius: 8,
                background: "#fff", color: "#475569", fontWeight: 600, fontSize: 13,
                cursor: isFirst ? "not-allowed" : "pointer", opacity: isFirst ? 0.4 : 1,
              }}>
              ← Anterior
            </button>

            {isLast ? (
              <button
                onClick={handleSubmit}
                disabled={loading || !form.project_name || !form.feedstock_type}
                style={{
                  padding: "10px 28px", background: "#1e40af", color: "#fff",
                  border: "none", borderRadius: 8, fontWeight: 700, fontSize: 14,
                  cursor: loading ? "wait" : "pointer",
                  opacity: (!form.project_name || !form.feedstock_type) ? 0.5 : 1,
                }}>
                {loading ? "Analisando..." : "Analisar → Fit Metodológico"}
              </button>
            ) : (
              <button
                onClick={() => setStep(s => s + 1)}
                style={{
                  padding: "10px 24px", background: "#1e40af", color: "#fff",
                  border: "none", borderRadius: 8, fontWeight: 700, fontSize: 13,
                  cursor: "pointer",
                }}>
                Próximo →
              </button>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}
