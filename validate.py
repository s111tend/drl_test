import requests
import time

def wiki_parse_request(topic: str, document_id: str):
    # process wiki page parsing using topic and document id
    return requests.post(
        "http://127.0.0.1:8000/api/v1/process", 
        json={'topic': topic, 'document_id': document_id}
    ).json()

def task_status_request(task_id: str):
    # process task status request by task id
    return requests.get(f"http://127.0.0.1:8000/api/v1/status/{task_id}").json()

def chat_request(session_id: str, document_id: str, text: str):
    # process chat request by session id, document id and input
    return requests.post(
        "http://127.0.0.1:8000/api/v1/chat",
        json={'session_id': session_id, 'document_id': document_id, 'text': text}
    ).json()


if __name__ == '__main__':
    document_id1 = 'document_001'
    document_id2 = 'document_002'
    session_id = 'session_001'

    valid_topic = 'Kyiv'
    invalid_topic = 'fwbfiuhrevhriubhfej'

    # process valid task
    valid_topic_task_id = wiki_parse_request(valid_topic, document_id1)[0]['task_id']

    time.sleep(5)

    # try to process task with incorrect document_id
    invalid_document_task_id = wiki_parse_request(valid_topic, document_id1)[0]['task_id']

    # try to process task with incorrect topic
    invalid_topic_task_id = wiki_parse_request(invalid_topic, document_id2)[0]['task_id']

    # create incorrect task_id
    invalid_task_id = 'ngjrengregergbnh'

    time.sleep(20)

    assert task_status_request(valid_topic_task_id)[0]['status'] == 'finished'
    assert task_status_request(invalid_document_task_id)[0]['status'] == 'failed'
    assert task_status_request(invalid_topic_task_id)[0]['status'] == 'failed'
    assert task_status_request(invalid_task_id)[0]['status'] is None

    question = 'When was Kyiv founded?'
    print(chat_request(session_id, document_id1, question)[0]['response'])