import logging
import numpy as np
import openai
import faiss
from langchain_text_splitters import RecursiveCharacterTextSplitter

from manage.utils import get_path, save_data, read_data
from manage.config import Config

class Retriever:
    def __init__(self, openai_client: openai.OpenAI) -> None:
        self.openai_client = openai_client
        self.emb_model = Config.EMBEDDING_MODEL
        self.emb_size = int(Config.EMBEDDING_SIZE)
        self.faiss_index = None
        self.faiss_index_path = None
        self.index_map = None
        self.index_map_path = None 
        self.text_splitter = RecursiveCharacterTextSplitter(
            ['.', '?', '!'],
            chunk_size=150,
            chunk_overlap=50,
            length_function=len,
            is_separator_regex=False,
        )
        self._init_index()

    def _init_index(self) -> None:
        """
            Initialize faiss index and load index map. If not exist, create new.
        """
        # Initialize faiss index
        self.faiss_index_path, path_exists = get_path(Config.FAISS_INDEX_PATH, 'faiss_index_test', '.bin')
        if path_exists:
            self.faiss_index = faiss.read_index(self.faiss_index_path, faiss.IO_FLAG_MMAP)
        else:
            # ensure embedding size is correct
            test_emb_size = self.get_text_embeddings('test').shape[1]
            if test_emb_size != self.emb_size:
                logging.error(f"Embeddings are mismatching! Setting emb_size to {test_emb_size}...")
                self.emb_size = test_emb_size
            
            # create new index
            index = faiss.IndexFlatIP(self.emb_size)
            self.faiss_index = faiss.IndexIDMap(index)

        # Initalize index map
        self.index_map_path, path_exists = get_path(Config.FAISS_INDEX_PATH, 'index_map', '.json')
        if path_exists:
            self.index_map = read_data(self.index_map_path)
        else:
            self.index_map = {
                'current_id': 0,
                'map': {}
            }

    def _check_openai_client(self) -> None:
        """
            Check if OpenAI client is available
        """
        if self.openai_client is None:
            raise ValueError("OpenAI client is not initialized")

    def get_text_embeddings(self, text_list: list) -> np.ndarray:
        """
            Get embeddings for a list of texts using the OpenAI client.

            :param text_list: list - List of texts to get embeddings for

            :return: Embeddings for the input texts as np.ndarray with shape (len(text_list), emb_size)
        """
        self._check_openai_client()
        response = self.openai_client.embeddings.create(input=text_list, model=self.emb_model)
        return np.array([el.embedding for el in response.data]).astype(np.float32)

    @staticmethod
    def normalize_vectors(vectors: np.ndarray) -> np.ndarray:
        """
            Normalize vectors to make cosine similarity search easier
        """
        return vectors / np.linalg.norm(vectors, axis=1, keepdims=True)

    def save(self, document_id: str, document_content: dict) -> None:
        """
            Save document embeddings to faiss index and save document itself.

            :param document_id: str
            :param document_content: dict - Content of the document to save
        """
        self.save_document_embeddings(document_id, document_content['sections'])
        self._save_document(document_id, document_content)

    def save_document_embeddings(self, document_id: str, text_chapters: list) -> None:
        """
            Save document's embeddings to vector db, one vector for one section of document

            :param document_id: str
            :param text_chapters: list - List of text chapters to save embeddings for
        """
        embeddings = self.get_text_embeddings(text_chapters)
        embeddings = Retriever.normalize_vectors(embeddings)
        ids = np.arange(self.index_map['current_id'], self.index_map['current_id'] + len(text_chapters), 1).astype(np.int64)
        self.faiss_index.add_with_ids(embeddings, ids)
        self.index_map['map'][document_id] = ids.tolist()
        self.index_map['current_id'] += len(text_chapters)
        self._save_index()
    
    def _save_document(self, document_id: str, data: dict) -> None:
        """
            Save document to local file storage

            :param document_id: str
            :param data: dict - Content of the document to save
        """
        document_path, path_exists = get_path(Config.DOCUMENTS_PATH, document_id)
        if path_exists:
            raise FileExistsError(f"Document '{document_id}' alreadty exists.")
        save_data(document_path, data)

    def _save_index(self):
        """
            Save current faiss index
        """
        faiss.write_index(self.faiss_index, self.faiss_index_path)
        save_data(self.index_map_path, self.index_map)
    
    def get_relevant_context(self, document_id: str, document_sections: list, input: str) -> str:
        """
            Retrieve relevant information from the document's context.
            First it finds the most relevant sections (top_k = 2) of document, next it searches 
            for the most relevant chunks of the document using temporal faiss index (top_k = 5)

            :param document_id: str
            :param document_sections: list
            :param input: str - Input to search for in the document's context

            :return: string with context or None if error occured
        """
        try:
            # get embedding for user's input
            input_embedding = self.get_text_embeddings([input])
            input_embedding = Retriever.normalize_vectors(input_embedding)
            
            # find most relevant sections of document
            relevant_sections_ids = self.get_most_relevant_sections(document_id, input_embedding)

            # load these sections
            #document_sections = self._get_document_sections(document_id)
            most_relevant_sections = [document_sections[section_id] for section_id in relevant_sections_ids]
            most_relevant_text = "\n\n".join(most_relevant_sections)

            # find most relevant chunks of document
            context_chunks = self.get_topk_context_chunks(most_relevant_text, input_embedding)
            return "\n\n".join(context_chunks)
        except Exception as e:
            # if error occured, return None and log the error
            logging.error(f"Error in 'get_relevant_context' function: {e}")
            return None

    def get_most_relevant_sections(self, document_id: str, input_embedding: np.ndarray, top_k: int = 2) -> list:
        """
            Find most relevant sections of the document using faiss index.

            :param document_id: str
            :param input_embedding: np.ndarray
            :param top_k: int - number of most relevant sections to return

            :return: list of section ids
        """
        # get db indices of sections of document from index_map
        sections_indices = np.array(self.index_map['map'][document_id])
        # find most relevant sections using faiss index
        distances, indices = self.faiss_index.search(input_embedding, top_k*2)
        # return section ids as they were in document
        return np.argwhere(np.isin(sections_indices, indices)).flatten().tolist()[:top_k]

    def get_topk_context_chunks(self, relevant_text: str, input_embedding: np.ndarray, top_k: int = 5) -> list:
        """
            Get top k context chunks of the document' section using temporal faiss index.

            :param relevant_text: str
            :param input_embedding: np.ndarray
            :param top_k: int - number of top k context chunks to return

            :return: list of context chunks
        """
        # split text into chunks
        chunks = self.text_splitter.split_text(relevant_text)
        # vectorize it and normalize
        chunks_embeddings = self.get_text_embeddings(chunks)
        chunks_embeddings = Retriever.normalize_vectors(chunks_embeddings)
        # create index
        index = faiss.IndexFlatIP(self.emb_size)
        # add embeddings to index
        index.add(chunks_embeddings)
        # search top k most relevant
        distances, indices = index.search(input_embedding, top_k)
        # find them in text
        indices = indices[indices >= 0]
        context_chunks = [chunks[id] for id in indices.flatten().tolist()]
        # return them
        return context_chunks