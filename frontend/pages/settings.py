import os
import sys
import shutil
import streamlit as st
from streamlit_extras.switch_page_button import switch_page

# Get the absolute path to the project root directory
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), "../.."))
src_path = os.path.abspath(os.path.join(project_root, "src"))
sys.path.insert(0, src_path)

from gpt_utils import GPT_UTILS

def set_open_api_key(api_key: str):
    st.session_state.OPENAI_API_KEY = api_key
    st.session_state.valid_key = True
    st.session_state.open_api_key_configured = True
    print("OPENAI API key is configured successfully!")

# Set Page Config
def page_config():
    st.set_page_config(
        page_title="Document Summarization and Q&A",
        page_icon="❇️",
        layout="wide",
    )

    if "valid_key" not in st.session_state:
        st.session_state.valid_key = False
        st.session_state.gpt = ""

    with st.sidebar:
        api_key_form = st.form("OPENAI_API_KEY_FORM")
        openai_api_key_input = api_key_form.text_input(
            "Input your OpenAI API Key",
            type="password",
            placeholder="🔑",
            help="You can get your API key from https://platform.openai.com/account/api-keys.",
            value=st.session_state.get("OPEN_API_KEY", ""),
        )
        configure_api_key = api_key_form.form_submit_button("Configure API Key")

        if configure_api_key:
            # Validate the API Key
            if openai_api_key_input:
                test_gpt = GPT_UTILS(api_key=openai_api_key_input)
                if test_gpt.validate_key():
                    set_open_api_key(openai_api_key_input)
                else:
                    st.error("Invalid API Key. Please re-configure with valid API Key")

        if not st.session_state.get("open_api_key_configured"):
            st.warning("Please configure your OpenAI API key!")
        else:
            st.success("OpenAI API key is configured!")
            st.session_state.gpt = GPT_UTILS(
                api_key=st.session_state.get("OPENAI_API_KEY", "")
            )    

@st.cache_resource
def custom_css():
    st.markdown(
        """ <style>
        footer {visibility: visible;}
        .block-container {
                        padding-top: 2rem;
                    }
        </style> """,
        unsafe_allow_html=True,
    )

# def switch_home():
#     if st.sidebar.button("Contact Us", use_container_width=True):
#         switch_page("main")

def delete_folder_contents(folder_path):
    """A function to delete the folder and it's content"""
    # Check if the folder exists
    if os.path.exists(folder_path):
        # Delete the folder and its contents
        shutil.rmtree(folder_path)
        print(f"Deleted everything in '{folder_path}'.")
    else:
        print(f"Folder '{folder_path}' does not exist.")

def count_files_in_directory(directory):
    """ A function to count files in directory"""
    if not os.path.exists(directory):
        return 0
    
    if not os.path.isdir(directory):
        return 0
    
    file_count = 0
    for _, _, files in os.walk(directory):
        file_count += len(files)
    
    return file_count

def write_uploaded_file(uploaded_file, folder_path):
    """A function to write the file to the folder from streamlit file uploader"""

    if uploaded_file is not None:
        # Create directory if not exists
        os.makedirs(folder_path, exist_ok=True)
        file_path = os.path.join(folder_path, uploaded_file.name)
        with open(file_path, "wb") as f:
            f.write(uploaded_file.read())
        
        return file_path, uploaded_file.type

def write_uploaded_files(uploaded_files, folder_path):
    """A streamlit function to write the multiple files to local directory from streamlit file uploader"""

    len_uploaded_files = len(uploaded_files)

    # Validate files and copy to new_files directory
    if len_uploaded_files != 0:
        try:         
            # Create directory if not exists
            os.makedirs(folder_path, exist_ok=True)
            file_count = 0
            msg = st.toast(f"Uploading {len_uploaded_files} files...")
            for file in uploaded_files:
                # Save the file to new_files directory
                file_path = os.path.join(folder_path, file.name)
                with open(file_path, "wb") as f:
                    f.write(file.read())
                file_count += 1
                # Display a success message after upload is done
                msg.toast(f"Uploaded {file_count}/{len_uploaded_files} files: {file.name}")

            if file_count == len_uploaded_files:
                st.success("All files uploaded and validated successfully.")
                msg.toast(f"Upload Complete.", icon="✔️")
                upload_success = True
            elif file_count > 0 and file_count <= len_uploaded_files:
                st.warning(f"Only {file_count} out of {len_uploaded_files} files are uploaded.")
                msg.toast(f"Upload Complete.", icon="⚠️")
                upload_success = True
            else:
                st.error("No files are uploaded.")
                msg.toast(f"Upload Error.", icon="❌")
                upload_success = False

        except Exception as e:
            error_msg = f"An error occurred while uploading files: {e}"
            st.exception(error_msg)
            upload_success = False
    else:
        st.error("Please choose a file")      
        upload_success = False  
            
    return upload_success
