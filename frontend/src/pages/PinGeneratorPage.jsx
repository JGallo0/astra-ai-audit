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

// ── Passos ────────────────────────────────────────────────────────────────────
const STEPS = [
  { id: "projeto",       label: "Projeto",           icon: "🏭" },
  { id: "feedstock",     label: "Feedstock",         icon: "🌿" },
  { id: "producao",      label: "Produção",           icon: "🔥" },
  { id: "biochar",       label: "Biochar",            icon: "⚗️" },
  { id: "carbono",       label: "Carbono",            icon: "📊" },
  { id: "adicionalidade",label: "Adicionalidade",     icon: "✅" },
  { id: "monitoramento", label: "Monitoramento",      icon: "📡" },
  { id: "social",        label: "Social & Ambiental", icon: "🤝" },
];

// Campos obrigatórios por passo
const REQUIRED_BY_STEP = {
  0: ["project_name", "project_country", "storage_pathway"],
  1: ["feedstock_type"],
};

// ── Primitivos de UI ──────────────────────────────────────────────────────────
const inp = {
  width: "100%", boxSizing: "border-box", padding: "8px 10px",
  border: "1px solid #cbd5e1", borderRadius: 6, fontSize: 13,
  background: "#fff", color: "#1e293b", fontFamily: "inherit",
};
const inpError = { ...inp, border: "1px solid #ef4444", background: "#fef2f2" };

function Field({ label, help, children, required, error }) {
  return (
    <div style={{ marginBottom: 18 }}>
      <label style={{ display: "block", fontWeight: 600, fontSize: 13, marginBottom: 4, color: error ? "#dc2626" : "#1e293b" }}>
        {label}
        {required && <span style={{ color: "#dc2626", marginLeft: 3 }} title="Campo obrigatório">*</span>}
      </label>
      {help && <p style={{ fontSize: 11, color: "#64748b", margin: "0 0 6px" }}>{help}</p>}
      {children}
      {error && <p style={{ fontSize: 11, color: "#dc2626", margin: "4px 0 0" }}>{error}</p>}
    </div>
  );
}

function TextInput({ name, value, onChange, placeholder, type = "text", hasError }) {
  return (
    <input
      style={hasError ? inpError : inp}
      type={type} name={name} value={value ?? ""}
      placeholder={placeholder}
      onChange={e => onChange(name, type === "number"
        ? (e.target.value === "" ? null : Number(e.target.value))
        : e.target.value)}
    />
  );
}

function SelectInput({ name, value, onChange, options, hasError }) {
  return (
    <select
      style={hasError ? inpError : inp}
      name={name} value={value ?? ""}
      onChange={e => onChange(name, e.target.value)}>
      <option value="">— Selecione —</option>
      {options.map(o => <option key={o.value} value={o.value}>{o.label}</option>)}
    </select>
  );
}

function Toggle({ name, value, onChange, label }) {
  return (
    <label style={{ display: "flex", alignItems: "center", gap: 10, cursor: "pointer", userSelect: "none", marginBottom: 10 }}>
      <div
        onClick={() => onChange(name, !value)}
        style={{
          width: 40, height: 22, borderRadius: 11,
          background: value ? "#1e40af" : "#cbd5e1",
          position: "relative", transition: "background .2s", flexShrink: 0,
        }}>
        <div style={{
          position: "absolute", top: 3, left: value ? 21 : 3,
          width: 16, height: 16, borderRadius: "50%",
          background: "#fff", transition: "left .2s",
        }} />
      </div>
      <span style={{ fontSize: 13, color: "#1e293b" }}>{label}</span>
    </label>
  );
}

/**
 * KnownValueField — input sempre visível.
 * Vazio → mostra default aplicado. Preenchido → mostra impacto calculado.
 * Remove o toggle "Tenho este dado" que confundia o usuário.
 */
function KnownValueField({ valueName, label, help, defaultText, unit, placeholder, form, set, type = "number" }) {
  const val = form[valueName];
  const hasValue = val !== null && val !== undefined && val !== "";
  return (
    <div style={{ marginBottom: 18 }}>
      <label style={{ display: "block", fontWeight: 600, fontSize: 13, marginBottom: 4, color: "#1e293b" }}>
        {label}
      </label>
      {help && <p style={{ fontSize: 11, color: "#64748b", margin: "0 0 6px" }}>{help}</p>}
      <div style={{ display: "flex", gap: 8, alignItems: "center" }}>
        <input
          style={{ ...inp, flex: 1 }}
          type={type} value={val ?? ""}
          placeholder={placeholder || `Opcional — sem valor: ${defaultText}`}
          onChange={e => set(valueName, e.target.value === "" ? null : (type === "number" ? Number(e.target.value) : e.target.value))}
        />
        {unit && <span style={{ fontSize: 12, color: "#64748b", whiteSpace: "nowrap" }}>{unit}</span>}
      </div>
      {!hasValue && (
        <div style={{
          marginTop: 5, padding: "5px 10px", background: "#f8fafc",
          border: "1px dashed #cbd5e1", borderRadius: 5,
          fontSize: 11, color: "#64748b",
        }}>
          📌 Sem valor: <strong style={{ color: "#475569" }}>{defaultText}</strong>
        </div>
      )}
    </div>
  );
}

// ── Passos do formulário ──────────────────────────────────────────────────────

function StepProjeto({ form, set, errors }) {
  return (
    <>
      <Field label="Nome do projeto" required error={errors.project_name}>
        <TextInput name="project_name" value={form.project_name} onChange={set}
          placeholder="Ex: Biochar Serra Negra" hasError={!!errors.project_name} />
      </Field>
      <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: 16 }}>
        <Field label="País" required error={errors.project_country}>
          <SelectInput name="project_country" value={form.project_country} onChange={set} hasError={!!errors.project_country} options={[
            { value: "brazil",    label: "Brasil (CPI 36)" },
            { value: "germany",   label: "Alemanha (CPI 79)" },
            { value: "usa",       label: "EUA (CPI 69)" },
            { value: "chile",     label: "Chile (CPI 52)" },
            { value: "india",     label: "Índia (CPI 39)" },
            { value: "indonesia", label: "Indonésia (CPI 34)" },
            { value: "bolivia",   label: "Bolívia (CPI 27)" },
            { value: "other",     label: "Outro" },
          ]} />
        </Field>
        <Field label="Via de aplicação" required error={errors.storage_pathway}>
          <SelectInput name="storage_pathway" value={form.storage_pathway} onChange={set} hasError={!!errors.storage_pathway} options={[
            { value: "soil",             label: "Solo agrícola" },
            { value: "built_environment",label: "Construção civil" },
            { value: "water_filtration", label: "Filtração de água" },
            { value: "other",            label: "Outra" },
          ]} />
        </Field>
      </div>
      <KnownValueField
        valueName="biochar_t_dry_year"
        label="Produção anual estimada de biochar"
        help="Toneladas de biochar seco por ano. Necessário para estimar volume de créditos."
        defaultText="Escala indefinida — não penaliza a auditoria"
        unit="t/ano" placeholder="Ex: 1000" form={form} set={set}
      />
      <KnownValueField
        valueName="estimated_credits_tco2"
        label="Créditos estimados"
        defaultText="Calculado pelo engine a partir dos dados técnicos"
        unit="tCO₂e/ano" placeholder="Ex: 750" form={form} set={set}
      />
    </>
  );
}

