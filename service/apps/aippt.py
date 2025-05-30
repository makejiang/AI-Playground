import os, subprocess
import logging
import time
import psutil
import shlex
import threading
import win32api, win32con
from . import winutils

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class app:
    def __init__(self):
        ...

    def is_running(self, process_name: str):
        return winutils.appisrunning(process_name.split('\\')[-1])
    
    def is_installed(self, install_name: str):
        return winutils.appisinstalled(install_name)

    def install(self, app_name: str, installer: str):
        # Placeholder for installation logic
        logger.info(f"Installing {app_name}...")
        
        # get the path of this script
        path_installer = os.path.join(winutils.get_download_folder(), "_aipg_apps", installer)
        if not os.path.exists(path_installer):
            return False

        logger.info(f"calling cmd process: {path_installer}")
        ret = subprocess.call([path_installer], shell=True)
        return ret==0

    def install_stream(self, app_name: str, installer: str, installed_name: str):
        # Placeholder for installation logic
        logger.info(f"Installing {app_name} with stream mode...")
        
        # get the path of this script
        path_installer = winutils.get_installer_path(installer)
        if not path_installer:
            return 'data:{"state":"not-installed", "message":"Can not find the installer"}\0'

        logger.info(f"calling cmd process: {path_installer}")
        # subprocess.Popen([path_installer], shell=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        try:
            win32api.ShellExecute(
                0, 
                "runas", 
                path_installer, 
                None, 
                None, 
                win32con.SW_SHOWNORMAL
            )
        except Exception as e:
            logger.error(f"Failed to launch installer with admin privileges: {e}")
            return 'data:{"state":"not-installed", "message":"Installation failed, could not start installer"}\0'
        #if ret:
        #    threading.Thread(target=self.__report_process_running, kwargs={"process_name": installer, "installed_name": installed_name}).start()
        return self.__report_install_process(installer, installed_name)

    def __report_install_process(self, process_name: str, installed_name: str):
        logger.info(f"report_process_running: {process_name}")
        
        # wait for the process to start
        count = 10
        while not winutils.appisrunning(process_name):
            time.sleep(0.3)
            count -= 1
            if count < 0:
                logger.error(f"'{process_name}' did not start in time")
                yield 'data:{"state":"not-installed", "message":"Installation failed, process did not start"}\0'
                return

        # wait for the process to finish
        while winutils.appisrunning(process_name):
            yield 'data:{"state":"installing"}\0'
            time.sleep(1)

        logger.info(f"'{process_name}' disappeared")

        # check if the app is installed
        ret = winutils.appisinstalled(installed_name)
        if ret:
            logger.info(f"'{installed_name}' is installed")
            yield 'data:{"state":"installed", "message":"Installation completed successfully"}\0'
        else:
            logger.info(f"'{installed_name}' is not installed")
            yield 'data:{"state":"not-installed", "message":"Installation failed"}\0'

    
    def uninstall(self, installed_name: str, uninstall_process_name=None):
        path_uninstall = winutils.get_uninstall_string(installed_name)
        logger.info(f"uinstall string: {path_uninstall}")
        
        if not path_uninstall:
            return False
        
        # replace "Program Files" with "Program-Files"
        # replace "Program Files (x86)" with "Program-Files-(x86)"
        path_uninstall = path_uninstall.replace("Program Files (x86)", "Program-Files-(x86)")
        path_uninstall = path_uninstall.replace("Program Files", "Program-Files")
        
        cmds = shlex.split(path_uninstall)

        # restore "Program-Files" to "Program Files"
        if len(cmds) > 1:
            cmds[0] = cmds[0].replace("Program-Files-(x86)", "Program Files (x86)")
            cmds[0] = cmds[0].replace("Program-Files", "Program Files")
            
            ret = subprocess.call(cmds, shell=True)    
        else:
            path_uninstall = path_uninstall.replace("Program-Files-(x86)", "Program Files (x86)")
            path_uninstall = path_uninstall.replace("Program-Files", "Program Files")
            
            # remove '"' at the begin and end if exists
            if path_uninstall.startswith('"') and path_uninstall.endswith('"'):
                path_uninstall = path_uninstall[1:-1]

            ret = subprocess.call([path_uninstall], shell=True)

        if ret!=0:
            logger.error(f"run uninstall cmd failed: {installed_name}, ret:  {ret}")
            return False

        # wait for uninstall window to close
        if uninstall_process_name:
            logger.info(f"waiting for '{uninstall_process_name}' appear")
            while not winutils.appisrunning(uninstall_process_name):
                time.sleep(0.3)
                # count -= 1
                # if count < 0:
                #     break
            logger.info(f"'{uninstall_process_name}' is running")

            # wait for the uninstall window to close
            while winutils.appisrunning(uninstall_process_name):
                time.sleep(1)

            logger.info(f"'{uninstall_process_name}' disappeared")

            # wait for the uninstall process to finish
            count = 10
            while winutils.get_uninstall_string(installed_name) is not None:
                time.sleep(1)
                count -= 1
                if count <= 0:
                    return False
        
        return True

    def uninstall_stream(self, installed_name: str, uninstall_process_name=None):
        path_uninstall = winutils.get_uninstall_string(installed_name)
        logger.info(f"uinstall string: {path_uninstall}")
        
        if not path_uninstall:
            return 'data:{"state":"not-installed", "message":"Can not find the app"}\0'
        
        path_uninstall = path_uninstall.replace("Program Files (x86)", "Program-Files-(x86)")
        path_uninstall = path_uninstall.replace("Program Files", "Program-Files")
        
        cmds = shlex.split(path_uninstall)

        try:
            # restore "Program-Files" to "Program Files"
            if len(cmds) > 1:
                cmds[0] = cmds[0].replace("Program-Files-(x86)", "Program Files (x86)")
                cmds[0] = cmds[0].replace("Program-Files", "Program Files")
                
                # subprocess.Popen(cmds, shell=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
                win32api.ShellExecute(
                    0, 
                    "runas", 
                    cmds[0], 
                    ' '.join(cmds[1:]), # parameters are passed as a list 
                    None, 
                    win32con.SW_SHOWNORMAL
                )
            else:
                path_uninstall = path_uninstall.replace("Program-Files-(x86)", "Program Files (x86)")
                path_uninstall = path_uninstall.replace("Program-Files", "Program Files")
                
                # remove '"' at the begin and end if exists
                if path_uninstall.startswith('"') and path_uninstall.endswith('"'):
                    path_uninstall = path_uninstall[1:-1]

                # subprocess.Popen([path_uninstall], shell=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
                win32api.ShellExecute(
                    0, 
                    "runas", 
                    path_uninstaller, 
                    None, 
                    None, 
                    win32con.SW_SHOWNORMAL
                )
        except Exception as e:
            logger.error(f"Failed to launch uninstaller with admin privileges: {e}")
            return 'data:{"state":"installed", "message":"Uninstallation failed, could not start uninstaller"}\0'

        if uninstall_process_name:
            return self.__report_uninstall_process(installed_name, uninstall_process_name)
        
        return 'data:{"state":"not-installed", "message":"uninstallation completed successfully"}\0'

    def __report_uninstall_process(self, installed_name: str, uninstall_process_name=None):
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



    def run(self, process_name, installed_name):
        logger.info(f"runapp: {process_name}")

        path_dir = winutils.get_install_localtion(installed_name)
        if not path_dir:
            logger.error(f"runapp: {installed_name} not installed")
            return False

        path_exe = os.path.join(path_dir, process_name)
        if not os.path.exists(path_exe):
            logger.error(f"runapp: {path_exe} not found")
            return False
        
        logger.info(f"calling cmd process: {path_exe}")
        subprocess.Popen([path_exe], shell=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        return True

    def close(self, process_name: str):
        logger.info(f"closeapp: {process_name}")
        
        process_name = process_name.split('\\')[-1]
        for proc in psutil.process_iter(attrs=['name', 'pid']):
            if proc.info['name'] == process_name:
                proc.terminate()
                proc.wait()  # Wait for the process to terminate

        return True


app_instance = app()