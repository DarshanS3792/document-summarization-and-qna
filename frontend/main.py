""" A streamlit page to showcase summarization capabilities.
    Page mainly showcases three capabilities:
        1. Summarize the pasted text.
        2. Summarize the content from web pages.
        3. Summarize the content from uploaded documents.
"""

import os
import sys
import time
import streamlit as st
import docx2txt
from pdfminer.high_level import extract_text
from pages.settings import page_config, custom_css, delete_folder_contents, write_uploaded_file
from streamlit_option_menu import option_menu
from streamlit_lottie import st_lottie
from streamlit_extras.switch_page_button import switch_page
from streamlit.components import v1

# Get the absolute path to the project root directory
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
src_path = os.path.abspath(os.path.join(project_root, "src"))
sys.path.insert(0, src_path)

# Loading prompt templates and GPT Utilities from src
from prompts import summarize_text
from db_utils import VECTOR_DB_UTILS
from url_utils import *

# Initialize database class
vector_db = VECTOR_DB_UTILS()

# Path for the temporary documents
temp_dir = f"{project_root}/temp_docs"

def summary_ytvideo():
    """A streamlit function to show the input options and summarize when YouTube Video URL is selected"""

    summarized_text = ""
    tokens_used = 0
    exec_time = 0

    with st.form("yt_video_summerize"):
        yt_url = st.text_input(label="Paste an YouTube URL",
                            value='''https://youtu.be/S951cdansBI''')
        word_limit = st.slider(label="Select summary word limit", min_value=200, max_value=1000, step=100)
        submit_button = st.form_submit_button(label="Summarize", disabled=not st.session_state.valid_key)

        if submit_button:
            # Validate the YouTube Video URL
            if validate_youtube_url(yt_url):
                extracted_text = vector_db.youtube_transcript(yt_url=yt_url)
                if len(extracted_text) == 0:
                    st.error("Unable to extract transcript from this Video. Please try other Video URLs")
                elif len(extracted_text) > 10000:
                    st.error("The extracted web content is too large to summarize.")
                else:
                    summarized_text, tokens_used, exec_time = gpt_completions(text_input=extracted_text, word_limit=word_limit)
            else:
                st.error("Invalid URL. Please correct and submit again.")

    return summarized_text, tokens_used, exec_time

def calculate_text_length(text_input: str):
    """A simple function to calculate the text length."""
    is_text_enough = len(text_input) > 750
    st.session_state.valid_text_length = is_text_enough

def gpt_completions(text_input: str, word_limit: int):
    """A function to build prompt and get gpt response."""
    
    # Start timer
    start_time = time.time()
    
    prompt = summarize_text(text_input=text_input, word_limit=word_limit)
    gpt_response = st.session_state.gpt.get_completion_from_messages(messages=prompt)
    gpt_summary = gpt_response.choices[0].message["content"]
    tokens_used = gpt_response.usage.total_tokens

    # End timer
    end_time = time.time()

    # Calculate the execution_time
    execution_time = end_time - start_time

    return gpt_summary, tokens_used, execution_time

def summary_text():
    """A streamlit function to show the input options and summarize when text input is selected"""
    
    summarized_text = ""
    tokens_used = 0
    exec_time = 0
    
    with st.form("text_summarize"):
        text_input = st.text_area(label="Paste the text to summarise",
                                    value='''''',
                                    height=150,
                                    max_chars=4092)
        word_limit = st.slider(label="Choose a summary word limit", min_value=200, max_value=1000, step=100)
        submit_button = st.form_submit_button(label="Summarize", disabled=not st.session_state.valid_key)
        if submit_button:
            if len(text_input) < word_limit:
                st.warning("Text is too short to summarize.")
                summarized_text = text_input
            else:
                summarized_text, tokens_used, exec_time = gpt_completions(text_input=text_input, word_limit=word_limit)

    return summarized_text, tokens_used, exec_time

def summary_url():
    """A streamlit function to show the input options and summarize when URL input is selected"""

    summarized_text = ""
    tokens_used = 0
    exec_time = 0

    with st.form("url_summarize"):
        url_input = st.text_input(label="Paste the URL",
                                  value='''''')
        word_limit = st.slider(label="Choose a summary word limit", min_value=200, max_value=1000, step=100)
        submit_button = st.form_submit_button(label="Summarize", disabled=not st.session_state.valid_key)
        if submit_button:
            if validate_input_url(url_input):
                extracted_text = extract_text_url(url_input)
                if len(extracted_text) == 0:
                    st.error("Unable to extract text content from this URL. Please try other URL.")
                elif len(extracted_text) > 10000:
                    st.error("The extracted web content is too large to summarize.")
                else:
                    summarized_text, tokens_used, exec_time = gpt_completions(text_input=extracted_text, word_limit=word_limit)
            else:
                st.error("Invalid URL. Please correct and submit again.")

    return summarized_text, tokens_used, exec_time

