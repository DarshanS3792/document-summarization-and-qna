""" A python file to define various utilities with url text extraction."""
import trafilatura
from trafilatura.settings import use_config
from courlan import validate_url, check_url

def validate_input_url(url):
    """A simple function to validate the url"""
    return validate_url(url)[0]

def validate_youtube_url(url):
    """A simple function to validate Youtube urls"""
    if validate_url(url)[0]:
        domain = check_url(url)[1]
        if domain == "youtube.com" or domain == "youtu.be":
            return True
        else:
            return False
    else:
        return False

def extract_text_url(url):
    """A function to extract the text content from given URL"""

    # Instantiate config for trafilatura
    config = use_config()

    # Setting the default configuration
    config.set("DEFAULT", "EXTRACTION_TIMEOUT", "0")

    # Download the Web content from the URL
    download_web = trafilatura.fetch_url(url)

    # Extract the main text content from the download web content
    extracted_text = trafilatura.extract(download_web, config=config)

    return extracted_text