function StepFeedstock({ form, set, errors }) {
  // is_forest_biomass é derivado do tipo selecionado — sem toggle separado
  const isForest = form.feedstock_type === "forest_biomass";

  const handleFeedstockType = (name, value) => {
    set(name, value);
    // Sincroniza is_forest_biomass automaticamente
    set("is_forest_biomass", value === "forest_biomass");
  };

  return (
    <>
      <Field label="Tipo de feedstock" required error={errors.feedstock_type}
        help="Selecione o tipo principal. As perguntas abaixo tratam de condições adicionais independentes do tipo.">
        <SelectInput name="feedstock_type" value={form.feedstock_type}
          onChange={handleFeedstockType} hasError={!!errors.feedstock_type} options={[
          { value: "agricultural_residue", label: "Resíduo agrícola (palha, bagaço, casca, podas de lavoura)" },
          { value: "forest_biomass",       label: "Biomassa florestal (galhos, serragem, podas de reflorestamento)" },
          { value: "urban_wood",           label: "Madeira urbana / resíduo de processamento de madeira" },
          { value: "food_waste",           label: "Resíduo de processamento alimentar" },
          { value: "sewage_sludge",        label: "Lodo de esgoto (biossólido)" },
          { value: "animal_manure",        label: "Esterco animal" },
          { value: "mixed",                label: "Misto (múltiplos resíduos biogênicos)" },
          { value: "other",                label: "Outro" },
        ]} />
      </Field>

      {/* Requisitos de sustentabilidade por tipo — aparecem automaticamente */}

      {isForest && (
        <div style={{ marginBottom: 16, padding: "14px 16px", background: "#eff6ff", borderRadius: 8, border: "1px solid #bfdbfe" }}>
          <p style={{ fontWeight: 700, fontSize: 13, margin: "0 0 4px", color: "#1e40af" }}>
            🌲 Certificação de sustentabilidade florestal
          </p>
          <p style={{ fontSize: 11, color: "#475569", margin: "0 0 12px" }}>
            Obrigatória para Puro.Earth. Verra aceita PEFC, FSC ou definição CDM de biomassa renovável.
            CPI Brasil = 36 → plano de manejo governamental <strong>não disponível</strong> na Puro.Earth (exige CPI ≥ 50).
          </p>
          <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: "4px 16px" }}>
            <Toggle name="has_fsc_certification"    value={form.has_fsc_certification}    onChange={set} label="Certificação FSC ativa" />
            <Toggle name="has_pefc_certification"   value={form.has_pefc_certification}   onChange={set} label="Certificação PEFC ativa" />
            <Toggle name="has_isae3000_dossier"     value={form.has_isae3000_dossier}     onChange={set} label="Dossiê auditado ISAE 3000" />
            <Toggle name="has_government_mgmt_plan" value={form.has_government_mgmt_plan} onChange={set} label="Plano de manejo gov. (CPI ≥ 50)" />
          </div>
        </div>
      )}

      {form.feedstock_type === "agricultural_residue" && (
        <div style={{ marginBottom: 16, padding: "14px 16px", background: "#fffbeb", borderRadius: 8, border: "1px solid #fde68a" }}>
          <p style={{ fontWeight: 700, fontSize: 13, margin: "0 0 4px", color: "#92400e" }}>
            🌾 Resíduo agrícola — limite de remoção (Verra Tabela 1)
          </p>
          <p style={{ fontSize: 11, color: "#475569", margin: "0 0 10px" }}>
            Remover mais de 50% dos resíduos do campo sem documentação de saúde do solo
            resulta em penalidade de elegibilidade na Verra VCS.
          </p>
          <Toggle name="high_residue_removal" value={form.high_residue_removal} onChange={set}
            label="Remove mais de 50% dos resíduos do campo?" />
          {form.high_residue_removal && (
            <Toggle name="has_soil_health_docs" value={form.has_soil_health_docs} onChange={set}
              label="Possui documentação de que não causa degradação do solo?" />
          )}
        </div>
      )}

      {form.feedstock_type === "food_waste" && (
        <div style={{ marginBottom: 16, padding: "14px 16px", background: "#fffbeb", borderRadius: 8, border: "1px solid #fde68a" }}>
          <p style={{ fontWeight: 700, fontSize: 13, margin: "0 0 4px", color: "#92400e" }}>
            🏭 Resíduo alimentar — critério de proporcionalidade (Verra Tabela 1)
          </p>
          <p style={{ fontSize: 11, color: "#475569", margin: "0 0 10px" }}>
            O volume de resíduos gerado não pode ter aumentado especificamente para produzir biochar.
            O resíduo deve ser subproduto natural da operação.
          </p>
          <Toggle name="residue_volume_increased" value={form.residue_volume_increased} onChange={set}
            label="Volume de resíduos aumentou para viabilizar o projeto de biochar?" />
          {form.residue_volume_increased && (
            <div style={{ marginTop: 6, padding: "8px 12px", background: "#fef2f2", borderRadius: 6, border: "1px solid #fca5a5", fontSize: 12, color: "#b91c1c" }}>
              ❌ Volume de resíduos aumentado especificamente para biochar → inelegível na Verra VCS (Tabela 1).
            </div>
          )}
        </div>
      )}

      {form.feedstock_type === "sewage_sludge" && (
        <div style={{ marginBottom: 16, padding: "14px 16px", background: "#f8fafc", borderRadius: 8, border: "1px solid #e2e8f0" }}>
          <p style={{ fontWeight: 700, fontSize: 13, margin: "0 0 4px", color: "#475569" }}>
            💧 Biossólido — conformidade com contaminantes
          </p>
          <p style={{ fontSize: 11, color: "#64748b", margin: 0 }}>
            Biossólidos devem cumprir os limites de metais pesados e contaminantes das diretrizes
            IBI ou EBC. Verifique os campos de PAH, PCB e metais pesados no Passo 4 (Biochar).
          </p>
        </div>
      )}

      {form.feedstock_type === "mixed" && (
        <div style={{ marginBottom: 16, padding: "14px 16px", background: "#f8fafc", borderRadius: 8, border: "1px solid #e2e8f0" }}>
          <p style={{ fontWeight: 700, fontSize: 13, margin: "0 0 4px", color: "#475569" }}>
            🔀 Misto — cada componente deve ser elegível individualmente
          </p>
          <p style={{ fontSize: 11, color: "#64748b", margin: 0 }}>
            Todos os tipos de resíduo incluídos devem atender os critérios de elegibilidade
            individualmente. Marque abaixo se algum componente envolve material fóssil ou coal ash
            (hard gates nas condições adicionais abaixo).
          </p>
        </div>
      )}

      {/* Condições de risco — independentes do tipo de feedstock */}
      <p style={{ fontSize: 12, fontWeight: 600, color: "#475569", margin: "4px 0 10px" }}>
        Condições adicionais
      </p>
      <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: "4px 16px" }}>
        <Toggle name="is_purpose_grown"   value={form.is_purpose_grown}   onChange={set} label="Cultivado para este fim (não é resíduo)?" />
        <Toggle name="feedstock_imported" value={form.feedstock_imported} onChange={set} label="Importado de outro país?" />
        <Toggle name="uses_mixed_waste"   value={form.uses_mixed_waste}   onChange={set} label="Contém materiais fósseis (plásticos, sintéticos)?" />
        <Toggle name="uses_coal_ash"      value={form.uses_coal_ash}      onChange={set} label="Usa cinza de carvão fóssil como insumo ou aditivo?" />
        <Toggle name="from_land_clearing" value={form.from_land_clearing} onChange={set} label="Proveniente de desmatamento / limpeza de terra?" />
      </div>

      {/* Alertas de hard gate */}
      {form.is_purpose_grown && (
        <div style={{ marginTop: 8, padding: "10px 14px", background: "#fef2f2", borderRadius: 6, border: "1px solid #fca5a5", fontSize: 12, color: "#b91c1c" }}>
          ❌ Feedstock cultivado para este fim elimina Verra VCS (AC 4a) e Puro.Earth.
        </div>
      )}
      {form.uses_mixed_waste && (
        <div style={{ marginTop: 8, padding: "10px 14px", background: "#fef2f2", borderRadius: 6, border: "1px solid #fca5a5", fontSize: 12, color: "#b91c1c" }}>
          ❌ Contaminação fóssil elimina Puro.Earth (Clarificação 001 BCH — hard gate absoluto).
        </div>
      )}
      {form.uses_coal_ash && (
        <div style={{ marginTop: 8, padding: "10px 14px", background: "#fef2f2", borderRadius: 6, border: "1px solid #fca5a5", fontSize: 12, color: "#b91c1c" }}>
          ❌ Cinza de carvão fóssil como insumo elimina Puro.Earth (Clar. 010 CAM). Nota: cinzas naturais do biochar (fração mineral da biomassa) são normais e não estão relacionadas a este critério.
        </div>
      )}
    </>
  );
}

