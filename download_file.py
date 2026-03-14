# =========================================================
# DOWNLOADS
# =========================================================

st.markdown("---")
st.subheader("Dossiê principal")

if (
    st.session_state.last_answer_text
    or st.session_state.last_audit_json
    or st.session_state.last_report_text
    or st.session_state.last_compliance_matrix_json
    or st.session_state.last_deep_dive_text
):
    professional_docx = build_professional_audit_docx(
        question=st.session_state.last_user_question,
        answer_text=st.session_state.last_answer_text,
        audit_json=st.session_state.last_audit_json,
        report_text=st.session_state.last_report_text,
        matrix_json=st.session_state.last_compliance_matrix_json,
        deep_dive_text=st.session_state.last_deep_dive_text,
        sources=st.session_state.last_sources_all,
        logo_path=LOGO_PATH
    )

    st.download_button(
        "Baixar dossiê profissional (.docx)",
        data=professional_docx,
        file_name="aia_dossie_auditoria_astracarbon.docx",
        mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
        use_container_width=True
    )

st.markdown("---")
st.subheader("Downloads auxiliares")

# Resposta
if st.session_state.last_answer_text:
    answer_docx = docx_from_text("Resposta da AiA", st.session_state.last_answer_text)
    answer_pdf = pdf_from_text("Resposta da AiA", st.session_state.last_answer_text)

    c1, c2, c3 = st.columns(3)
    with c1:
        st.download_button(
            "Resposta (.md)",
            data=st.session_state.last_answer_text,
            file_name="aia_resposta.md",
            mime="text/markdown",
            use_container_width=True
        )
    with c2:
        st.download_button(
            "Resposta (.docx)",
            data=answer_docx,
            file_name="aia_resposta.docx",
            mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
            use_container_width=True
        )
    with c3:
        st.download_button(
            "Resposta (.pdf)",
            data=answer_pdf,
            file_name="aia_resposta.pdf",
            mime="application/pdf",
            use_container_width=True
        )

# Fontes
if st.session_state.last_sources_all:
    src_md = export_sources_markdown(st.session_state.last_sources_all)
    src_docx = docx_from_text("Fontes utilizadas", src_md)
    src_pdf = pdf_from_text("Fontes utilizadas", src_md)

    c1, c2, c3 = st.columns(3)
    with c1:
        st.download_button(
            "Fontes (.md)",
            data=src_md,
            file_name="aia_fontes.md",
            mime="text/markdown",
            use_container_width=True
        )
    with c2:
        st.download_button(
            "Fontes (.docx)",
            data=src_docx,
            file_name="aia_fontes.docx",
            mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
            use_container_width=True
        )
    with c3:
        st.download_button(
            "Fontes (.pdf)",
            data=src_pdf,
            file_name="aia_fontes.pdf",
            mime="application/pdf",
            use_container_width=True
        )

# Auditoria
if st.session_state.last_audit_json:
    audit_md = render_audit_json(st.session_state.last_audit_json)
    audit_docx = docx_from_text("Auditoria estruturada", audit_md)
    audit_pdf = pdf_from_text("Auditoria estruturada", audit_md)

    c1, c2, c3, c4 = st.columns(4)
    with c1:
        st.download_button(
            "Auditoria (.json)",
            data=json.dumps(st.session_state.last_audit_json, ensure_ascii=False, indent=2),
            file_name="aia_auditoria.json",
            mime="application/json",
            use_container_width=True
        )
    with c2:
        st.download_button(
            "Auditoria (.md)",
            data=audit_md,
            file_name="aia_auditoria.md",
            mime="text/markdown",
            use_container_width=True
        )
    with c3:
        st.download_button(
            "Auditoria (.docx)",
            data=audit_docx,
            file_name="aia_auditoria.docx",
            mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
            use_container_width=True
        )
    with c4:
        st.download_button(
            "Auditoria (.pdf)",
            data=audit_pdf,
            file_name="aia_auditoria.pdf",
            mime="application/pdf",
            use_container_width=True
        )

# Relatório
if st.session_state.last_report_text:
    report_docx = docx_from_text("Relatório consolidado", st.session_state.last_report_text)
    report_pdf = pdf_from_text("Relatório consolidado", st.session_state.last_report_text)

    c1, c2, c3 = st.columns(3)
    with c1:
        st.download_button(
            "Relatório (.md)",
            data=st.session_state.last_report_text,
            file_name="aia_relatorio.md",
            mime="text/markdown",
            use_container_width=True
        )
    with c2:
        st.download_button(
            "Relatório (.docx)",
            data=report_docx,
            file_name="aia_relatorio.docx",
            mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
            use_container_width=True
        )
    with c3:
        st.download_button(
            "Relatório (.pdf)",
            data=report_pdf,
            file_name="aia_relatorio.pdf",
            mime="application/pdf",
            use_container_width=True
        )

# Matriz
if st.session_state.last_compliance_matrix_json:
    matrix_df = matrix_json_to_dataframe(st.session_state.last_compliance_matrix_json)
    matrix_docx = matrix_to_docx_bytes(matrix_df, "Matriz de conformidade")
    matrix_pdf = matrix_to_pdf_bytes(matrix_df, "Matriz de conformidade")

    c1, c2, c3 = st.columns(3)
    with c1:
        st.download_button(
            "Matriz (.json)",
            data=json.dumps(st.session_state.last_compliance_matrix_json, ensure_ascii=False, indent=2),
            file_name="aia_matriz_conformidade.json",
            mime="application/json",
            use_container_width=True
        )
    with c2:
        st.download_button(
            "Matriz (.docx)",
            data=matrix_docx,
            file_name="aia_matriz_conformidade.docx",
            mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
            use_container_width=True
        )
    with c3:
        st.download_button(
            "Matriz (.pdf)",
            data=matrix_pdf,
            file_name="aia_matriz_conformidade.pdf",
            mime="application/pdf",
            use_container_width=True
        )

# Aprofundamento
if st.session_state.last_deep_dive_text:
    deep_docx = docx_from_text("Aprofundamento técnico", st.session_state.last_deep_dive_text)
    deep_pdf = pdf_from_text("Aprofundamento técnico", st.session_state.last_deep_dive_text)

    c1, c2, c3 = st.columns(3)
    with c1:
        st.download_button(
            "Aprofundamento (.md)",
            data=st.session_state.last_deep_dive_text,
            file_name="aia_aprofundamento.md",
            mime="text/markdown",
            use_container_width=True
        )
    with c2:
        st.download_button(
            "Aprofundamento (.docx)",
            data=deep_docx,
            file_name="aia_aprofundamento.docx",
            mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
            use_container_width=True
        )
    with c3:
        st.download_button(
            "Aprofundamento (.pdf)",
            data=deep_pdf,
            file_name="aia_aprofundamento.pdf",
            mime="application/pdf",
            use_container_width=True
        )