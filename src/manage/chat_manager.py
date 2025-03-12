import openai

import logging

from manage.utils import get_path, read_data, save_data
from manage.config import Config
from manage.retriever import Retriever

class ChatManager:
    def __init__(self, retriever: Retriever, openai_client: openai.OpenAI) -> None:
        self.retriever = retriever
        self.openai_client = openai_client

    def _check_openai_client(self) -> None:
        """
            Check if OpenAI client is available
        """
        if self.openai_client is None:
            raise ValueError("OpenAI client is not initialized")

    def get_chat_history(self, session_id: str) -> str:
        """
            Load chat_history if exists, otherwise create new.
        """
        session_path, path_exists = get_path(Config.SESSIONS_PATH, session_id)
        if path_exists:
            chat_history = read_data(session_path)
            return chat_history
        
        chat_history = {
            'metadata': {
                'session_id': session_id
            },
            'messages': [{
                'role': 'system',
                'content': "You are an AI assistant answering questions based on the provided Wikipedia context. "
                "Try to answer shortly. If no Wikipedia context provided, say 'I don't have access to Wikipedia page "
                "with the information about it, but I can answer using another source.' and answer the question by "
                "your own. DON'T TELL USER THAT YOU HAVE LACK OF INFORMATION PROVIDED OR THAT CONTEXT IS NOT RELEVANT ENAUGH!"
            }]
        }
        logging.info(f"Creating new session: {session_id}")
        return chat_history
    
    def save_chat_history(self, session_id: str, chat_history: dict) -> None:
        """
            Save chat history to a file

            :param session_id : str
            :param chat_history : dict
        """
        session_path, path_exists = get_path(Config.SESSIONS_PATH, session_id)
        save_data(session_path, chat_history)

    def get_openai_response(self, messages: list) -> str:
        """
            Get OpenAI response for a given messages history

            :param messages : list

            :return: str
        """
        response = self.openai_client.chat.completions.create(
            messages=messages,
            model=Config.GPT_MODEL,
        )
        return response.choices[0].message.content

    def get_chat_response(self, session_id: str, document_id: str, inputs: str) -> str:
        """
            Get chat response using the provided Wikipedia document, chat_history and user input

            :param session_id : str
            :param document_id : str
            :param inputs : str

            :return: str
        """
        # get relevant ccontext from document
        document_sections = self._get_document_sections(document_id)
        relevant_context = self.retriever.get_relevant_context(document_id, document_sections, inputs)
        if relevant_context is None:
            relevant_context = "No context found."

        # get chat history
        chat_history = self.get_chat_history(session_id)

        # compose user message
        user_message = {
            "role": "user", 
            "content": f"Answer the question: {inputs}\n\nHere is some relevant information: {relevant_context}"
        }
        chat_history['messages'].append(user_message)

    
        # get response from OpenAI
        self._check_openai_client()
        response = self.get_openai_response(chat_history['messages'])
        assistant_message = {
            "role": "assistant", 
            "content": response
        }
        chat_history['messages'].append(assistant_message)

        # save chat history accorading to the user message and agent's response
        self.save_chat_history(session_id, chat_history)

        return response
    
    def _get_document_sections(self, document_id: str) -> list:
        """
            Get document content as a list of sections.

            :param document_id : str

            :return: list of sections
        """
        documents_path, path_exists = get_path(Config.DOCUMENTS_PATH, document_id)
        if not path_exists:
            raise FileNotFoundError(f"Document {document_id} doesn't exist!")
        data = read_data(documents_path)
        return data['sections']