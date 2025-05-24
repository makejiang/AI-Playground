import concurrent.futures
import os
import queue
import shutil
import logging
import time
import traceback
from os import path, makedirs, rename
from threading import Thread, Lock
from time import sleep
from typing import Any, Callable, Dict, List

import psutil
import requests

from modelscope.hub.api import HubApi
from modelscope.hub.utils.utils import (get_endpoint)
from modelscope.hub.file_download import (create_temporary_directory_and_cache,
                                          download_file, get_file_download_url)

from psutil._common import bytes2human

import aipg_utils as utils
from exceptions import DownloadException

import urllib3

urllib3.disable_warnings()

model_list_cache = dict()
model_lock = Lock()

class MSFileItem:
    relpath: str
    size: int
    url: str
    url_grant: str

    def __init__(self, relpath: str, size: int, url: str, url_grant: str) -> None:
        self.relpath = relpath
        self.size = size
        self.url = url
        self.url_grant = url_grant


class MSDownloadItem:
    name: str
    size: int
    url: str
    url_grant: str
    disk_file_size: int
    save_filename: str

    def __init__(
        self, name: str, size: int, url: str, url_grant: str, disk_file_size: int, save_filename: str
    ) -> None:
        self.name = name
        self.size = size
        self.url = url
        self.url_grant = url_grant
        self.disk_file_size = disk_file_size
        self.save_filename = save_filename


class NotEnoughDiskSpaceException(Exception):
    requires_space: int
    free_space: int

    def __init__(self, requires_space: int, free_space: int):
        self.requires_space = requires_space
        self.free_space = free_space
        message = "Not enough disk space. It requires {}, but only {} of free space is available".format(
            bytes2human(requires_space), bytes2human(free_space)
        )
        super().__init__(message)



