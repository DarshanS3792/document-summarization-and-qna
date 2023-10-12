""" A Streamlit page that takes the documents and provide an interface to chat with the data available in the document.
"""

import os
import sys
import time
import streamlit as st
import pandas as pd
from pages.settings import page_config, custom_css, delete_folder_contents, write_uploaded_files, count_files_in_directory
from dotenv import load_dotenv, find_dotenv
from streamlit_option_menu import option_menu
from streamlit_lottie import st_lottie
from streamlit_extras.switch_page_button import switch_page
# import speech_recognition as sr

_ = load_dotenv(find_dotenv())  # read local .env file

# Load Environment Variables
KNOWLDGE_BASE_DIR = os.environ["KNOWLDGE_BASE_DIR"]  # Load Knowledge base directory name
FAISS_DB_DIR = os.environ["FAISS_DB_DIR"]  # Load Vector database directory name

# Get the absolute path to the project root directory
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), "../.."))
src_path = os.path.abspath(os.path.join(project_root, "src"))
sys.path.insert(0, src_path)

# Loading prompt templates and GPT Utilities from src
from prompts import prompt_doc_qa
from db_utils import VECTOR_DB_UTILS
from url_utils import *

# Initialize database class
vector_db = VECTOR_DB_UTILS()

# Path for the knowledge base documents
kb_path = f"{project_root}/{KNOWLDGE_BASE_DIR}"
db_path = f"{project_root}/{FAISS_DB_DIR}"
processed_dir_path = f"{project_root}/processed_documents"
current_db_info_file_path = f"{project_root}/db_details.csv"

if "db_exist" not in st.session_state:
    st.session_state.db_exist = False
    st.session_state.db_list = False

def process_documents(merge_with_exist: bool=False):
    """ A streamlit function to convert the uploaded document files into chunks and store in vector db.
    """
    try:
        db, db_build_time = vector_db.run_db_build(input_type="documents", embeddings=st.session_state.gpt.embeddings, merge_with_existing_db=merge_with_exist)
        if db is not None:
            st.info(f"Database build completed in {db_build_time:.4f} seconds")
            st.session_state.db_exist = True
            return st.session_state.db_exist
        else:
            st.session_state.db_exist = False
            return st.session_state.db_exist

    except Exception as e:
        error_msg = f"An error occurred while reading files: {e}"
        st.error(error_msg)
        st.session_state.db_exist = False
        return st.session_state.db_exist

def input_documents():
    """ A streamlit function to provide upload interface for documents and extract information from it.
    """
    
    with st.form("Process_Documents"):
        uploaded_files = st.file_uploader(label="Choose a file",
                                   type=["pdf", "xlsx", "txt"],
                                   accept_multiple_files=True,
                                   disabled=not st.session_state.valid_key,)
        merge_with_exist_db = st.checkbox(label="Merge with existing database",
                                          help="Check this box to merge with the existing vector database. Keep it unchecked to overwrite current database. Merging with exsiting database might result in unreliable responses.")
        submit_button = st.form_submit_button(label="Process Documents", disabled=not st.session_state.valid_key)

        if submit_button:
            # Upload all the documents to a temporary directory
            upload_state = write_uploaded_files(uploaded_files=uploaded_files, folder_path=kb_path)
            if not upload_state:
                st.error("Error while uploading files. Please check input files.")
            else:
                with st.spinner("Building database..."):
                    db_status = process_documents(merge_with_exist_db)
                    st.session_state.db_list = True

