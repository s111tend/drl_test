import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    WORKDIR = os.path.split(os.path.dirname(os.path.dirname(__file__)))[0]
    DOCUMENTS_PATH = os.path.join(WORKDIR, os.getenv('DOCUMENTS_PATH', "data/documents"))

    SESSIONS_PATH = os.path.join(WORKDIR, os.getenv('SESSIONS_PATH', "data/sessions"))

    LOG_DIR = os.path.join(WORKDIR, os.getenv('LOG_DIR', '/logs'))

    WIKI_API_USER_AGENT = os.getenv('WIKI_API_USER_AGENT', 'chat-app')
    WIKI_API_LANGUAGE = os.getenv('WIKI_API_LANGUAGE', 'en')

    EMBEDDING_MODEL = os.getenv('EMBEDDING_MODEL', "text-embedding-ada-002")
    EMBEDDING_SIZE = os.getenv('EMBEDDING_SIZE', 1536)
    FAISS_INDEX_PATH = os.path.join(WORKDIR, os.getenv('FAISS_INDEX_PATH', "data/faiss_index/"))

    GPT_MODEL = os.getenv('GPT_MODEL', 'gpt-4o-mini')
    OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

    # EMBEDDING MODEL SETTINGS
    CHUNK_SIZE = 150
    CHUNK_OVERLAP = 50

    # RETRIEVEMENT SETTINGS
    TOP_K1 = 2
    TOP_K2 = 4