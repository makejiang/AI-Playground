import os
import psutil
import logging
import winreg
import win32gui

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def _get_reg_software_value(hkey, sw_name, key_name, wow6432=False):
    try:
        if wow6432:
            registry_key = winreg.OpenKey(hkey, r"SOFTWARE\WOW6432Node\Microsoft\Windows\CurrentVersion\Uninstall")
        else:
            registry_key = winreg.OpenKey(hkey, r"SOFTWARE\Microsoft\Windows\CurrentVersion\Uninstall")

        i = 0
        while True:
            try:
                subkey_name = winreg.EnumKey(registry_key, i)
                #print(f"subkey_name: {subkey_name}")
            except OSError:
                break

            try:
                subkey = winreg.OpenKeyEx(registry_key, subkey_name)
                display_name, _ = winreg.QueryValueEx(subkey, "DisplayName")
                #print(f"    DisplayName: {display_name}")
                if sw_name in display_name:
                    return winreg.QueryValueEx(subkey, key_name)[0]

            except WindowsError:
                pass
            

            i += 1
    except WindowsError:
        logger.error(f"Error accessing registry w: {WindowsError}")
        
    return None

def get_download_folder():
    try:
        with winreg.OpenKey(winreg.HKEY_CURRENT_USER, r'SOFTWARE\Microsoft\Windows\CurrentVersion\Explorer\Shell Folders') as key:
            downloads_folder = winreg.QueryValueEx(key, '{374DE290-123F-4565-9164-39C4925E467B}')[0]
            return downloads_folder
    except Exception as e:
        print(f"Error accessing registry: {e}")
        return None

def is_window_running(win_title):
    try:
        ret = win32gui.FindWindow(None, win_title)
        print(f"FindWindow: {ret}")
        return ret!=0
    except:
        return False

def appisinstalled(installedname: str):
    return get_uninstall_string(installedname) is not None

def appisrunning(processname: str):
    return processname in (p.name() for p in psutil.process_iter(attrs=['name']))

def get_uninstall_string(software_name):
    # path_uninstall = _get_reg_software_value(winreg.HKEY_LOCAL_MACHINE, software_name, "QuietUninstallString")
    # if path_uninstall:
    #     return path_uninstall

    path_uninstall = _get_reg_software_value(winreg.HKEY_LOCAL_MACHINE, software_name, "UninstallString")
    if path_uninstall:
        return path_uninstall
    
    path_uninstall = _get_reg_software_value(winreg.HKEY_LOCAL_MACHINE, software_name, "UninstallString", wow6432=True)
    if path_uninstall:
        return path_uninstall

    # path_uninstall = _get_reg_software_value(winreg.HKEY_CURRENT_USER, software_name, "QuietUninstallString")
    # if path_uninstall:
    #     return path_uninstall

    path_uninstall = _get_reg_software_value(winreg.HKEY_CURRENT_USER, software_name, "UninstallString")
    if path_uninstall:
        return path_uninstall
    
    path_uninstall = _get_reg_software_value(winreg.HKEY_CURRENT_USER, software_name, "UninstallString", wow6432=True)
    if path_uninstall:
        return path_uninstall

    return path_uninstall


def get_install_localtion(software_name):
    path_uninstall = get_uninstall_string(software_name)
    logger.info(f"uninstall string: {path_uninstall}")

    if not path_uninstall:
        return None
    
    path_uninstall = path_uninstall.replace("Program Files (x86)", "Program-Files-(x86)")
    path_uninstall = path_uninstall.replace("Program Files", "Program-Files")
    
    # Handle quoted paths
    if path_uninstall.startswith('"'):
        # Extract path between quotes
        quoted_path = path_uninstall.split('"')[1]
        install_dir = os.path.dirname(quoted_path)
    else:
        # Handle unquoted paths (split by space and take the first part)
        install_dir = os.path.dirname(path_uninstall.split(' ')[0])

    install_dir = install_dir.replace("Program-Files-(x86)", "Program Files (x86)")
    install_dir = install_dir.replace("Program-Files", "Program Files")
    
    logger.info(f"get_install_localtion: {install_dir}")
    return install_dir