def input_url():	
    """ A streamlit function to extract text content from web url.	
    """	
    with st.form("Input_Web_URL"):	
        input_url = st.text_input(label="Enter a URL",	
                                value='''https://en.wikipedia.org/wiki/Eiffel_Tower''',
                                disabled=not st.session_state.valid_key,)	
        merge_with_exist_db = st.checkbox(label="Merge with existing database",
                                          help="Check this box to merge with the existing database. Keep it unchecked to overwrite current database. Merging with exsiting database might result in unreliable responses.")
        submit_url = st.form_submit_button(label="Extract Content", disabled=not st.session_state.valid_key,)	
        if submit_url:	
            # Extract web page content from the given URL	
            if validate_input_url(input_url):	
                extracted_text = extract_text_url(input_url)	
                if len(extracted_text) == 0:	
                    st.error("Unable to extract text content from this URL. Please try other URL.")	
                else:	
                    # Convert into chunks and build db	
                    db, db_build_time = vector_db.run_db_build(input_type="web_url", embeddings=st.session_state.gpt.embeddings, page_content=extracted_text, source_url=input_url, merge_with_existing_db=merge_with_exist_db)	
                    if db is not None:	
                        st.info(f"Database build completed in {db_build_time:.4f} seconds")	
                        st.session_state.db_exist = True	
                        return st.session_state.db_exist	
                    else:	
                        st.session_state.db_exist = False	
                        return st.session_state.db_exist	
            else:	
                st.error("Invalid URL. Please correct and submit again.")	
                st.session_state.db_exist = False	
                return st.session_state.db_exist	

