import streamlit as st 

from app_pages.validation_utils import (
    convert_df_to_csv_bytes,
    convert_json_to_bytes,
    docx_from_text,
    pdf_from_text,
    pdf_from_text_branded,
    matrix_to_docx_bytes,
    matrix_to_pdf_bytes,
    build_full_audit_text,
    build_full_eligibility_dossier_text,
    build_executive_dossier_text,
    normalize_result_language,
)


def render_downloads_tab(
    run_id,
    project_name,
    summary,
    df,
    last_full_audit_results,
    last_full_audit_trails,
):
    full_audit_text = build_full_audit_text(summary, last_full_audit_results)
    full_audit_docx = docx_from_text("CO2mply | Audit Summary", full_audit_text)
    full_audit_pdf = pdf_from_text_branded(
        "CO2mply | Audit Summary",
        full_audit_text,
        brand_name="CO2mply",
    )

    normalized_results_en = normalize_result_language(
        last_full_audit_results,
        lang="en",
    )

    eligibility_dossier_text = build_executive_dossier_text(
        project_name,
        summary,
        normalized_results_en,
        lang="en",
    )

    eligibility_docx = docx_from_text(
        "CO2mply | Eligibility Dossier",
        eligibility_dossier_text,
    )
    eligibility_pdf = pdf_from_text_branded(
        "CO2mply | Eligibility Dossier",
        eligibility_dossier_text,
        brand_name="CO2mply",
    )

    matrix_docx = matrix_to_docx_bytes(df, "CO2mply | Compliance Matrix")
    matrix_pdf = matrix_to_pdf_bytes(df, "CO2mply | Compliance Matrix")
    csv_bytes = convert_df_to_csv_bytes(df)
    json_bytes = convert_json_to_bytes(
        {
            "run_id": run_id,
            "summary": summary,
            "results": last_full_audit_results,
            "trails": last_full_audit_trails,
        }
    )

    d1, d2, d3 = st.columns(3)

    with d1:
        st.download_button(
            "Audit summary (.md)",
            data=full_audit_text,
            file_name=f"co2mply_audit_summary_{run_id}.md",
            mime="text/markdown",
            width="stretch",
        )
        st.download_button(
            "Eligibility dossier (.md)",
            data=eligibility_dossier_text,
            file_name=f"co2mply_eligibility_dossier_{run_id}.md",
            mime="text/markdown",
            width="stretch",
        )
        st.download_button(
            "Compliance matrix (.csv)",
            data=csv_bytes,
            file_name=f"co2mply_compliance_matrix_{run_id}.csv",
            mime="text/csv",
            width="stretch",
        )

    with d2:
        st.download_button(
            "Audit summary (.docx)",
            data=full_audit_docx,
            file_name=f"co2mply_audit_summary_{run_id}.docx",
            mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
            width="stretch",
        )
        st.download_button(
            "Eligibility dossier (.docx)",
            data=eligibility_docx,
            file_name=f"co2mply_eligibility_dossier_{run_id}.docx",
            mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
            width="stretch",
        )
        st.download_button(
            "Compliance matrix (.docx)",
            data=matrix_docx,
            file_name=f"co2mply_compliance_matrix_{run_id}.docx",
            mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
            width="stretch",
        )

    with d3:
        st.download_button(
            "Audit summary (.pdf)",
            data=full_audit_pdf,
            file_name=f"co2mply_audit_summary_{run_id}.pdf",
            mime="application/pdf",
            width="stretch",
        )
        st.download_button(
            "Eligibility dossier (.pdf)",
            data=eligibility_pdf,
            file_name=f"co2mply_eligibility_dossier_{run_id}.pdf",
            mime="application/pdf",
            width="stretch",
        )
        st.download_button(
            "Compliance matrix (.pdf)",
            data=matrix_pdf,
            file_name=f"co2mply_compliance_matrix_{run_id}.pdf",
            mime="application/pdf",
            width="stretch",
        )
        st.download_button(
            "Trace (.json)",
            data=json_bytes,
            file_name=f"co2mply_audit_{run_id}.json",
            mime="application/json",
            width="stretch",
        )
        
