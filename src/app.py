from fastapi import FastAPI, BackgroundTasks, HTTPException
from pydantic import BaseModel
from openai import OpenAI

import uvicorn
import uuid
import logging
from manage import Retriever, TaskManager, ChatManager, get_path, Config


app = FastAPI()


# initialize logger
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    handlers=[logging.StreamHandler()]
)

# initialize openai client and other components
openai_client = OpenAI(api_key=Config.OPENAI_API_KEY)
retriever = Retriever(openai_client)
task_manager = TaskManager(retriever)
chat_manager = ChatManager(retriever, openai_client)


class ProcessInputs(BaseModel):
    topic: str
    document_id: str

class ChatInputs(BaseModel):
    session_id: str
    document_id: str
    text: str
    

@app.post("/api/v1/process")
async def process(inputs: ProcessInputs, background_tasks: BackgroundTasks):
    """
        Accept textual requests and launch a background task to gather textual information from Wikipedia.
        It should receive the user's request and start a background task for processing. After starting a task,
        it should return an identifier for the task.

        The results should be stored as a file `{document_id}.txt` in the `data/documents` directory.

        Examples of a valid user request:
        - Kyiv
        - Isaac Newton
        - Spider-man

        :return: task_id of the background task that was started
    """
    
    # set unique task_id
    task_id = str(uuid.uuid4())

    # assign task
    task_manager.assign_task(task_id)

    # start background task
    background_tasks.add_task(
        task_manager.process_task, 
        task_id=task_id, 
        topic=inputs.topic, 
        document_id=inputs.document_id
    )

    return {"task_id": task_id}, 202


@app.get("/api/v1/status/{task_id}")
async def status(task_id: str):
    """
        Check the status of the background task. It should receive a task_id path parameter and return the status of the task.
        The task can have four possible statuses: pending, running, finished, or failed.

        :param task_id: str

        :return: status of the background task (pending, running, finished, or failed)
    """
    code = 200

    # get task status
    task_status = task_manager.get_task_status(task_id)
    if task_status is None:
        code = 404 

    return {"status": task_status}, code


@app.post("/api/v1/chat")
async def chat(inputs: ChatInputs):
    """
    Endpoint for interaction with СhatGPT. The document with `document_id` identifier should be inserted
    into СhatGPT prompt, so the user will be able to chat about specific topic.

    The session history should be persistent and stored as `{session_id}.json` in the `data/sessions` directory
    in a JSON format. So, each time you call the `chat` endpoint, session history will be pulled from the file and used
    for generation.

    :param inputs: ChatInputs
        1. session_id – session identifier to keep track of the conversation.
        2. document_id - identified of a textual document to insert into prompt.
        2. text – user input text

    :return: bot response
    """

    # get chat response
    response, code = chat_manager.get_chat_response(
        session_id=inputs.session_id, 
        document_id=inputs.document_id, 
        inputs=inputs.text
    )

    return {"response": response}, code


@app.get("/-/healthy/")
async def healthy():
    return {}, 200