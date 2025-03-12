import wikipediaapi
import logging

from manage.utils import get_path, save_data
from manage.config import Config
from manage.retriever import Retriever

class TaskManager:
    def __init__(self, retriever: Retriever) -> None:
        self.retriever = retriever
        self.wiki_client = self.get_wiki_client()
        self.tasks = {}

    def get_wiki_client(self) -> wikipediaapi.Wikipedia:
        """
            Set up the Wikipedia API client
        """
        try:
            logging.getLogger("wikipediaapi").setLevel(logging.WARNING)
            return wikipediaapi.Wikipedia(
                user_agent = Config.WIKI_API_USER_AGENT,
                language = Config.WIKI_API_LANGUAGE
            )
        except Exception as e:
            logging.error(f"Error getting wiki client: {e}", )
            return None
        
    def _check_wiki_client(self) -> None:
        """
            Check if wiki client is available and raises error if not
        """
        if self.wiki_client is None:
            raise ValueError("Wiki client is not initialized!")
    
    def assign_task(self, task_id: str) -> None:
        """
            Add a task to the task list
        """
        self.tasks[task_id] = 'pending'
        logging.info(f"Task {task_id} is pending...")

    def run_task(self, task_id: str) -> None:
        """
            Update task status to 'running'
        """
        self.tasks[task_id] = 'running'
        logging.info(f"Task {task_id} is running...")

    def finish_task(self, task_id: str) -> None:
        """
            Update task status to 'finished'
        """
        self.tasks[task_id] = 'finished'
        logging.info(f"Task {task_id} is finished!")

    def fail_task(self, task_id: str) -> None:
        """
            Update task status to 'failed'
        """
        self.tasks[task_id] = 'failed'
        logging.info(f"Task {task_id} is failed!")

    def get_task_status(self, task_id: str) -> str:
        """
            Get task status

            :param task_id: str

            :return: status of the task ('pending', 'running', 'finished', 'failed' and None if task_id is incorrect)
        """
        status = self.tasks.get(task_id)
        if status is None:
            logging.error(f"Task not found with id {task_id}!")
        return status
    
    def process_task(self, task_id: str, topic: str, document_id: str) -> None:
        """
            Process a task

            :param task_id: str
            :param topic: str - requested topic of the Wikipedia page
            :param document_id: str - id of the document to store the content
        """
        # check if task is in tasks dictionary.
        if self.get_task_status(task_id) is None:
            return
        
        try:
            # update task status to 'running'
            self.run_task(task_id)

            # get wiki page
            self._check_wiki_client()
            wikipage = self.retrieve_wikipedia_content(topic)

            # save document and it's sections embeddings to a vector DB
            self.retriever.save(document_id, wikipage)

            # update task status to 'finished'
            self.finish_task(task_id)
        except Exception as e:
            # if error occures, fail the task and log the exception
            self.fail_task(task_id)
            logging.error(f"Error: {e}")

    def retrieve_wikipedia_content(self, topic: str) -> dict:
        """
            Get the content of a Wikipedia page

            :param topic: str - topic of the Wikipedia page

            :return: content of the Wikipedia page structured as dictionary
        """
        # get page content
        page = self.wiki_client.page(topic.replace(' ', '_'))
        if not page.exists():
            raise ValueError(f"Page not found with name '{topic}'.")

        # structure the content
        data = {
            'topic': topic,
            'title': page.title,
            'sections': ['Summary. ' + page.summary]
        }
        for section in page.sections:
            if section.text != "":
                data['sections'].append(section.title + "." + section.text)

        return data