const REACTOR_TECH = {
  retort_kiln: "high", tlud_gasifier: "high", flash_carbonization: "high",
  rotary_kiln: "high", integrated_chp: "high",
  drum_kiln: "low", pit_kiln: "low", open_burning: "low",
};
const REACTOR_TEMP = {
  flash_carbonization: 700, integrated_chp: 650, tlud_gasifier: 550,
  retort_kiln: 500, rotary_kiln: 500, drum_kiln: 400, pit_kiln: 350, open_burning: 300,
};
const ALL_REACTORS = [
  { value: "retort_kiln",        label: "Kiln retorta (pirólise fechada, ~500°C)",             tech: "high" },
  { value: "tlud_gasifier",      label: "TLUD / Gasificador (alta eficiência, ~550°C)",        tech: "high" },
  { value: "flash_carbonization",label: "Flash carbonization (>700°C, alta permanência)",       tech: "high" },
  { value: "rotary_kiln",        label: "Kiln rotativo (industrial, ~500°C)",                  tech: "high" },
  { value: "integrated_chp",     label: "Sistema integrado pirólise + CHP (>650°C, rec. gás)", tech: "high" },
  { value: "drum_kiln",          label: "Forno de tambor / drum kiln (~400°C)",                tech: "low"  },
  { value: "pit_kiln",           label: "Forno de cova / pit kiln (artesanal, ~350°C)",        tech: "low"  },
  { value: "open_burning",       label: "Queima aberta (proibido em Puro.Earth)",              tech: "low"  },
  { value: "other",              label: "Outro / não definido",                                tech: null   },
];

