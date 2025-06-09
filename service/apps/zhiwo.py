import os
import psutil
import subprocess
import logging
import win32api, win32con
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
        logger.info(f"app location: {path_dir}")

        path_exe = os.path.join(path_dir, process_name)
        if not os.path.exists(path_exe):
            logger.error(f"runapp: {path_exe} not found")
            return 'data:{"state":"not-installed", "message":"is the app installed correctly?"}\0'

        logger.info(f"calling cmd process: {path_exe}")
        try:
            win32api.ShellExecute(
                        0, 
                        "runas", 
                        path_exe, 
                        None, 
                        None, 
                        win32con.SW_SHOWNORMAL
                    )
        except Exception as e:
            logger.error(f"Error starting process {process_name}: {e}")
            return 'data:{"state":"installed", "message":"Failed to start the application"}\0'
            
        return self._report_running_process(process_name)

app_instance = app()