from openai import OpenAI
import streamlit as st

from schemas.project_schema import get_demo_project_data
from versioning.methodology_manager import get_requirements
from engine.requirement_logic import run_engine

# Initialize the OpenAI client
client = OpenAI(api_key=st.secrets["OPENAI_API_KEY"])

st.title("Vector Store Manager")

if st.button("Listar Vector Stores"):
    try:
        with st.spinner("Loading vector stores..."):
            stores = client.vector_stores.list()
        
        if stores.data:
            st.success(f"Found {len(stores.data)} vector store(s)")
            for s in stores.data:
                col1, col2 = st.columns(2)
                with col1:
                    st.write("**ID:**", s.id)
                with col2:
                    st.write("**Name:**", s.name)
        else:
            st.info("No vector stores found")
    
    except Exception as e:
        st.error(f"Error listing vector stores: {str(e)}")

# =========================================================
# TESTE ENGINE V2 (TEMPORÁRIO)
# =========================================================

import pandas as pd

with st.expander("🧪 Teste Engine V2"):
    if st.button("Rodar teste V2"):
        try:
            project_data = get_demo_project_data()
            requirements = get_requirements()
            results = run_engine(project_data, requirements)

            st.success("Engine executada com sucesso")

            df_results = pd.DataFrame(results)
            st.dataframe(df_results, hide_index=True, width="stretch")

        except Exception as e:
            st.error(f"Erro ao rodar engine: {e}")