function StepProducao({ form, set }) {
  const temp      = form.pyrolysis_temp_c;
  const techClass = form.verra_tech_class;

  const reactorOptions = ALL_REACTORS.filter(
    r => !techClass || r.tech === techClass || r.tech === null
  );

  const handleTechClass = (name, val) => {
    set("verra_tech_class", val);
    const currentTech = REACTOR_TECH[form.reactor_type];
    if (form.reactor_type && currentTech && currentTech !== val) {
      set("reactor_type", "");
    }
  };

  const handleReactorType = (name, val) => {
    set("reactor_type", val);
    const tech = REACTOR_TECH[val];
    const hint = REACTOR_TEMP[val];
    if (tech && !form.verra_tech_class) set("verra_tech_class", tech);
    if (hint && !form.pyrolysis_temp_c) set("pyrolysis_temp_c", hint);
  };

  let prdeMsg = null;
  if (temp !== null && temp !== undefined) {
    if (temp < 350)      prdeMsg = { color: "#b91c1c", bg: "#fef2f2", border: "#fca5a5", text: `❌ ${temp}°C < 350°C → biochar não elegível para créditos` };
    else if (temp < 450) prdeMsg = { color: "#92400e", bg: "#fffbeb", border: "#fde68a", text: `⚠️ ${temp}°C → PRde Verra = 0.65 (baixa temperatura)` };
    else if (temp < 600) prdeMsg = { color: "#92400e", bg: "#fffbeb", border: "#fde68a", text: `⚠️ ${temp}°C → PRde Verra = 0.80 (temperatura média)` };
    else                 prdeMsg = { color: "#15803d", bg: "#f0fdf4", border: "#bbf7d0", text: `✅ ${temp}°C > 600°C → PRde Verra = 0.89 (máxima permanência)` };
  }

  return (
    <>
      <KnownValueField
        valueName="pyrolysis_temp_c"
        label="Temperatura média de pirólise"
        help="Driver primário de permanência na Verra VCS (Tabela 3). Também informa Isometric/Puro via H/Corg esperado."
        defaultText="PRde Verra = 0.56 (Tabela 3 VM0044, temperatura desconhecida)"
        unit="°C" placeholder="Ex: 600" form={form} set={set}
      />
      {prdeMsg && (
        <div style={{ padding: "8px 12px", background: prdeMsg.bg, border: `1px solid ${prdeMsg.border}`, borderRadius: 6, fontSize: 12, color: prdeMsg.color, marginTop: -8, marginBottom: 16 }}>
          {prdeMsg.text}
        </div>
      )}

      <Field label="Classe tecnológica da instalação"
        help="Filtra os tipos de reator disponíveis abaixo.">
        <SelectInput name="verra_tech_class" value={techClass} onChange={handleTechClass} options={[
          { value: "high", label: "Alta tecnologia (controle automatizado, sensores contínuos)" },
          { value: "low",  label: "Baixa tecnologia (fornos simples, sem automação)" },
          { value: "",     label: "Não sei / não definido" },
        ]} />
      </Field>

      <Field label="Tipo de reator / forno"
        help={techClass
          ? `Exibindo tipos de ${techClass === "high" ? "alta" : "baixa"} tecnologia.`
          : "Selecione a classe acima para filtrar os tipos."}>
        <SelectInput name="reactor_type" value={form.reactor_type} onChange={handleReactorType} options={reactorOptions} />
      </Field>

      {form.reactor_type === "open_burning" && (
        <div style={{ padding: "8px 12px", background: "#fef2f2", border: "1px solid #fca5a5", borderRadius: 6, fontSize: 12, color: "#b91c1c", marginTop: -8 }}>
          ❌ Queima aberta é proibida em Puro.Earth (Clar. 004 BCH) e não atinge temperatura mínima para créditos.
        </div>
      )}

      <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: "4px 16px", marginTop: 8 }}>
        <Toggle name="has_continuous_temp_monitoring" value={form.has_continuous_temp_monitoring} onChange={set} label="Monitoramento contínuo de temperatura?" />
        <Toggle name="has_pyrolysis_gas_recovery"     value={form.has_pyrolysis_gas_recovery}     onChange={set} label="Gases de pirólise recuperados/combustados?" />
        <Toggle name="has_engineering_diagram"        value={form.has_engineering_diagram}        onChange={set} label="Diagrama de engenharia do reator?" />
        <Toggle name="has_maintenance_plan"           value={form.has_maintenance_plan}           onChange={set} label="Plano de manutenção do reator?" />
      </div>

      {!form.has_pyrolysis_gas_recovery && (
        <div style={{ padding: "8px 12px", background: "#fffbeb", border: "1px solid #fde68a", borderRadius: 6, fontSize: 12, color: "#92400e", marginTop: 4 }}>
          ⚠️ Sem recuperação de gás: hard gate em Puro.Earth. Penalidade em Isometric (net-negativity).
          Na Verra: PEP,p,y calculado via Fe default = 0.049 tCH₄/t biochar.
        </div>
      )}
    </>
  );
}

function StepBiochar({ form, set }) {
  const hc = form.h_c_ratio;
  let hcMsg = null;
  if (hc !== null && hc !== undefined) {
    if (hc >= 0.5)       hcMsg = { color: "#b91c1c", bg: "#fef2f2", border: "#fca5a5", text: `❌ H/Corg ${hc} ≥ 0.5 → permanência zero em Isometric e Puro.Earth (hard gate)` };
    else if (hc > 0.7)   hcMsg = { color: "#92400e", bg: "#fffbeb", border: "#fde68a", text: `⚠️ H/Corg ${hc} > 0.7 → inelegível para solo na Verra VCS (AC 10)` };
    else if (hc >= 0.3)  hcMsg = { color: "#92400e", bg: "#fffbeb", border: "#fde68a", text: `⚠️ H/Corg ${hc} — elegível, mas permanência moderada (ideal < 0.3)` };
    else                  hcMsg = { color: "#15803d", bg: "#f0fdf4", border: "#bbf7d0", text: `✅ H/Corg ${hc} — excelente estabilidade` };
  }

  return (
    <>
      <KnownValueField
        valueName="h_c_ratio"
        label="H/Corg — razão molar hidrogênio/carbono orgânico"
        help="Driver primário de permanência em Isometric e Puro.Earth (Woolf 2021). Gate binário na Verra (≤ 0.7 para solo)."
        defaultText="0.35 (típico resíduo madeireiro, pirólise 500°C) — permanência conservadora"
        unit="adimensional" placeholder="Ex: 0.28" form={form} set={set}
      />
      {hcMsg && (
        <div style={{ padding: "8px 12px", background: hcMsg.bg, border: `1px solid ${hcMsg.border}`, borderRadius: 6, fontSize: 12, color: hcMsg.color, marginTop: -8, marginBottom: 16 }}>
          {hcMsg.text}
        </div>
      )}

      <KnownValueField
        valueName="o_c_ratio"
        label="O/Corg — razão molar oxigênio/carbono orgânico"
        help="Deve ser < 0.2 em Isometric e Puro.Earth. Hard gate se ≥ 0.2."
        defaultText="0.08 (pirólise > 450°C) — assumido dentro do limite"
        unit="adimensional" placeholder="Ex: 0.07" form={form} set={set}
      />
      {form.o_c_ratio !== null && form.o_c_ratio >= 0.2 && (
        <div style={{ padding: "8px 12px", background: "#fef2f2", border: "1px solid #fca5a5", borderRadius: 6, fontSize: 12, color: "#b91c1c", marginTop: -8, marginBottom: 16 }}>
          ❌ O/Corg ≥ 0.2 → permanência zero em Isometric e Puro.Earth (hard gate)
        </div>
      )}

      <KnownValueField
        valueName="pah_value"
        label="PAH — hidrocarbonetos aromáticos policíclicos"
        help="Limite WBC/Isometric: 12 mg/kg. Limite IBI Basic: 20 mg/kg. IBI Premium: 6 mg/kg."
        defaultText="Sem análise — conformidade não verificável (não penalizado)"
        unit="mg/kg" placeholder="Ex: 4.2" form={form} set={set}
      />
      {form.pah_value !== null && form.pah_value > 12 && (
        <div style={{ padding: "8px 12px", background: "#fef2f2", border: "1px solid #fca5a5", borderRadius: 6, fontSize: 12, color: "#b91c1c", marginTop: -8, marginBottom: 16 }}>
          ❌ PAH {form.pah_value} mg/kg > 12 → ambiental zerado em Isometric e Puro.Earth
        </div>
      )}

      <KnownValueField
        valueName="pcb_value"
        label="PCB — bifenilas policloradas"
        defaultText="Sem análise — não penalizado"
        unit="mg/kg" placeholder="Ex: 0.05" form={form} set={set}
      />

      <Field label="Padrão de qualidade aplicável">
        <SelectInput name="quality_standard" value={form.quality_standard} onChange={set} options={[
          { value: "ibi",               label: "IBI Biochar Standard" },
          { value: "ebc",               label: "EBC (European Biochar Certificate)" },
          { value: "local_regulation",  label: "Regulação local específica" },
          { value: "not_stated",        label: "Não definido / ainda em análise" },
        ]} />
      </Field>

      <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: "4px 16px" }}>
        <Toggle name="has_iso17025_lab"       value={form.has_iso17025_lab}       onChange={set} label="Laboratório ISO 17025 identificado?" />
        <Toggle name="heavy_metals_documented" value={form.heavy_metals_documented} onChange={set} label="Metais pesados documentados?" />
      </div>
    </>
  );
}

