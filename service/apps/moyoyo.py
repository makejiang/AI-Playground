# filepath: c:\Users\asd\Source\AI-Playground\service\apps\moyoyo.py
import os
import subprocess
import logging
import time
from . import winutils
from .base_app import BaseApp

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class app(BaseApp):
    def __init__(self):
        super().__init__()
        self.app_count = 5

    def run_stream(self, process_name, installed_name):
        logger.info(f"runapp stream: {process_name}")

        path_dir = winutils.get_install_location_reg(installed_name)
        path_exe = os.path.join(path_dir, process_name)
        if not os.path.exists(path_exe):
            logger.error(f"runapp: {path_exe} not found")
            return 'data:{"state":"not-installed", "message":"is the app installed correctly?"}\0'

        logger.info(f"calling cmd process: {path_exe}")
        subprocess.Popen([path_exe], shell=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, cwd=path_dir)
        self.app_count = 2

        time.sleep(2)  # give some time for the process to start
        return self._report_running_process(process_name)

    def is_running(self, process_name: str):
        count = winutils.appisrunning_count(process_name.split('\\')[-1])
        logger.info(f"Process '{process_name}' is running {count} times")
        if count >= self.app_count:
            return True
        else:
            self.close(process_name)
            return False


app_instance = app()
