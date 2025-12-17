import streamlit as st
from rag import RAGPipeline
import os
import tempfile

st.set_page_config(page_title="GenAI Document Assistant", page_icon="🚀", layout="wide")

# Initialize RAG pipeline
@st.cache_resource
def get_rag_pipeline():
    return RAGPipeline()

rag = get_rag_pipeline()

# UI
st.title("GenAI Document Assistant")
st.markdown("Upload documents and ask questions using RAG (BERT + FAISS + Groq)")

# Sidebar for document upload
with st.sidebar:
    st.header("Upload Documents")
    uploaded_file = st.file_uploader(
        "Choose a file",
        type=['pdf', 'txt', 'png', 'jpg', 'jpeg'],
        help="Upload PDF, TXT, or image files"
    )
    
    if uploaded_file:
        if st.button("Add to Database"):
            with st.spinner("Processing document..."):
                # Save uploaded file temporarily
                with tempfile.NamedTemporaryFile(delete=False, suffix=os.path.splitext(uploaded_file.name)[1]) as tmp_file:
                    tmp_file.write(uploaded_file.getvalue())
                    tmp_path = tmp_file.name
                
                try:
                    rag.add_document(tmp_path)
                    st.success(f"✓ Added {uploaded_file.name} to database!")
                except Exception as e:
                    st.error(f"Error: {str(e)}")
                finally:
                    os.unlink(tmp_path)
    
    st.divider()
    st.markdown(f"**Documents in DB:** {len(rag.chunks)} chunks")

# Main chat interface
st.header("Ask Questions")

# Initialize chat history
if "messages" not in st.session_state:
    st.session_state.messages = []

# Display chat history
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

# Chat input
if prompt := st.chat_input("Ask a question about your documents..."):
    # Add user message
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)
    
    # Generate response
    with st.chat_message("assistant"):
        with st.spinner("Thinking..."):
            try:
                response = rag.query(prompt)
                st.markdown(response)
                st.session_state.messages.append({"role": "assistant", "content": response})
            except Exception as e:
                error_msg = f"Error: {str(e)}"
                st.error(error_msg)
                st.session_state.messages.append({"role": "assistant", "content": error_msg})

# Clear chat button
if st.session_state.messages:
    if st.button("Clear Chat History"):
        st.session_state.messages = []
        st.rerun()
