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

    # def close(self, process_name: str):
    #     logger.info(f"closeapp: {process_name}")
        
    #     # kill the process
    #     for proc in psutil.process_iter(attrs=['name', 'pid']):
    #         try:
    #             if proc.info['name'] == process_name:
    #                 subprocess.run(["taskkill", "/F", "/PID", str(proc.info['pid'])], check=True)
    #         except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
    #             logger.error(f"Error closing process {process_name}: {proc.info['pid']}")
    #             continue


    #     return True

    # def _report_running_process(self, process_name: str):
    #     # wait for the process to start
    #     count = 10
    #     while not winutils.appisrunning(process_name):
    #         time.sleep(0.3)
    #         count -= 1
    #         if count < 0:
    #             logger.error(f"'{process_name}' did not start in time")
    #             yield 'data:{"state":"installed", "message":"Installation failed, process did not start"}\0'
    #             return

    #     yield 'data:{"state":"running"}\0'
    #     self._report_process_running(process_name)

app_instance = app()