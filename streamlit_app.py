import streamlit as st
import requests
import os
from logger_config import setup_logger

logger = setup_logger("streamlit_app")

API_URL = "http://localhost:8000"

st.set_page_config(page_title="RAG Subject Chatbot", layout="wide")

st.title("📚 Document-Based Subject Chatbot")

# Sidebar - Subject Management
st.sidebar.header("Subject Management")

# Create new subject
with st.sidebar.expander("Create New Subject"):
    new_subject_name = st.text_input("Subject Name")
    new_subject_desc = st.text_area("Description")
    if st.button("Create Subject"):
        if new_subject_name:
            logger.info(f"User creating subject: {new_subject_name}")
            response = requests.post(f"{API_URL}/subjects/", json={
                "name": new_subject_name,
                "description": new_subject_desc
            })
            if response.status_code == 200:
                st.sidebar.success("Subject created!")
                st.rerun()
            else:
                logger.error(f"Failed to create subject: {response.json().get('detail')}")
                st.sidebar.error(f"Error: {response.json().get('detail')}")

# List subjects
response = requests.get(f"{API_URL}/subjects/")
if response.status_code == 200:
    subjects = response.json()
    subject_names = {s['name']: s['id'] for s in subjects}
    
    selected_subject_name = st.sidebar.selectbox(
        "Select Subject", 
        options=list(subject_names.keys()) if subject_names else []
    )
    
    if selected_subject_name:
        subject_id = subject_names[selected_subject_name]
        st.sidebar.info(f"Selected: {selected_subject_name}")
        logger.info(f"User selected subject: {selected_subject_name} ({subject_id})")
        
        # Main Content Area
        tab1, tab2 = st.tabs(["💬 Chat", "📄 Upload Documents"])
        
        with tab1:
            st.header(f"Chat with {selected_subject_name}")
            
            # Initialize chat history
            if "messages" not in st.session_state:
                st.session_state.messages = []
            
            # Display chat messages
            for message in st.session_state.messages:
                with st.chat_message(message["role"]):
                    st.markdown(message["content"])

            # Chat input
            if prompt := st.chat_input("Ask a question about the documents..."):
                logger.info(f"User asked question: {prompt}")
                st.session_state.messages.append({"role": "user", "content": prompt})
                with st.chat_message("user"):
                    st.markdown(prompt)

                with st.chat_message("assistant"):
                    with st.spinner("Thinking..."):
                        response = requests.post(
                            f"{API_URL}/subjects/{subject_id}/chat",
                            json={"question": prompt}
                        )
                        
                        if response.status_code == 200:
                            data = response.json()
                            answer = data['answer']
                            sources = data.get('sources', [])
                            
                            st.markdown(answer)
                            if sources:
                                st.caption(f"Sources: {', '.join(sources)}")
                            
                            st.session_state.messages.append({"role": "assistant", "content": answer})
                            st.rerun()
                        else:
                            error_msg = "Error getting response."
                            logger.error(f"Chat error: {response.status_code}")
                            st.error(error_msg)
                            st.session_state.messages.append({"role": "assistant", "content": error_msg})

        with tab2:
            st.header("Upload Documents")
            uploaded_file = st.file_uploader("Choose a PDF or TXT file", type=['pdf', 'txt'])
            
            if uploaded_file is not None:
                if st.button("Upload"):
                    with st.spinner("Uploading and processing..."):
                        logger.info(f"User uploading file: {uploaded_file.name}")
                        files = {"file": (uploaded_file.name, uploaded_file, uploaded_file.type)}
                        response = requests.post(
                            f"{API_URL}/subjects/{subject_id}/documents/",
                            files=files
                        )
                        
                        if response.status_code == 200:
                            st.success("Document uploaded successfully!")
                        else:
                            logger.error(f"Upload failed: {response.text}")
                            st.error(f"Upload failed: {response.text}")

else:
    st.error("Could not connect to backend API. Is it running?")
