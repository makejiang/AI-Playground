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

    def run_stream(self, process_name, installed_name):
        logger.info(f"runapp stream: {process_name}")

        path_dir = winutils.get_install_location_reg(installed_name)
        path_exe = os.path.join(path_dir, process_name)
        if not os.path.exists(path_exe):
            logger.error(f"runapp: {path_exe} not found")
            return 'data:{"state":"not-installed", "message":"is the app installed correctly?"}\0'

        logger.info(f"calling cmd process: {path_exe}")
        subprocess.Popen([path_exe], shell=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, cwd=path_dir)
        time.sleep(1)  # give some time for the process to start

        return self._report_running_process(process_name)

    def _report_uninstall_process(self, installed_name: str, uninstall_process_name=None):
        # wait for the process to start
        count = 10
        while not winutils.appisrunning(uninstall_process_name):
            time.sleep(0.3)
            count -= 1
            if count < 0:
                logger.error(f"'{uninstall_process_name}' did not start in time")
                yield 'data:{"state":"error", "message":"Uninstallation failed, process did not start"}\0'
                return

        # wait for the process to finish
        while winutils.appisrunning(uninstall_process_name):
            if not winutils.appisinstalled(installed_name):
                logger.info(f"'{installed_name}' is not installed anymore")
                yield 'data:{"state":"not-installed", "message":"uninstallation completed successfully"}\0'
                return

            yield 'data:{"state":"uninstalling"}\0'
            time.sleep(1)

        logger.info(f"'{uninstall_process_name}' disappeared")
        # check if the app is installed
        ret = winutils.appisinstalled(installed_name)
        if ret:
            logger.info(f"'{installed_name}' is installed")
            yield 'data:{"state":"installed", "message":"uninstallation failed"}\0'
        else:
            logger.info(f"'{installed_name}' is not installed")
            yield 'data:{"state":"not-installed", "message":"uninstallation completed successfully"}\0'

app_instance = app()