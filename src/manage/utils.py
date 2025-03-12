import os
import json

def get_path(head: str, tail: str, ext: str = '.json') -> tuple:
    """
        Get path to a file with a given head, tail and extension.
    """
    path = os.path.join(head, tail + ext)
    return path, os.path.exists(path)

def save_data(path: str, data: dict) -> None:
    """
        Save data to a file as a json object.
    """
    with open(path, 'w', encoding='utf-8') as file:
        json.dump(data, file, ensure_ascii=False, indent=4)

def read_data(path: str) -> dict:
    """
        Read data from file as a json object.
    """
    with open(path, 'r', encoding='utf-8') as file:
        data = json.load(file)
    return data