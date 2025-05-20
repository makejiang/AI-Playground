import requests
import json
import os
import logging
from flask import jsonify

from modelscope.hub.api import HubApi
from modelscope.hub.utils.utils import (get_endpoint)
from modelscope.hub.file_download import (create_temporary_directory_and_cache,
                                          download_file, get_file_download_url)

_api = HubApi()
print(get_endpoint())

logging.basicConfig(level=logging.INFO)


def get_tasks_name_from_repo(repo_id: str) -> str:
    """
    Extract task names from model metadata retrieved from the specified API URL or local file.
    
    Args:
        repo_id: The ID of the repository to fetch model metadata from.

    Returns:
        A string of task names from the model metadata. Empty string if no tasks found or if API call fails.
    """
    try:
        api_url = f"{_api.endpoint}/api/v1/models/{repo_id}"
        response = requests.get(api_url)
        if response.status_code != 200:
            logging.error(f"Failed to fetch model metadata from {api_url}. Status code: {response.status_code}")
            return "reponotfound"

        data = response.json()
                
        # Check if the response has the expected structure
        if data.get("Code")!=200 or "Data" not in data:
            logging.error(f"Invalid response format from {api_url}")
            return "wrong1"
        
        # Extract tasks from the Data section
        task = data.get("Data", {}).get("Tasks", [])[0]
        return task.get("Name", "notask")
    
    except Exception as e:
        logging.error(f"Error extracting tasks from model metadata: {e}")
        return "wrong2"


def list_files_in_repo(repo_id: str) -> list:
    """
    List all files in the specified repository.
    
    Args:
        repo_id: The ID of the repository to list files from.

    Returns:
        A list of file paths in the repository. Empty list if API call fails.
    """
    repo_files = _api.get_model_files(model_id=repo_id,
                                      recursive=True)
    files = []
    for file in repo_files:
        if file["Type"] == "blob" and not file["Path"].endswith(('.jpg', '.jpeg', '.md', '.png', '.pdf', '.txt')):
            #url = f"{_api.endpoint}/models/{repo_id}/file/view/master/{file['Path']}"
            url = get_file_download_url(repo_id, file["Path"], revision='master')
            files.append({"name": file["Path"], "size": file["Size"], "url": url})

    return files


if __name__ == "__main__":
    # Example usage
    print("")
    print("**********Testing get_tasks_name_from_repo function**********")
    #repo_id = "MusePublic/DreamShaper_SD_1_5"
    repo_id = "Yntec/Dreamshaper8"
    files = list_files_in_repo(repo_id)
    print(f"Done:")

    #pretty print the lists
    for item in files:
        print(f"Name: {item['name']}, Size: {item['size']}B, Url: {item['url']}")

    # exit

    # print("")
    # print("**********Testing get_tasks_name_from_repo function**********")
    # repo_id = "Qwen/Qwen3-1.7B-GGUF"
    # tasks_name = get_tasks_name_from_repo(repo_id)
    # print(f"Tasks name for {repo_id}: {tasks_name}")

    # print("")
    # print("**********Testing get_tasks_name_from_repo function**********")
    # repo_id = "MusePublic/DreamShaper_SD_1_5"
    # tasks_name = get_tasks_name_from_repo(repo_id)
    # print(f"Tasks name for {repo_id}: {tasks_name}")

    # print("")
    # print("**********Testing get_tasks_name_from_repo function**********")
    # repo_id = "Qwen/Qwen3-1.7B-GGUF1"
    # tasks_name = get_tasks_name_from_repo(repo_id)
    # print(f"Tasks name for {repo_id}: {tasks_name}")
