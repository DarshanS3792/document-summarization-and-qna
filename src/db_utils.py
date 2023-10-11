""" A python file to process text or documents into text chunks followed by embeddings to store in vector databases.
    It also provides the utilitie to clear the persisted db.
"""

import os
import time
import datetime
import shutil
import pandas as pd
from langchain.vectorstores import FAISS
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain.document_loaders import TextLoader, PDFMinerLoader, UnstructuredWordDocumentLoader, UnstructuredExcelLoader
from langchain.docstore.document import Document
from langchain.document_loaders import YoutubeLoader
from dotenv import load_dotenv, find_dotenv

_ = load_dotenv(find_dotenv())  # read local .env file

# Load Environment Variables
KNOWLDGE_BASE_DIR = os.environ["KNOWLDGE_BASE_DIR"]  # Load Knowledge base directory name
FAISS_DB_DIR = os.environ["FAISS_DB_DIR"]  # Load Vector database directory name
CHUNK_SIZE = int(os.environ["CHUNK_SIZE"])  # Loading Text chunk size as integer variable
CHUNK_OVERLAP = int(os.environ["CHUNK_OVERLAP"]) # Loading Text chunk overlap as integer variable

# Get the absolute path to the project root directory
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))

knowledge_base_path = f"{project_root}/{KNOWLDGE_BASE_DIR}"
processed_dir_path = f"{project_root}/processed_documents"
faiss_db_path = f"{project_root}/{FAISS_DB_DIR}"
current_db_info_file_path = f"{project_root}/db_details.csv"


