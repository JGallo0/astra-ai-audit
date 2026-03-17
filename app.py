from openai import OpenAI
import streamlit as st

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