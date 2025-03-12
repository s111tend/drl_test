
## Description

The task is to create an application with an API (FastAPI) that will have THREE routes inside and a background task processor. The application must gather data about the requested topic from Wikipedia, structure it, and place it into the TXT file (named by the given `document_id`) in the local `data/documents` folder.   
On the other side, it is necessary to implement a route to chat with ChatGPT using the information from a specified document and previous chat history. To have a chat history, it is necessary to work with an additional folder `data/sessions` to store conversation history into a JSON file named with a given `session_id` (on the structure chat history in the JSON file, you decide on your own).

## Environment variables
Before running the application, you need to set the following environment variables in `.env` file:

```
    OPENAI_API_KEY=sk-...
```

You can also use some additional parameters if you want:

```
    # relative path to the data folder:
    DOCUMENTS_PATH=... # standard: data/documents/

    # relative path to the sessions folder:
    SESSIONS_PATH=... # standard: data/sessions/

    WIKI_API_USER_AGENT=... # standard: chat-app
    WIKI_API_LANGUAGE=... # standard: en

    # openai embedding model and embedding size (the size of embedding is automatically set to the real value if you set it to a wrong one):
    EMBEDDING_MODEL=... # standard: text-embedding-3-small
    EMBEDDING_SIZE=... # standard: 1536

    # relative path to the folder with vector db components:
    FAISS_INDEX_PATH=... # standard: data/faiss_index/

    # openai llm to use
    GPT_MODEL=... # standard: gpt-4
```

## Running instructions

After clonning the repository, you can build and run it with docker using Dockerfile:

```
    docker build -t chat_app .
    docker run -p 8000:8000 chat_app
```

or with Docker-compose.yml file:

```
    docker-compose up --build
```

When container is running, you can access the API using URL: `http://localhost:8000/`.

## API Routes

### 1. Processing [`/api/v1/process`]
The POST route aims to create a task to gather textual information from Wikipedia in the background. It receives the user's request, creates a new background task, and returns the corresponding identifier `task_id` to the user.
    
```
JSON Request Format:   
{
    "topic": str,
    "document_id": str 
}
   
JSON Response format:   
{
    "task_id": str
}
```
    
Examples of a valid topic in the user request:
- "Kyiv Oblast"
- "Volodymyr Zelenskyy"
- "Kyiv Polytechnic Institute"


### 2. Status [`/api/v1/status/{task_id}`]
The GET route accepts the `task_id` path parameter and returns its current status.   

```
JSON Response format:
{
    "status": str
}
```

### 3. Chatting [`/api/v1/chat`]
The POST route accepts user questions in the `text` field, `document_id` and `session_id` and returns relevant answers using the information from `data/documents/{document_id}.txt`.   

The `session_id` input attribute will help to distinguish one conversation from another, so the chat histories for each session will be stored independently in `data/sessions` folder.

```
JSON Request Format:
{
    "session_id": str, (any string could be here)
    "document_id": str, (any string could be here)
    "text": str
}

JSON Response format:

{
    "response": str
}
```


## Implementation details

### Retrivement of relevent information
Since the search for relevant information should be carried out on the text of a particular document, saving and selecting this information is as follows:
1. When saving information into a document, the embedding of each chapter of the document is saved in a single vector database, and an index map is created to obtain embedding indices related to a particular chapter of a particular document.
2. When selecting the required information, the two most relevant chapters of the document to which the question refers are found first. The text from these chapters is then divided into small passages and the most relevant passages are selected using a time vector database, which are then used to obtain the desired answer.

### AI agent settings
If there is no chatting session with given id, the application creates a new one with message to agent from system. This message contains instructions how to deal with situation when found context from document is not enough to answer question. In this case the agent will answer that it doesn't have enaugh information and it will try to answer by itself.