function StepCarbono({ form, set }) {
  return (
    <>
      <div style={{ marginBottom: 20 }}>
        <Toggle name="has_lca" value={form.has_lca} onChange={set} label="LCA (Life Cycle Assessment) iniciada ou disponível?" />
        {form.has_lca ? (
          <KnownValueField
            valueName="lca_emission_factor_tco2_t"
            label="Intensidade de emissões do processo (LCA)"
            help="Total de emissões do ciclo de vida por tonelada de biochar produzido."
            defaultText="0.28 tCO₂e/t (referência bibliográfica resíduos agrícolas, pirólise média)"
            unit="tCO₂e/t biochar" placeholder="Ex: 0.18" form={form} set={set}
          />
        ) : (
          <div style={{ padding: "8px 12px", background: "#fffbeb", border: "1px solid #fde68a", borderRadius: 6, fontSize: 12, color: "#92400e", marginLeft: 50 }}>
            ⚠️ Sem LCA: Puro.Earth penalizada (cap 45% em Contabilidade de Carbono). Isometric e Verra aceitam LCA futura.
          </div>
        )}
      </div>

      <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: "4px 16px" }}>
        <Toggle name="has_system_boundary"       value={form.has_system_boundary}       onChange={set} label="Fronteira do sistema definida?" />
        <Toggle name="has_baseline"              value={form.has_baseline}              onChange={set} label="Cenário baseline documentado?" />
        <Toggle name="has_baseline_fate_evidence" value={form.has_baseline_fate_evidence} onChange={set} label="Evidência do destino do feedstock sem o projeto?" />
        <Toggle name="has_leakage_assessment"    value={form.has_leakage_assessment}    onChange={set} label="Avaliação de leakage realizada?" />
        <Toggle name="has_uncertainty_analysis"  value={form.has_uncertainty_analysis}  onChange={set} label="Análise de incerteza documentada?" />
        <Toggle name="has_reversal_risk_assessment" value={form.has_reversal_risk_assessment} onChange={set} label="Avaliação de risco de reversão?" />
      </div>

      <Field label="Opção de durabilidade" help="Isometric e Puro exigem seleção explícita (200 ou 1000 anos)." style={{ marginTop: 8 }}>
        <SelectInput name="durability_option" value={form.durability_option} onChange={set} options={[
          { value: "200_years",  label: "200 anos (padrão mais comum)" },
          { value: "1000_years", label: "1000 anos (maior crédito potencial)" },
          { value: "not_stated", label: "Ainda não definido" },
        ]} />
      </Field>

      <KnownValueField
        valueName="transport_distance_km"
        label="Distância de transporte (round-trip)"
        help="Feedstock → planta + planta → aplicação. Relevante para Verra: > 200km aciona CDM TOOL12."
        defaultText="≤ 200 km assumido → leakage de transporte = zero na Verra"
        unit="km" placeholder="Ex: 80" form={form} set={set}
      />

      <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: "4px 16px", marginTop: 8 }}>
        <Toggle name="has_soil_temp_method" value={form.has_soil_temp_method} onChange={set} label="Método de temperatura do solo definido?" />
      </div>
    </>
  );
}

function StepAdicionalidade({ form, set }) {
  return (
    <>
      <Toggle name="has_financial_additionality" value={form.has_financial_additionality} onChange={set}
        label="Análise de adicionalidade financeira realizada?" />

      <Field label="Método de adicionalidade" style={{ marginTop: 8 }}>
        <SelectInput name="additionality_method" value={form.additionality_method} onChange={set} options={[
          { value: "irr_npv",       label: "Análise de TIR/VPL (IRR/NPV)" },
          { value: "cost_analysis", label: "Análise de custo incremental" },
          { value: "barriers",      label: "Análise de barreiras" },
          { value: "none",          label: "Nenhuma / ainda não realizada" },
        ]} />
      </Field>

      {form.additionality_method === "irr_npv" && (
        <KnownValueField
          valueName="irr_without_carbon"
          label="TIR do projeto sem receita de carbono"
          help="Se TIR < custo de capital setorial → adicionalidade financeira demonstrada."
          defaultText="Não calculada — adicionalidade financeira não verificável pelo engine"
          unit="%" placeholder="Ex: 8.5" form={form} set={set}
        />
      )}

      <Field label="Caminho Verra VT0008" help="Específico para Verra VCS — outros padrões usam abordagens diferentes.">
        <SelectInput name="vt0008_path" value={form.vt0008_path} onChange={set} options={[
          { value: "investment_comparison", label: "Option 1 — Comparação de investimento (IRR/VPL)" },
          { value: "benchmark",             label: "Option 2 — Análise de benchmark setorial" },
          { value: "not_stated",            label: "Não aplicável / não definido" },
        ]} />
      </Field>

      <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: "4px 16px" }}>
        <Toggle name="has_regulatory_additionality" value={form.has_regulatory_additionality} onChange={set} label="Projeto não exigido por lei?" />
        <Toggle name="is_first_of_its_kind"         value={form.is_first_of_its_kind}         onChange={set} label="Projeto pioneiro / first-of-its-kind?" />
        <Toggle name="has_common_practice_evidence" value={form.has_common_practice_evidence} onChange={set} label="Evidência de que não é prática comum?" />
      </div>

      {form.is_first_of_its_kind && (
        <div style={{ marginTop: 8, padding: "10px 14px", background: "#fffbeb", borderRadius: 8, border: "1px solid #fde68a", fontSize: 12, color: "#92400e" }}>
          ⚠️ <strong>Puro.Earth Clar. 005 ADD:</strong> alegar first-of-its-kind como isenção de adicionalidade financeira é bloqueado. O projeto ainda precisa demonstrar adicionalidade por outra via.
        </div>
      )}
    </>
  );
}

