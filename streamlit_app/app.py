import streamlit as st
import requests
import json
import time
import os
from dotenv import load_dotenv
import subprocess
import sys
import threading

# Load environment variables
load_dotenv()

# Constants
API_URL = "http://localhost:5000/api/search"
FLASK_STATUS_URL = "http://localhost:5000/api/health"

# Set page configuration
st.set_page_config(
    page_title="RAG Search System",
    page_icon="🔍",
)

def check_flask_server():
    try:
        response = requests.get(FLASK_STATUS_URL, timeout=2)
        return response.status_code == 200
    except:
        return False

def start_flask_server():
    try:
        # Get the path to the Flask app
        flask_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 
                                 "flask_app", "app.py")
        
        if os.path.exists(flask_path):
            # Start the Flask server as a subprocess
            subprocess.Popen([sys.executable, flask_path])
            st.success("Flask server started! Please wait a moment for it to initialize...")
            time.sleep(2)  # Wait for server to start
        else:
            st.error(f"Flask app not found at {flask_path}")
    except Exception as e:
        st.error(f"Failed to start Flask server: {str(e)}")

def get_llm_response(query):
    try:
        payload = {"query": query}
        
        with st.spinner("Searching the internet and generating response..."):
            if not check_flask_server():
                start_flask_server()
                for _ in range(5):
                    time.sleep(1)
                    if check_flask_server():
                        break
                else:
                    return "", [], "Could not connect to the Flask server. Please make sure it's running at http://localhost:5000"
            
            response = requests.post(API_URL, json=payload, timeout=60)
            
            if response.status_code == 200:
                data = response.json()
                return data.get("response", ""), data.get("sources", []), None
            else:
                error_message = f"Error: {response.status_code} - {response.text}"
                return "", [], error_message
    
    except requests.exceptions.ConnectionError:
        return "", [], "Connection error: Could not connect to the Flask server. Please make sure it's running at http://localhost:5000"
    except requests.exceptions.Timeout:
        return "", [], "Timeout error: The request took too long to complete. The server might be processing a complex query."
    except Exception as e:
        return "", [], f"Error: {str(e)}"

if 'chat_history' not in st.session_state:
    st.session_state.chat_history = []

if 'server_checked' not in st.session_state:
    st.session_state.server_checked = False


st.title("RAG Search System")
st.markdown("Ask anything and get answers based on the latest web information")



if st.button("Clear Chat History"):
    st.session_state.chat_history = []
    st.rerun()

if not st.session_state.server_checked:
    if not check_flask_server():
        st.warning("Flask backend is not running. Make sure to start it before making queries.")
    st.session_state.server_checked = True

# User input
user_query = st.text_input("Enter your question:", key="user_query")
search_button = st.button("Search")

if search_button and user_query:
    st.session_state.chat_history.append({"role": "user", "content": user_query})
    response_text, sources, error = get_llm_response(user_query)
    
    if error:
        st.error(error)
    else:

        st.session_state.chat_history.append({
            "role": "assistant", 
            "content": response_text,
            "sources": sources
        })

st.header("Chat History")
for message in st.session_state.chat_history:
    if message["role"] == "user":
        st.markdown(f"**You:** {message['content']}")
    else:
        st.markdown(f"**Assistant:** {message['content']}")
        if "sources" in message and message["sources"]:
            st.markdown("**Sources:**")
            for i, source in enumerate(message["sources"], 1):
                st.markdown(f"{i}. [{source}]({source})")
    
    st.markdown("---")