def chat_with_data():
    """ A streamlit function to load the page to upload documents and chat with the data. You can input data in two ways:
        1. A text document such as PDF or DOCX.
        2. A Web Page or Blog URL.
        3. A YouTube URL.
    """

    # Load the page config and custom css from settings
    page_config()
    custom_css()
    
    col1, col2 = st.columns(spec=[0.16, 0.84])
           
    with col1:
        st.image(image="gallery/Title-Image-dark-small.png") 
        
    with col2:
        st_lottie("https://lottie.host/7d468c6d-1115-4fe1-9963-019a4bad95f3/HbnPMZtxjc.json", speed=2, quality="high", height=93, width=90)      

    st.caption("_Smart Document Companion: Summarize, Understand, and Interact with Ease_")
    st.subheader("", divider='blue')
    
    # Horizontal menu   
    selected = option_menu(None, ["Document Summarization", "Document Q&A"], 
        icons=['file-earmark', 'file-earmark'], 
        menu_icon="cast", default_index=1, orientation="horizontal")
    
    if selected == "Document Summarization":
        switch_page("main")
    
    # Validate Open AI Key
    # if not st.session_state.valid_key:
    #     st.warning("Invalid Open AI API Key. Please re-configure your Open AI API Key.")

    # Create tabs for Ingest and Query pages
    ingest_tab, query_tab = st.tabs(["**Ingest Data**", "**Query Documents**"])

    with ingest_tab:
        input_options = st.radio("Options", ["**Document(s)**", "**URL**", "**YouTube URL**"], horizontal=True, label_visibility="hidden")
        if input_options == "**Document(s)**":
            col1, col2 = st.columns([0.6, 0.4])
            with col1:
                input_documents()
                st.sidebar.info(
                    """
                    1. Click **Browse files** to upload the files and select whether or not they should be merged with an existing vector database.
                    2. To extract text content from documents and create a vector database, select **Process Documents**.
                    3. After a successful build, the **Files in vector database** count should always be 2.
                    4. You can also reset the vector database by clicking the **Clear Database** button.
                    5. You can then proceed to ask queries regarding documents in the **Query Documents** tab.

                    """
                )

        elif input_options == "**URL**":
            col1, col2 = st.columns([0.6, 0.4])
            with col1:
                input_url()
                st.sidebar.info(
                    """
                    1. Paste a Web URL and select whether or not they should be merged with an existing vector database.
                    2. To extract text content from an url and create a vector database, select **Extract Content**.
                    3. After a successful build, the **Files in vector database** count should always be 2.
                    4. You can also reset the vector database by clicking the **Clear Database** button.
                    5. You can then proceed to ask queries regarding documents in the **Query Documents** tab.
                    
                    """
                )
        elif input_options == "**YouTube URL**":
            col1, col2 = st.columns([0.6, 0.4])
            with col1:           
                st.sidebar.info(
                    """
                    1. Paste a YouTube URL and select whether or not they should be merged with an existing vector database.
                    2. To extract the transcript from a YouTube url and create a vector database, select **Extract Transcript**.
                    3. After a successful build, the **Files in vector database** count should always be 2.
                    4. You can also reset the vector database by clicking the **Clear Database** button.
                    5. You can then proceed to ask queries regarding documents in the **Query Documents** tab.
                    
                    """
                )
                with st.form("Input_YT_URL"):	
                    yt_url = st.text_input(label="Enter a URL",	
                                        value='''https://youtu.be/S951cdansBI''',
                                        disabled=not st.session_state.valid_key,)	
                    merge_with_exist_db = st.checkbox(label="Merge with existing database",
                                                    help="Check this box to merge with the existing database. Keep it unchecked to overwrite current database. Merging with exsiting database might result in unreliable responses.")
                    submit_url = st.form_submit_button(label="Extract Transcript", disabled=not st.session_state.valid_key,)	
                    if submit_url:	
                        # Validate the YouTube Video URL	
                        if validate_youtube_url(yt_url):	
                            db, db_build_time = vector_db.run_db_build(input_type="yt_url", embeddings=st.session_state.gpt.embeddings, source_url=yt_url, merge_with_existing_db=merge_with_exist_db)	
                            # video_info = vector_db._get_video_info(yt_url)	
                            if db is not None:	
                                st.info(f"Database build completed in {db_build_time:.4f} seconds")	
                        else:	
                            st.error("Invalid URL. Please correct and submit again.")	
            with col2:	
                tab1, tab2 = st.tabs(["**Video Details**", "**Watch Video**"])	
                if validate_youtube_url(yt_url):	
                    with tab1:	
                        video_info = vector_db._get_video_info(yt_url)	
                        st.dataframe(video_info, use_container_width=True)	
                    with tab2:	
                        st.video(yt_url)

        st.subheader("", divider='blue')

        st.session_state.db_list = os.path.exists(current_db_info_file_path)

        # st.markdown("#### Existing knowledge base info:")
        db_info_col1, db_info_col2 = st.columns([0.2, 0.8])
        with db_info_col1:
            st.metric(label="Files in vector database", value=count_files_in_directory(db_path))
            drop_database = st.button(label="Clear Database", use_container_width=True)
            if drop_database:
                delete_folder_contents(kb_path)
                delete_folder_contents(db_path)
                delete_folder_contents(processed_dir_path)
                if st.session_state.db_list:
                    os.remove(current_db_info_file_path)
                st.session_state.db_list = False
        with db_info_col2:
            if st.session_state.db_list:
                df = pd.read_csv(current_db_info_file_path)
                st.dataframe(df)
            # else:
            #     st.warning("No data exist in database.")

    with query_tab:
        response = None
        query_input = st.text_input(label="Please type your query that can be answered from the database.",
                                    placeholder="Enter your query",
                                    disabled=not st.session_state.valid_key,)
        return_source_docs = st.toggle(label="Return Source documents",
                                       value=True,
                                       disabled=True)

        if (len(query_input) != 0):
            start_time = time.time()
            local_db = vector_db.load_local_db(embeddings=st.session_state.gpt.embeddings)
            if local_db is not None:
                with st.spinner("Retrieving response ..."):
                    response = st.session_state.gpt.retrieval_qa(query=query_input,
                                                prompt=prompt_doc_qa(),
                                                db=local_db,
                                                return_source_documents=return_source_docs)
            else:
                st.error("Please build the Vector Database")
            end_time = time.time()

        if response is not None:
            response_completion = response['result']
            response_source_docs = []
            if return_source_docs:
                source_docs = response['source_documents']
                for document in source_docs:
                    response_source_docs.append({
                        'source': document.metadata['source'],
                        'content': document.page_content,
                    })

            with st.expander('', expanded=True):
                st.markdown(response_completion)
            if return_source_docs: st.markdown(f"<p style='font-size: smaller; color: green;'>Source documents: {response_source_docs}</p>", unsafe_allow_html=True) 
            st.markdown(f"<p style='font-size: smaller; color: green;'>Reponse time: {(end_time - start_time):.4f} seconds</p>", unsafe_allow_html=True)

chat_with_data()