function StepMonitoramento({ form, set }) {
  return (
    <>
      <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: "4px 16px" }}>
        <Toggle name="has_monitoring_table"       value={form.has_monitoring_table}       onChange={set} label="Tabela de parâmetros de monitoramento?" />
        <Toggle name="has_data_storage_plan"      value={form.has_data_storage_plan}      onChange={set} label="Plano de armazenamento de dados?" />
        <Toggle name="has_continuous_weighing"    value={form.has_continuous_weighing}    onChange={set} label="Pesagem contínua do biochar?" />
        <Toggle name="has_fc_lab_analysis"        value={form.has_fc_lab_analysis}        onChange={set} label="Análise laboratorial de carbono orgânico (FCp)?" />
        <Toggle name="has_chain_of_custody"       value={form.has_chain_of_custody}       onChange={set} label="Rastreabilidade feedstock → aplicação?" />
        <Toggle name="has_application_coordinates" value={form.has_application_coordinates} onChange={set} label="Coordenadas dos locais de aplicação?" />
        <Toggle name="has_offsite_backup"         value={form.has_offsite_backup}         onChange={set} label="Backup eletrônico offsite dos dados?" />
      </div>

      <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: 16, marginTop: 12 }}>
        <KnownValueField
          valueName="data_retention_years"
          label="Período de retenção de dados"
          defaultText="Não definido — Verra exige ≥ 2 anos pós-crédito"
          unit="anos" placeholder="Ex: 3" form={form} set={set}
        />
        <Field label="Método de amostragem do biochar">
          <SelectInput name="sampling_method" value={form.sampling_method} onChange={set} options={[
            { value: "method_a",      label: "Método A — amostra a cada lote" },
            { value: "method_b",      label: "Método B — 1 a cada 10 lotes" },
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
      <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: "4px 16px" }}>
        <Toggle name="has_env_compliance"        value={form.has_env_compliance}        onChange={set} label="Conformidade ambiental documentada?" />
        <Toggle name="has_no_net_env_harm"       value={form.has_no_net_env_harm}       onChange={set} label="Sem dano ambiental líquido demonstrado?" />
        <Toggle name="has_no_net_social_harm"    value={form.has_no_net_social_harm}    onChange={set} label="Sem dano social líquido demonstrado?" />
        <Toggle name="has_stakeholder_consultation" value={form.has_stakeholder_consultation} onChange={set} label="Consulta a stakeholders?" />
        <Toggle name="has_grievance_mechanism"   value={form.has_grievance_mechanism}   onChange={set} label="Mecanismo de queixas?" />
        <Toggle name="has_sdg_reporting"         value={form.has_sdg_reporting}         onChange={set} label="Alinhamento com ODS (SDG)?" />
        <Toggle name="has_adaptive_management"   value={form.has_adaptive_management}   onChange={set} label="Plano de gestão adaptativa?" />
        <Toggle name="has_pollution_prevention"  value={form.has_pollution_prevention}  onChange={set} label="Prevenção de poluição (PAH, metais)?" />
      </div>

      {form.has_adaptive_management && (
        <KnownValueField
          valueName="adaptive_management_triggers"
          label="Número de gatilhos de gestão adaptativa documentados"
          help="Puro.Earth exige ≥ 4 gatilhos explícitos."
          defaultText="Não definido — Puro.Earth: parcial se < 4"
          unit="gatilhos" placeholder="Ex: 4" form={form} set={set}
        />
      )}

      {form.has_sdg_reporting && (
        <div style={{ marginTop: 4 }}>
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

// ── Validação por passo ───────────────────────────────────────────────────────
function validateStep(step, form) {
  const errors = {};
  const req = REQUIRED_BY_STEP[step] || [];
  for (const field of req) {
    if (!form[field] || form[field] === "" || form[field] === "not_stated") {
      errors[field] = "Campo obrigatório";
    }
  }
  return errors;
}

// ── Resultados ────────────────────────────────────────────────────────────────
function ResultsView({ result, onReset, projectId }) {
  const { results, recommendation, reasoning } = result;
  const [chosen, setChosen] = useState(recommendation);
  const methods = Object.entries(results).sort((a, b) => b[1].overall - a[1].overall);

  return (
    <div style={{ maxWidth: 920, margin: "0 auto", padding: "0 24px 60px" }}>
      <div style={{ textAlign: "center", marginBottom: 36 }}>
        <h1 style={{ fontSize: 24, fontWeight: 800, color: "#0f172a", margin: "0 0 8px" }}>
          Fit Metodológico — Resultado Preliminar
        </h1>
        <p style={{ color: "#64748b", fontSize: 13 }}>
          Baseado nos dados autodeclarados. Não substitui auditoria com PDD completo.
        </p>
      </div>

      {/* Recomendação */}
      <div style={{ background: "#eff6ff", border: "2px solid #3b82f6", borderRadius: 12, padding: "18px 22px", marginBottom: 28 }}>
        <div style={{ fontSize: 11, fontWeight: 700, color: "#1e40af", textTransform: "uppercase", letterSpacing: 1, marginBottom: 6 }}>
          Metodologia Recomendada
        </div>
        <div style={{ fontSize: 20, fontWeight: 800, color: "#1e40af", marginBottom: 8 }}>
          {METHOD_LABEL[recommendation]}
        </div>
        <p style={{ fontSize: 13, color: "#334155", margin: 0, lineHeight: 1.6 }}>
          {reasoning.replace(/\*\*(.*?)\*\*/g, (_, t) => t)}
        </p>
      </div>

      {/* Cards de metodologia */}
      <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fit, minmax(260px, 1fr))", gap: 14, marginBottom: 28 }}>
        {methods.map(([method, data]) => {
          const isChosen = method === chosen;
          const isRec = method === recommendation;
          return (
            <div key={method} onClick={() => setChosen(method)} style={{
              background: "#fff", borderRadius: 12, padding: "18px 18px 14px",
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
              <div style={{ fontWeight: 700, fontSize: 13, color: METHOD_COLOR[method], marginBottom: 4 }}>
                {data.label}
              </div>
              <div style={{ display: "flex", alignItems: "baseline", gap: 8, marginBottom: 12 }}>
                <span style={{ fontSize: 32, fontWeight: 900, color: GRADE_COLOR[data.grade] }}>{data.grade}</span>
                <span style={{ fontSize: 18, fontWeight: 700, color: "#475569" }}>{data.overall}%</span>
              </div>
              {Object.entries(data.dimensions || {}).map(([dim, score]) => (
                <div key={dim} style={{ marginBottom: 4 }}>
                  <div style={{ display: "flex", justifyContent: "space-between", fontSize: 11, color: "#64748b", marginBottom: 2 }}>
                    <span>{DIM_LABEL[dim] || dim}</span>
                    <span style={{ fontWeight: 600 }}>{score !== null ? `${Math.round(score)}%` : "—"}</span>
                  </div>
                  <div style={{ height: 3, background: "#e2e8f0", borderRadius: 2 }}>
                    <div style={{
                      height: 3, borderRadius: 2, width: `${Math.max(0, score || 0)}%`,
                      background: score >= 70 ? "#22c55e" : score >= 45 ? "#f59e0b" : "#ef4444",
                      transition: "width .3s",
                    }} />
                  </div>
                </div>
              ))}
              <div style={{ fontSize: 11, color: "#94a3b8", marginTop: 8 }}>
                {data.compliant}/{data.total} requisitos conformes
              </div>
            </div>
          );
        })}
      </div>

      {/* Top Gaps */}
      {results[chosen]?.top_gaps?.length > 0 && (
        <div style={{ marginBottom: 28 }}>
          <h2 style={{ fontSize: 15, fontWeight: 700, color: "#1e293b", marginBottom: 14 }}>
            Principais gaps — {METHOD_LABEL[chosen]}
          </h2>
          {results[chosen].top_gaps.map((gap, i) => (
            <div key={i} style={{
              background: "#fff", border: "1px solid #e2e8f0", borderRadius: 8,
              padding: "10px 14px", marginBottom: 8, borderLeft: "3px solid #f59e0b",
            }}>
              <div style={{ fontWeight: 600, fontSize: 12, color: "#0f172a", marginBottom: 3 }}>
                {gap.requirement_name || gap.title}
              </div>
              <div style={{ fontSize: 12, color: "#64748b", marginBottom: 3 }}>{gap.gap || "—"}</div>
              {gap.recommendation && (
                <div style={{ fontSize: 11, color: "#0369a1", fontStyle: "italic" }}>
                  → {gap.recommendation}
                </div>
              )}
            </div>
          ))}
        </div>
      )}

      {/* Ações */}
      <div style={{ display: "flex", gap: 12, flexWrap: "wrap" }}>
        <button
          onClick={() => alert(`PDD Draft para ${METHOD_LABEL[chosen]} — em breve!`)}
          style={{
            padding: "11px 22px", background: METHOD_COLOR[chosen], color: "#fff",
            border: "none", borderRadius: 8, fontWeight: 700, fontSize: 14, cursor: "pointer",
          }}>
          Gerar PDD Draft — {METHOD_LABEL[chosen]}
        </button>
        {projectId && (
          <a href={`/projects/${projectId}`} style={{
            padding: "11px 22px", background: "#fff", color: "#1e40af",
            border: "2px solid #1e40af", borderRadius: 8, fontWeight: 700,
            fontSize: 14, textDecoration: "none",
          }}>Ver Projeto</a>
        )}
        <button onClick={onReset} style={{
          padding: "11px 22px", background: "#f1f5f9", color: "#475569",
          border: "1px solid #cbd5e1", borderRadius: 8, fontWeight: 600,
          fontSize: 14, cursor: "pointer",
        }}>Nova Análise</button>
      </div>

      <p style={{ fontSize: 11, color: "#94a3b8", marginTop: 20 }}>
        ⚠️ Avaliação preliminar baseada em dados autodeclarados. Scores podem variar significativamente após auditoria com PDD completo.
      </p>
    </div>
  );
}

// ── Estado inicial do formulário ──────────────────────────────────────────────
const EMPTY = {
  // Projeto
  project_name: "", project_country: "brazil", storage_pathway: "soil",
  biochar_t_dry_year: null, estimated_credits_tco2: null,
  // Feedstock
  feedstock_type: "", is_forest_biomass: false, is_purpose_grown: false,
  feedstock_imported: false, uses_mixed_waste: false, uses_coal_ash: false,
  from_land_clearing: false,
  has_fsc_certification: false, has_pefc_certification: false,
  has_isae3000_dossier: false, has_government_mgmt_plan: false,
  // Sustentabilidade por tipo
  high_residue_removal: false, has_soil_health_docs: false, // agrícola
  residue_volume_increased: false, // processamento alimentar
  // Produção
  pyrolysis_temp_c: null, verra_tech_class: "",
  has_continuous_temp_monitoring: false, has_pyrolysis_gas_recovery: false,
  has_engineering_diagram: false, has_maintenance_plan: false,
  is_greenfield_facility: true, reactor_type: "",
  // Biochar
  h_c_ratio: null, o_c_ratio: null, pah_value: null, pcb_value: null,
  quality_standard: "not_stated", has_iso17025_lab: false, heavy_metals_documented: false,
  // Carbono
  has_lca: false, lca_emission_factor_tco2_t: null,
  has_system_boundary: false, has_baseline: false, has_baseline_fate_evidence: false,
  has_leakage_assessment: false, has_uncertainty_analysis: false,
  durability_option: "not_stated", has_soil_temp_method: false,
  has_reversal_risk_assessment: false, transport_distance_km: null,
  // Adicionalidade
  has_financial_additionality: false, additionality_method: "none",
  irr_without_carbon: null, vt0008_path: "not_stated",
  has_regulatory_additionality: false, is_first_of_its_kind: false,
  has_common_practice_evidence: false,
  // Monitoramento
  has_monitoring_table: false, has_data_storage_plan: false,
  has_continuous_weighing: false, has_fc_lab_analysis: false,
  has_chain_of_custody: false, has_application_coordinates: false,
  has_offsite_backup: false, data_retention_years: null,
  sampling_method: "not_described",
  // Social
  has_env_compliance: false, has_no_net_env_harm: false,
  has_no_net_social_harm: false, has_stakeholder_consultation: false,
  has_grievance_mechanism: false, has_sdg_reporting: false,
  has_adaptive_management: false, has_pollution_prevention: false,
  adaptive_management_triggers: 0, has_puro_sdg_template: false,
  // Aplicação
  soil_application: true,
};

// ── Página principal ──────────────────────────────────────────────────────────
export default function PinGeneratorPage() {
  const navigate = useNavigate();
  const [step, setStep]       = useState(0);
  const [form, setForm]       = useState(EMPTY);
  const [errors, setErrors]   = useState({});
  const [loading, setLoading] = useState(false);
  const [result, setResult]   = useState(null);
  const [projectId, setProjectId] = useState(null);
  const [apiError, setApiError]   = useState(null);

  const set = useCallback((name, value) => setForm(f => ({ ...f, [name]: value })), []);

  const tryNext = () => {
    const errs = validateStep(step, form);
    setErrors(errs);
    if (Object.keys(errs).length === 0) setStep(s => s + 1);
  };

  const handleSubmit = async () => {
    const errs = validateStep(step, form);
    setErrors(errs);
    if (Object.keys(errs).length > 0) return;

    setLoading(true);
    setApiError(null);
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
      setApiError(e.message);
    } finally {
      setLoading(false);
    }
  };

  if (result) {
    return (
      <ResultsView
        result={result} projectId={projectId}
        onReset={() => { setResult(null); setStep(0); setForm(EMPTY); setProjectId(null); }}
      />
    );
  }

  const StepComp = STEP_COMPONENTS[step];
  const isLast = step === STEPS.length - 1;

  return (
    <div style={{ minHeight: "100vh", background: "#f8fafc" }}>
      {/* Header */}
      <div style={{ background: "#1e40af", padding: "14px 24px", display: "flex", alignItems: "center", gap: 14 }}>
        <button onClick={() => navigate("/")} style={{ background: "transparent", border: "none", color: "#93c5fd", cursor: "pointer", fontSize: 13 }}>
          ← Voltar
        </button>
        <div>
          <div style={{ color: "#fff", fontWeight: 800, fontSize: 15 }}>Novo Projeto — Análise Preliminar</div>
          <div style={{ color: "#93c5fd", fontSize: 11 }}>Project Idea Note + Fit Metodológico (sem PDD)</div>
        </div>
      </div>

      {/* Progress tabs */}
      <div style={{ background: "#fff", borderBottom: "1px solid #e2e8f0", padding: "0 24px", overflowX: "auto" }}>
        <div style={{ display: "flex", gap: 0, minWidth: "max-content" }}>
          {STEPS.map((s, i) => (
            <button key={s.id} onClick={() => i < step && setStep(i)} style={{
              padding: "12px 14px", border: "none", background: "transparent",
              borderBottom: `3px solid ${i === step ? "#1e40af" : "transparent"}`,
              color: i === step ? "#1e40af" : i < step ? "#22c55e" : "#94a3b8",
              fontWeight: i === step ? 700 : 500, fontSize: 12,
              cursor: i < step ? "pointer" : "default", whiteSpace: "nowrap",
              display: "flex", alignItems: "center", gap: 5,
            }}>
              <span>{i < step ? "✓" : s.icon}</span>
              <span>{s.label}</span>
            </button>
          ))}
        </div>
      </div>

      {/* Barra de progresso */}
      <div style={{ height: 3, background: "#e2e8f0" }}>
        <div style={{
          height: 3, background: "#1e40af",
          width: `${((step + 1) / STEPS.length) * 100}%`,
          transition: "width .3s",
        }} />
      </div>

      {/* Form */}
      <div style={{ maxWidth: 820, margin: "28px auto", padding: "0 24px" }}>
        <div style={{ background: "#fff", borderRadius: 12, border: "1px solid #e2e8f0", padding: "26px 30px" }}>
          <div style={{ display: "flex", justifyContent: "space-between", alignItems: "baseline", marginBottom: 18 }}>
            <div>
              <h2 style={{ fontSize: 17, fontWeight: 700, color: "#0f172a", margin: 0 }}>
                {STEPS[step].icon} {STEPS[step].label}
              </h2>
              <p style={{ fontSize: 12, color: "#64748b", margin: "4px 0 0" }}>
                Passo {step + 1} de {STEPS.length} — campos com * são obrigatórios; demais assumem valores conservadores se em branco.
              </p>
            </div>
          </div>

          <StepComp form={form} set={set} errors={errors} />

          {apiError && (
            <div style={{ marginTop: 14, padding: "10px 14px", background: "#fef2f2", border: "1px solid #fca5a5", borderRadius: 6, color: "#b91c1c", fontSize: 13 }}>
              {apiError}
            </div>
          )}

          <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginTop: 28, borderTop: "1px solid #f1f5f9", paddingTop: 20 }}>
            <button onClick={() => { setErrors({}); setStep(s => s - 1); }}
              disabled={step === 0}
              style={{
                padding: "9px 18px", border: "1px solid #cbd5e1", borderRadius: 8,
                background: "#fff", color: "#475569", fontWeight: 600, fontSize: 13,
                cursor: step === 0 ? "not-allowed" : "pointer", opacity: step === 0 ? 0.4 : 1,
              }}>
              ← Anterior
            </button>

            <span style={{ fontSize: 12, color: "#94a3b8" }}>{step + 1} / {STEPS.length}</span>

            {isLast ? (
              <button onClick={handleSubmit} disabled={loading}
                style={{
                  padding: "9px 24px", background: "#1e40af", color: "#fff",
                  border: "none", borderRadius: 8, fontWeight: 700, fontSize: 14,
                  cursor: loading ? "wait" : "pointer",
                }}>
                {loading ? "Analisando..." : "Analisar → Fit Metodológico"}
              </button>
            ) : (
              <button onClick={tryNext}
                style={{
                  padding: "9px 22px", background: "#1e40af", color: "#fff",
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