def render_trails_section(trails):
    st.markdown("#### Trilha detalhada")

    for i, trail in enumerate(trails, start=1):
        with st.expander(f"[{i}] {trail.get('module', '')} | {trail.get('analysis_label', '')}"):
            st.markdown("**Queries do projeto**")
            st.code(trail.get("project_query", ""), language="text")

            st.markdown("**Queries da metodologia**")
            st.code(trail.get("methodology_query", ""), language="text")

            st.markdown("**Trechos do projeto**")
            st.code(trail.get("project_context", ""), language="text")

            st.markdown("**Trechos da metodologia**")
            st.code(trail.get("methodology_context", ""), language="text")

            st.markdown("**Resposta bruta do modelo**")
            st.code(trail.get("model_response_raw", ""), language="json")

            st.markdown("**Resultado interpretado**")
            st.json(trail.get("parsed_result", {}))

def render():
    st.warning("Validation page ainda em transição. Usando renderer legado.")

    legacy_renderer = st.session_state.get("_validation_legacy_renderer")

    if callable(legacy_renderer):
        legacy_renderer()
    else:
        st.error("Renderer legado não encontrado.")

def render_history_tab(history, lang, t, theme, safe_str, badge_html):
    st.markdown(f"#### {t(lang, 'history')}")

    if not history:
        st.info("Nenhuma execução registrada nesta sessão.")
    else:
        for item in history:
            html_parts = [
                '<div class="auditoria-card">',
                '<div style="display:flex;justify-content:space-between;gap:1rem;flex-wrap:wrap;">',
                '<div>',
                f'<div style="font-weight:700;color:{theme["primary"]};">{safe_str(item["project_name"])}</div>',
                f'<div class="auditoria-small">{safe_str(item["timestamp"])}</div>',
                '</div>',
                f'<div class="auditoria-small">run_id: {safe_str(item["run_id"])}</div>',
                '</div>',
                '<div style="margin-top:0.5rem;">',
                badge_html(safe_str(item["execution_mode"]), "info"),
                badge_html(f"score {item['overall_score']}%", "success"),
                badge_html(f"conf {item['overall_confidence']}%", "warning"),
                badge_html(f"US$ {item['estimated_cost']:.3f}", "danger"),
                '</div>',
                '<div class="auditoria-small" style="margin-top:0.5rem;">',
                f'módulos: {", ".join(item["modules"])}',
                '</div>',
                '</div>',
            ]
            html = "".join(html_parts)
            st.markdown(html, unsafe_allow_html=True)
def render_executive_summary(summary):
    score = summary.get("overall_score", 0)
    confidence = summary.get("overall_confidence", 0)
    status_counts = summary.get("status_counts", {})
    risk_counts = summary.get("risk_counts", {})

    # =========================
    # CLASSIFICAÇÃO GERAL
    # =========================
    if score >= 75:
        headline = "Projeto tecnicamente sólido e próximo de conformidade plena."
    elif score >= 55:
        headline = "Projeto tecnicamente consistente, com lacunas relevantes para certificação."
    elif score >= 40:
        headline = "Projeto parcialmente estruturado, com lacunas críticas de conformidade."
    else:
        headline = "Projeto ainda não atende aos requisitos mínimos de certificação."

    # =========================
    # RISCO PRINCIPAL
    # =========================
    high_risk = risk_counts.get("alto", 0)

    if high_risk > 0:
        risk_msg = f"Foram identificados {high_risk} requisitos com risco alto, indicando exposição significativa para auditoria."
    else:
        risk_msg = "Não foram identificados riscos críticos imediatos."

    # =========================
    # CONFIANÇA DA ANÁLISE
    # =========================
    if confidence >= 70:
        confidence_msg = "A análise apresenta alta robustez documental e consistência."
    elif confidence >= 50:
        confidence_msg = "A análise apresenta confiabilidade moderada, com base documental parcial."
    else:
        confidence_msg = "A análise apresenta baixa robustez documental, com necessidade de evidências adicionais."

    # =========================
    # RECOMENDAÇÃO PRINCIPAL
    # =========================
    recommendation = (
        "Priorizar a consolidação de evidências auditáveis (laudos, rastreabilidade por lote, documentação formal) "
        "e o alinhamento explícito com os critérios da metodologia."
    )

    # =========================
    # UI
    # =========================
    st.markdown("### 🧭 Executive Summary")

    with st.container(border=True):

        # Headline
        st.markdown(f"#### {headline}")

        # Métricas principais
        m1, m2 = st.columns(2)
        with m1:
            st.metric("Score geral", f"{score}%")
        with m2:
            st.metric("Confiança", f"{confidence}%")

        st.divider()

        # Diagnóstico
        st.markdown("**Diagnóstico da análise**")
        st.write(confidence_msg)

        # Risco
        st.markdown("**Risco identificado**")
        st.write(risk_msg)

        st.divider()

        # Próximo passo
        st.markdown("**Próxima ação recomendada**")
        st.write(recommendation)
