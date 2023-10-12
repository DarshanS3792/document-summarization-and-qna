# document-summarization-and-qna

1. To use this application, you must create an API Key with OpenAI.
    
2. In your terminal, create an virtual environment and install requirements from requirements file by running following command.

   `python -m pip install -r requirements.txt --no-cache-dir`

3. Run following command from the project root directory to launch the streamlit application.

   `streamlit run frontend/main.py`

4. Browse `http://localhost:8501/` to see the application.

5. Optionally, you can build a docker image and deploy as a container after step 1.

6. To build the docker image, execute the following command in the project root directory.

    `docker build -t document-summarization-and-qna .`

7. To run the container, execute the command: `docker run -d --restart unless-stopped -p 8080:8501 document-summarization-and-qna`

8. Input your OpenAI API key and start using the application.