class MSPlaygroundDownloader:
    hub_api: HubApi
    file_queue: queue.Queue[MSDownloadItem]
    total_size: int
    download_size: int
    prev_sec_download_size: int
    on_download_progress: Callable[[str, int, int, int], None] = None
    on_download_completed: Callable[[str, Exception], None] = None
    thread_alive: int
    thread_lock: Lock
    download_stop: bool
    completed: bool
    wait_for_complete: bool
    repo_id: str
    save_path: str
    save_path_tmp: str
    error: Exception
    ms_token: str | None

    def __init__(self, ms_token=None) -> None:
        #self.fs = MsFileSystem()
        self.hub_api = HubApi()
        self.total_size = 0
        self.download_size = 0
        self.thread_lock = Lock()
        self.ms_token = ms_token

    def hf_url_exists(self, repo_id: str):
        return self.hub_api.repo_exists(repo_id)

    def probe_type(self, repo_id : str):
        # "text-generation" or "image-generation"
        # "text-to-image" or "image-to-image"
        return utils.get_tasks_name_from_repo(repo_id)

    def is_gated(self, repo_id: str):
        return False

    def download(self, repo_id: str, model_type: int, backend: str, thread_count: int = 2):
        print(f"download {repo_id} at {backend}")
        self.repo_id = repo_id
        self.total_size = 0
        self.download_size = 0
        self.file_queue = queue.Queue()
        self.download_stop = False
        self.completed = False
        self.error = None
        self.save_path = path.join(utils.get_model_path(model_type, backend))
        logging.info(f"save_path: {self.save_path}")        
        self.save_path_tmp = path.abspath(
            path.join(self.save_path, repo_id.replace("/", "---") + "_tmp")
        )

        if not path.exists(self.save_path_tmp):
            makedirs(self.save_path_tmp)

        key = f"{repo_id}_{model_type}"
        cache_item = model_list_cache.get(key)
        if cache_item is None:
            file_list = list()
            self.enum_file_list(file_list, repo_id, model_type)

            model_list_cache.__setitem__(key, {"size": self.total_size, "queue": self.file_queue})
        else:
            self.total_size = cache_item["size"]
            file_list: list = cache_item["queue"]

        self.build_queue(file_list)

        usage = psutil.disk_usage(self.save_path)
        if self.total_size - self.download_size > usage.free:
            raise NotEnoughDiskSpaceException(
                self.total_size - self.download_size, usage.free
            )
        self.multiple_thread_download(thread_count)


    def build_queue(self, file_list: list[MSFileItem]):
        for file in file_list:
            save_filename = path.abspath(path.join(self.save_path_tmp, file.relpath))
            if path.exists(save_filename):
                local_file_size = path.getsize(save_filename)
                self.download_size += local_file_size
                # if local file size less thand network file size download it, else skip it!
                if local_file_size < file.size:
                    self.file_queue.put(
                        MSDownloadItem(
                            file.relpath,
                            file.size,
                            file.url,
                            file.url_grant,
                            local_file_size,
                            save_filename,
                        )
                    )
            else:
                self.file_queue.put(
                    MSDownloadItem(file.relpath, file.size, file.url, file.url_grant, 0, save_filename)
                )

    def get_model_total_size(self, repo_id: str, model_type: int):
        key = f"{repo_id}_{model_type}"
        
        self.repo_id = repo_id
        with model_lock:
            item = model_list_cache.get(key)

        logging.info(f"get model total size {key}, item: {item}")
        if item is None:
            file_list = list()
            self.enum_file_list(file_list, repo_id, model_type)
            with model_lock:
                model_list_cache.__setitem__(
                    key, {"size": self.total_size, "queue": file_list}
                )
            return self.total_size
        else:
            return item["size"]

    def _get_grant_url(self, file_path: str, revision: str = "master") -> str:
        return f"{get_endpoint()}/models/{self.repo_id}/revolve/{revision}/{file_path}"

    def enum_file_list(
        self, file_list: List, enum_path: str, model_type: int, is_root=True
    ):
        # repo = "/".join(enum_path.split("/")[:2])
        model_id = "/".join(enum_path.split("/")[:2])
        file_path = "/".join(enum_path.split("/")[2:])

        self.total_size = 0
        try:
            repo_files = self.hub_api.get_model_files(model_id=model_id, recursive=True)
            for file in repo_files:
                if len(file_path) > 0:
                    if file["Path"] == file_path:
                        self.total_size += file["Size"]
                        url = get_file_download_url(model_id=model_id, file_path=file["Path"], revision='master')
                        url_grant = self._get_grant_url(file["Path"], revision='master')
                        file_list.append(MSFileItem(file["Path"], file["Size"], url, url_grant))
                        break
                elif file["Type"] == "blob" and not file["Path"].endswith(('.jpg', '.jpeg', '.md', '.png', '.pdf')):
                    self.total_size += file["Size"]
                    url = get_file_download_url(model_id=model_id, file_path=file["Path"], revision='master')
                    url_grant = self._get_grant_url(file["Path"], revision='master')
                    file_list.append(MSFileItem(file["Path"], file["Size"], url, url_grant))

            logging.info(f"total size: {self.total_size}")
        except Exception as e:
            logging.error(f"get model files failed: {e}")
            

    def multiple_thread_download(self, thread_count: int):
        self.download_stop = False

        if self.on_download_progress is not None:
            self.prev_sec_download_size = 0
            report_thread = self.start_report_download_progress()

        with concurrent.futures.ThreadPoolExecutor(max_workers=thread_count) as executor:
            futures = [
                executor.submit(self.download_model_file)
                for _ in range(min(thread_count, self.file_queue.qsize()))
            ]
            concurrent.futures.wait(futures)
            executor.shutdown()
        
        self.completed = True
        if report_thread is not None:
            report_thread.join()

        if self.on_download_completed is not None:
            self.on_download_completed(self.repo_id, self.error)

        if not self.download_stop and self.error is None:
            self.move_to_desired_position()
        else:
            # Download aborted
            shutil.rmtree(self.save_path_tmp)

    def move_to_desired_position(self, retriable: bool = True):
        desired_repo_root_dir_name = os.path.join(self.save_path, utils.repo_local_root_dir_name(self.repo_id))
        move_to_flat_structure = False
        # face restore and insightface model need to be in a flat structure to work with reactor node
        if "facerestore" in self.save_path or "insightface" in self.save_path:
            move_to_flat_structure = True
            desired_repo_root_dir_name = path.abspath(path.join(self.save_path, self.repo_id.replace("/", "---")))
        elif "nsfw_detector" in self.save_path:
            move_to_flat_structure = True
            desired_repo_root_dir_name = path.abspath(path.join(self.save_path, 'vit-base-nsfw-detector'))
            if not os.path.exists(desired_repo_root_dir_name):
                os.makedirs(desired_repo_root_dir_name)
        try:
            if os.path.exists(desired_repo_root_dir_name) or move_to_flat_structure:
                for item in os.listdir(self.save_path_tmp):
                    shutil.move(os.path.join(self.save_path_tmp, item), desired_repo_root_dir_name)
                shutil.rmtree(self.save_path_tmp)
            else:
                rename(
                    self.save_path_tmp,
                    path.abspath(desired_repo_root_dir_name)
                )
        except Exception as e:
            if (retriable):
                sleep(5)
                self.move_to_desired_position(retriable=False)
            else:
                raise e

    def start_report_download_progress(self):
        thread = Thread(target=self.report_download_progress)
        thread.start()
        return thread

    def report_download_progress(self):
        while not self.download_stop and not self.completed:
            self.on_download_progress(
                self.repo_id,
                self.download_size,
                self.total_size,
                self.download_size - self.prev_sec_download_size,
            )

            self.prev_sec_download_size = self.download_size
            time.sleep(1)

    def init_download(self, file: MSDownloadItem):
        path_file = path.dirname(file.save_filename)
        makedirs(path_file, exist_ok=True)

        headers = {}
        if self.ms_token is not None:
            headers["Authorization"] = f"Bearer {self.ms_token}"

        if file.disk_file_size > 0:
            # download skip exists part
            headers["Range"] = f"bytes={file.disk_file_size}-"
            response = requests.get(
                file.url,
                stream=True,
                verify=False,
                headers=headers,
            )
            fw = open(file.save_filename, "ab")
        else:
            response = requests.get(
                file.url, stream=True, verify=False, headers=headers
            )
            fw = open(file.save_filename, "wb")

        return response, fw

    def is_access_granted(self, repo_id: str, model_type, backend : str):

        repo_id = utils.trim_repo(repo_id)
        headers={}
        if (self.ms_token is not None):
            headers["Authorization"] = f"Bearer {self.ms_token}"

        self.file_queue = queue.Queue()
        self.repo_id = repo_id
        self.save_path = path.join(utils.get_model_path(model_type,backend))
        self.save_path_tmp = path.abspath(
            path.join(self.save_path, repo_id.replace("/", "---") + "_tmp")
        )

        file_list = list()
        self.enum_file_list(file_list, repo_id, model_type)
        self.build_queue(file_list)
        file = self.file_queue.get_nowait()

        logging.info(f"file: {file}")
        response = requests.head(file.url_grant, verify=False, headers=headers, allow_redirects=True)
        logging.info(f"file url check response: {response.status_code}")

        return response.status_code == 200


    def download_model_file(self):
        try:
            while not self.download_stop and not self.file_queue.empty():
                file = self.file_queue.get_nowait()
                #print(f"start download file: {file.url}")
                download_retry = 0
                while True:
                    try:
                        response, fw = self.init_download(file)
                        if response.status_code != 200:
                            download_retry += 1  # we only want to retry once in case of non network errors
                            raise DownloadException(file.url)
                        # start download file
                        with response:
                            with fw:
                                for bytes in response.iter_content(chunk_size=8192):
                                    download_len = bytes.__len__()
                                    with self.thread_lock:
                                        self.download_size += download_len
                                    file.disk_file_size += fw.write(bytes)

                                    if self.download_stop:
                                        print(
                                            f"thread {Thread.native_id} exit by user stop"
                                        )
                                        break
                        break
                    except Exception:
                        traceback.print_exc()
                        download_retry += 1
                        if download_retry < 4:
                            print(
                                f"download file {file.url} failed. retry {download_retry} time"
                            )
                            time.sleep(download_retry)
                        else:
                            raise DownloadException(file.url)

        except Exception as ex:
            self.error = ex
            traceback.print_exc()

    def stop_download(self):
        self.download_stop = True


def test_download_progress(repo_id: str, dowanlod_size: int, total_size: int, speed: int):
    print(f"download {dowanlod_size}/{total_size}  speed {speed}/s")


def test_download_complete(repo_id: str, ex: Exception):
    if ex is None:
        print("download success")
    else:
        print(f"{ex}")


def init():
    #repo_id = "AI-ModelScope/bge-small-en-v1.5-gguf"
    repo_id = "MPlusPlus/dreamshaper-8"
    downloader = MSPlaygroundDownloader()
    expect_total_size = downloader.get_model_total_size(repo_id, 1)
    print(f"expect total size: {expect_total_size}")

    downloader.on_download_progress = test_download_progress
    downloader.on_download_completed = test_download_complete
    downloader.download(repo_id, 1, backend='default', thread_count=4)
    


if __name__ == "__main__":
    init()
