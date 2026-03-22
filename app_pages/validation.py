import streamlit as st

from app_pages.validation_utils import (
    convert_df_to_csv_bytes,
    convert_json_to_bytes,
    docx_from_text,
    pdf_from_text,
    matrix_to_docx_bytes,
    matrix_to_pdf_bytes,
    build_full_audit_text,
    build_full_eligibility_dossier_text,
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
    full_audit_docx = docx_from_text("Auditoria Resumida Isometric", full_audit_text)
    full_audit_pdf = pdf_from_text("Auditoria Resumida Isometric", full_audit_text)

    eligibility_dossier_text = build_full_eligibility_dossier_text(
        project_name=project_name,
        summary=summary,
        results=last_full_audit_results,
        trails=last_full_audit_trails,
    )
    eligibility_docx = docx_from_text("Dossiê de Elegibilidade Metodológica", eligibility_dossier_text)
    eligibility_pdf = pdf_from_text("Dossiê de Elegibilidade Metodológica", eligibility_dossier_text)

    matrix_docx = matrix_to_docx_bytes(df, "Matriz de Conformidade Isometric")
    matrix_pdf = matrix_to_pdf_bytes(df, "Matriz de Conformidade Isometric")
    csv_bytes = convert_df_to_csv_bytes(df)
    json_bytes = convert_json_to_bytes({
        "run_id": run_id,
        "summary": summary,
        "results": last_full_audit_results,
        "trails": last_full_audit_trails,
    })

    d1, d2, d3 = st.columns(3)

    with d1:
        st.download_button(
            "Auditoria resumida (.md)",
            data=full_audit_text,
            file_name=f"auditoria_resumida_isometric_{run_id}.md",
            mime="text/markdown",
            use_container_width=True
        )
        st.download_button(
            "Dossiê (.md)",
            data=eligibility_dossier_text,
            file_name=f"dossie_elegibilidade_{run_id}.md",
            mime="text/markdown",
            use_container_width=True
        )
        st.download_button(
            "Matriz (.csv)",
            data=csv_bytes,
            file_name=f"matriz_conformidade_isometric_{run_id}.csv",
            mime="text/csv",
            use_container_width=True
        )

    with d2:
        st.download_button(
            "Auditoria resumida (.docx)",
            data=full_audit_docx,
            file_name=f"auditoria_resumida_isometric_{run_id}.docx",
            mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
            use_container_width=True
        )
        st.download_button(
            "Dossiê (.docx)",
            data=eligibility_docx,
            file_name=f"dossie_elegibilidade_{run_id}.docx",
            mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
            use_container_width=True
        )
        st.download_button(
            "Matriz (.docx)",
            data=matrix_docx,
            file_name=f"matriz_conformidade_isometric_{run_id}.docx",
            mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
            use_container_width=True
        )

    with d3:
        st.download_button(
            "Auditoria resumida (.pdf)",
            data=full_audit_pdf,
            file_name=f"auditoria_resumida_isometric_{run_id}.pdf",
            mime="application/pdf",
            use_container_width=True
        )
        st.download_button(
            "Dossiê (.pdf)",
            data=eligibility_pdf,
            file_name=f"dossie_elegibilidade_{run_id}.pdf",
            mime="application/pdf",
            use_container_width=True
        )
        st.download_button(
            "Matriz (.pdf)",
            data=matrix_pdf,
            file_name=f"matriz_conformidade_isometric_{run_id}.pdf",
            mime="application/pdf",
            use_container_width=True
        )
        st.download_button(
            "Trilha (.json)",
            data=json_bytes,
            file_name=f"auditoria_isometric_{run_id}.json",
            mime="application/json",
            use_container_width=True
        )