class VECTOR_DB_UTILS:
    """ A class to define various utilities for vector databases.
    """

    def __init__(self) -> None:
        self.knowledge_base_path = knowledge_base_path
        self.db_path = faiss_db_path
        self.chunk_size = CHUNK_SIZE
        self.chunk_overlap = CHUNK_OVERLAP

    def create_documents(self) -> list:
        """ A method to extract the document contents from the documents that exist in a folder and returns the list of documents.
        """

        loader_mapping = {
                '.pdf': PDFMinerLoader,
                '.docx': UnstructuredWordDocumentLoader,
                '.txt': TextLoader,
                '.xlsx': UnstructuredExcelLoader,
            }
        
        # Check if documents folder exist and not empty
        if os.path.exists(self.knowledge_base_path) and os.listdir(self.knowledge_base_path):
            # Define empty documents list
            documents = []
            df = pd.DataFrame(columns=['Input_Type', 'File_Name', 'File_Type', 'Executed_Time'])
            os.makedirs(processed_dir_path, exist_ok=True)
            # Iterate over files and extract the text from documents
            for file_name in os.listdir(self.knowledge_base_path):
                file_path = os.path.join(self.knowledge_base_path, file_name)
                ext = "." + file_path.rsplit(".", 1)[-1]
                
                if ext in loader_mapping:
                    loader_class = loader_mapping[ext]  # get the defined loader class for the given file type
                    loader = loader_class(file_path)  # define the loader for the file
                    document_contents = loader.load()  # extract the document contents using loader
                    documents.extend(document_contents)  # Append the existing document list

                    file_info = {
                        'Input_Type': "Document",
                        'File_Name': file_name,
                        'File_Type': ext,  # Get the file extension
                        'Executed_Time': datetime.datetime.now()     # Get the current time
                    }
                    print(file_info)
                    temp_df = pd.DataFrame(file_info, index=[0])

                    # Append the information to the DataFrame
                    df = pd.concat([df, temp_df], ignore_index=True)

                    # Move processed documents to processed folder
                    shutil.move(file_path, os.path.join(processed_dir_path, os.path.basename(file_path)))   
                else:
                    raise ValueError(f"Unsupported file extension: {ext}")
        
            return documents, df
        else:
            return None
        
    def _get_video_info(self, yt_url) -> dict:
        """Get important video information.

        Components are:
            - title
            - description
            - thumbnail url,
            - publish_date
            - channel_author
            - and more.
        """
        try:
            from pytube import YouTube

        except ImportError:
            raise ImportError(
                "Could not import pytube python package. "
                "Please it install it with `pip install pytube`."
            )
        yt = YouTube(yt_url)
        video_info = {
            "title": yt.title,
            "description": yt.description,
            "view_count": str(yt.views),
            "thumbnail_url": yt.thumbnail_url,
            "publish_date": yt.publish_date.strftime("%d/%m/%Y"),
            "length": f"{yt.length /60:.2f} Minutes",
            "author": yt.author,
        }
        return video_info
        
    def youtube_transcript(self, yt_url):
        """ A method to extract transcriptions from Youtube video and create
        """
        try:
            loader = YoutubeLoader.from_youtube_url(youtube_url=yt_url, add_video_info=True)
            yt_transcript = loader.load()
            # Access Video Info
            yt_info = self._get_video_info(yt_url)
            file_info = {
                'Input_Type': "YouTube Video",
                'File_Name': f"{yt_info['title']}({yt_url})",
                'File_Type': None,  # Get the file extension
                'Executed_Time': datetime.datetime.now()     # Get the current time
            }
            df = pd.DataFrame(file_info, index=[0])
            #return [Document(page_content=yt_transcript, metadata={"source": yt_url})]
            return yt_transcript, df
        except Exception as e:
            print(f"Error while loading transcripts from youtube video: {e}")
            return None

    def process_documents(self, documents):
        """ A method to convert the extracted documents into chunks and return splitted data.
        """

        # Define the text splitter configurations
        text_splitter = RecursiveCharacterTextSplitter(chunk_size=CHUNK_SIZE, chunk_overlap=CHUNK_OVERLAP)

        if not documents:
            print("No new document to process")
            return None
        else:
            text_chunks = text_splitter.split_documents(documents)
        
        return text_chunks

    def run_db_build(self, input_type, embeddings, page_content="", source_url= "", merge_with_existing_db: bool=False, **kwargs):
        """ A method to build the vector db and store in the defined database path.
        """
        try:
            start_time = time.time()
            os.makedirs(self.db_path, exist_ok=True)

            # Get extracted documents content
            if input_type == "documents":
                documents, doc_df = self.create_documents()
            elif input_type == "web_url":
                documents = [Document(page_content=page_content, metadata={"source": source_url})]
                file_info = {
                    'Input_Type': "Web Page",
                    'File_Name': f"{source_url}",
                    'File_Type': None,  # Get the file extension
                    'Executed_Time': datetime.datetime.now()     # Get the current time
                }
                doc_df = pd.DataFrame(file_info, index=[0])

            elif input_type == "yt_url":
                documents, doc_df = self.youtube_transcript(yt_url=source_url)

            # Get the text chunks
            if documents is not None:
                processed_documents = self.process_documents(documents=documents)
            else:
                print("No document content is provided.")                

            # Build vector db
            new_db = FAISS.from_documents(documents=processed_documents, embedding=embeddings)

            if merge_with_existing_db:
                exist_db = self.load_local_db(embeddings)
                # print(f"Exist_DB:{exist_db.docstore.__dict__}")
                if exist_db is not None:
                    print("Merging new db into existing. . .")
                    exist_db.merge_from(new_db)
                    # Save the new merged database
                    exist_db.save_local(self.db_path)
                    final_db = exist_db
                    # print(f"Merged_DB:{final_db.docstore.__dict__}")
                    if os.path.exists(current_db_info_file_path):
                        exist_df = pd.read_csv(current_db_info_file_path)
                    else:
                        exist_df = pd.DataFrame(columns=['Input_Type', 'File_Name', 'File_Type', 'Executed_Time'])
                    
                    merge_df = pd.concat([exist_df, doc_df], ignore_index=True)
                    merge_df.to_csv(current_db_info_file_path, index=False)
                else:
                    print("No db exists. . .")
                    new_db.save_local(self.db_path)
                    final_db = new_db
                    # print(f"New_DB:{final_db.docstore.__dict__}")
                    doc_df.to_csv(current_db_info_file_path, index=False)
            else:
                print("Overwriting existing database. . .")
                new_db.save_local(self.db_path)
                final_db = new_db
                # print(f"New_DB:{final_db.docstore.__dict__}")
                doc_df.to_csv(current_db_info_file_path, index=False)

            # if merge_with_existing_db:
            #     new_db.save_local(self.db_path)
            # else:
            #     new_db.save_local(self.db_path)

            
            end_time = time.time()

            return final_db, end_time-start_time
        
        except Exception as e:
            error_msg = f"An error occurred while reading files: {e}"
            print(error_msg)
            return None, 0.00

    def load_local_db(self, embeddings):
        """ A simple method to load locally saved vector database.
        """
        if os.path.exists(self.db_path) and os.path.isfile(os.path.join(self.db_path, "index.faiss")):
            return FAISS.load_local(self.db_path, embeddings)
        else:
            return None