def summary_document():
    """A streamlit function to show the input options and summarize when document upload input is selected"""

    summarized_text = ""
    tokens_used = 0
    exec_time = 0

    with st.form("doc_summarize"):
        uploaded_file = st.file_uploader(label="Choose a file",
                                           type=["pdf", "docx", "txt"], on_change=delete_folder_contents(temp_dir))
        word_limit = st.slider(label="Choose a summary word limit", min_value=200, max_value=1000, step=100)
        submit_button = st.form_submit_button(label="Summarize", disabled=not st.session_state.valid_key)
        if submit_button:
            if uploaded_file is not None:
                file_path, file_type = write_uploaded_file(uploaded_file, temp_dir)
                extracted_text = ""
                #st.write(file_type)
                if file_type == "application/pdf":
                    # Extract PDF text
                    extracted_text = extract_text(file_path)
                elif file_type == "application/vnd.openxmlformats-officedocument.wordprocessingml.document":
                    # Extract DOCX text
                    extracted_text = docx2txt.process(file_path)
                elif file_type == "text/plain":
                    # Extract TXT file contents
                    with open(file_path) as f:
                        extracted_text = f.read()

                if len(extracted_text) == 0:
                    st.error("Unable to extract text content from this document. Please try with other document.")
                elif len(extracted_text) > 10000:
                    st.error("The extracted text content is too large to summarize.")
                else:
                    summarized_text, tokens_used, exec_time = gpt_completions(text_input=extracted_text, word_limit=word_limit)
            else:
                st.error("Please upload a document")       

    return summarized_text, tokens_used, exec_time

def summarization():
    """ A function to display the various summarization capabilities as streamlit page.
        This function mainly defines the input mode for three methods and call the execution functions on select.
    """
    
    # Load the page config and custom css from settings
    page_config()
    custom_css()
    
    col1, col2 = st.columns(spec=[0.08, 0.92])
           
    with col1:
        st_lottie("https://lottie.host/7d468c6d-1115-4fe1-9963-019a4bad95f3/HbnPMZtxjc.json", speed=2, quality="high", height=90, width=75)   
        
    with col2:
        st.title(':blue[HAI7.ai]')
        # st.image(image="gallery/Title-Image-dark.png", width=150)         

    st.caption("_Smart Document Companion: Summarize, Understand, and Interact with Ease_")
    st.subheader("", divider='blue')
    
    # Horizontal menu   
    selected = option_menu(None, ["Document Summarization", "Document Q&A"], 
        icons=['file-earmark', 'file-earmark'], 
        menu_icon="cast", default_index=0, orientation="horizontal")
    
    if selected == "Document Q&A":
        switch_page("chat_with_data")
       
    # Define the header for the page
    # st.subheader("Summarization 🔮")
    
    summarized_text = ""
    
    # if not st.session_state.valid_key:
    #     st.warning("Invalid Open AI API Key. Please re-configure your Open AI API Key.")
    
    tab1, tab2, tab3, tab4 = st.tabs(["**Document(s)**", "**URL**", "**YouTube URL**", "**Text**"])

    with tab1:
        summarized_text, tokens_used, exec_time = summary_document()
        print_summary(summarized_text, tokens_used, exec_time)

    with tab2:
        summarized_text, tokens_used, exec_time = summary_url()
        print_summary(summarized_text, tokens_used, exec_time)

    with tab3:
        summarized_text, tokens_used, exec_time = summary_ytvideo()
        print_summary(summarized_text, tokens_used, exec_time)
        
    with tab4:
        summarized_text, tokens_used, exec_time = summary_text()
        print_summary(summarized_text, tokens_used, exec_time)
        
    v1.html("""
    <script>
    const tabs = window.parent.document.querySelectorAll('button[data-baseweb="tab"] p');
    const tab_panels = window.parent.document.querySelectorAll('div[data-baseweb="tab-panel"]');

    tabs.forEach(function (tab, index) {
        const tab_panel_child = tab_panels[index].querySelectorAll("*");

        function set_visibility(state) {
            tab_panels[index].style.visibility = state;
            tab_panel_child.forEach(function (child) {
                child.style.visibility = state;
            });
        }

        tab.addEventListener("click", function (event) {
            set_visibility('hidden')

            let element = tab_panels[index].querySelector('div[data-testid="stVerticalBlock"]');
            let main_block = window.parent.document.querySelector('section.main div[data-testid="stVerticalBlock"]');
            const waitMs = 1;

            function waitForLayout() {
                if (element.offsetWidth === main_block.offsetWidth) {
                    set_visibility("visible");
                } else {
                    setTimeout(waitForLayout, waitMs);
                }
            }
            waitForLayout();
        });
    });
    </script>
""", height=0)

def print_summary(summarized_text, tokens_used, exec_time):
    if len(summarized_text) > 0:
        with st.expander(label='', expanded=True):
            st.markdown("### Summarized Content:")
            st.divider()
            st.write(summarized_text)
            st.markdown(
                f"<p style='font-size: smaller; color: green;'>Tokens used: {tokens_used}</br>Executed in {exec_time:.4f} seconds",
                unsafe_allow_html=True,
            )
            
summarization()
