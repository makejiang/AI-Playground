import os
import psutil
import logging
import threading
import winreg
import win32gui
import win32com.client

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

def get_installer_path(installer_name: str):
    installer_path = os.path.join(get_download_folder(), "_aipg_apps", installer_name)
    if os.path.exists(installer_path):
        return installer_path
    
    # get path of working directory's parent directory
    installer_path = os.path.join(os.path.dirname(os.getcwd()), "_aipg_apps", installer_name)
    if os.path.exists(installer_path):
        return installer_path

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
    # return processname in (p.name() for p in psutil.process_iter(attrs=['name']))
    # return (p.name() for p in psutil.process_iter(attrs=['name']) if p.info['name'] == processname) is not None
    for p in psutil.process_iter(attrs=['name']):
        if p.info['name'] == processname:
            return True

    logger.info(f"appisrunning: {processname} not running")
    return False

def appisrunning_count(processname: str):
    return sum(1 for p in psutil.process_iter(attrs=['name']) if p.info['name'] == processname)

def is_process_running(process_name):
    """Checks if a process with the given name is running.
    Args:
        process_name: The name of the process to check (e.g., "notepad.exe").
    Returns:
        True if the process is running, False otherwise.
    """
    try:
        wmi = win32com.client.GetObject("winmgmts:")
        processes = wmi.InstancesOf("Win32_Process")
        for process in processes:
            if process.Properties_("Name").Value == process_name:
                return True
        return False
    except Exception as e:
        print(f"Error checking process: {e}")
        return False

def list_running_processes():
    """Lists all running processes on the system."""
    try:
        wmi = win32com.client.GetObject("winmgmts:")
        processes = wmi.InstancesOf("Win32_Process")

        process_list = []
        for process in processes:
            process_name = process.Properties_("Name").Value
            process_list.append(process_name)

        return sorted(process_list)
    except Exception as e:
        logger.error(f"Error listing processes: {e}")
        return []

def app_running_count(processname: str):
    try:
        wmi = win32com.client.GetObject("winmgmts:")
        processes = wmi.InstancesOf("Win32_Process")
        count = 0
        for process in processes:
            if process.Properties_("Name").Value == processname:
                count += 1
        return count
    except Exception as e:
        print(f"Error checking process: {e}")
        return 0

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

def get_install_location_reg(software_name):
    # This function retrieves the installation location of a software from the registry.
    # It searches both 32-bit and 64-bit registry views.
    path = _get_reg_software_value(winreg.HKEY_LOCAL_MACHINE, software_name, "InstallLocation")
    if path:
        return path

    path = _get_reg_software_value(winreg.HKEY_LOCAL_MACHINE, software_name, "InstallLocation", wow6432=True)
    if path:
        return path

    path = _get_reg_software_value(winreg.HKEY_CURRENT_USER, software_name, "InstallLocation")
    if path:
        return path
    path = _get_reg_software_value(winreg.HKEY_CURRENT_USER, software_name, "InstallLocation", wow6432=True)
    if path:
        return path

    return None

def get_install_location(software_name):
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
    
    logger.info(f"get_install_location: {install_dir}")
    return install_dir

