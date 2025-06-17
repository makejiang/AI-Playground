# filepath: c:\Users\asd\Source\AI-Playground\service\apps\moyoyo.py
import os
import subprocess
import logging
import time
import psutil
from . import winutils
from .base_app import BaseApp

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class app(BaseApp):
    def __init__(self):
        super().__init__()

    def run_stream(self, process_name, installed_name):
        logger.info(f"runapp stream: {process_name}")

        path_dir = winutils.get_install_location(installed_name)
        path_exe = os.path.join(path_dir, process_name)
        path_work = os.path.join(path_dir, 'Model\\llm-service')

        if not os.path.exists(path_exe):
            logger.error(f"runapp: {path_exe} not found")
            return 'data:{"state":"not-installed", "message":"is the app installed correctly?"}\0'

        logger.info(f"calling cmd process: {path_exe}")
        subprocess.Popen([path_exe], shell=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, cwd=path_work)

        # time.sleep(2)  # give some time for the process to start
        return self._report_running_process(process_name.split('\\')[-1])

    def _report_running_process(self, process_name):
        # wait for the process to start
        count = 10
        while not self.is_running(process_name):
            time.sleep(0.9)
            count -= 1
            if count < 0:
                logger.error(f"'{process_name}' did not start in time")
                yield 'data:{"state":"installed", "message":"Application failed to start"}\0'
                return

        # wait for the process to finish
        while self.is_running(process_name):
            yield 'data:{"state":"running"}\0'
            time.sleep(1)

        yield 'data:{"state":"installed", "message":"look like the app is closed"}\0'

    def close(self, process_name: str):
        logger.info(f"closeapp: {process_name}")
        
        process_name = process_name.split('\\')[-1]
        for proc in psutil.process_iter(attrs=['name', 'pid']):
            try:
                if proc.info['name'] == process_name:
                    proc.terminate()
                    proc.wait()  # Wait for the process to terminate
            except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
                logger.error(f"Error closing process {process_name}: {proc.info['pid']}")
                continue

        return True


app_instance = app()
