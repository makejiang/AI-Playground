import os, platform, subprocess
import logging
import psutil 
import shlex 
import time

if platform.system() == 'Windows':
    import winreg
    import win32gui
            

def _get_reg_software_value(hkey, sw_name, key_name):
    try:
        registry_key = winreg.OpenKey(hkey, r"SOFTWARE\Microsoft\Windows\CurrentVersion\Uninstall")
        i = 0
        while True:
            subkey_name = winreg.EnumKey(registry_key, i)
            subkey = winreg.OpenKey(registry_key, subkey_name)
            try:
                display_name, _ = winreg.QueryValueEx(subkey, "DisplayName")
                if sw_name in display_name:
                    return winreg.QueryValueEx(subkey, key_name)[0]
            except EnvironmentError:
                pass
            i += 1
    except WindowsError:
        pass

    return None

def _get_download_folder():
    if platform.system() == 'Windows':
        try:
            with winreg.OpenKey(winreg.HKEY_CURRENT_USER, r'SOFTWARE\Microsoft\Windows\CurrentVersion\Explorer\Shell Folders') as key:
                downloads_folder = winreg.QueryValueEx(key, '{374DE290-123F-4565-9164-39C4925E467B}')[0]
                return downloads_folder
        except Exception as e:
            print(f"Error accessing registry: {e}")
            return None
    elif platform.system() == 'Linux':
        return os.path.expanduser('~/Downloads')
    else:
        print("Unsupported platform")
        return None

def _is_window_running(win_title):
    if platform.system() == 'Windows':
        try:
            ret = win32gui.FindWindow(None, win_title)
            print(f"FindWindow: {ret}")
            return ret!=0
        except:
            return False
    else:
        print("Unsupported platform")
        return False

def appisinstalled(installedname: str):
    logging.info(f"appisinstalled: {installedname}")
    return get_uninstall_string(installedname) is not None

def appisrunning(processname: str):
    logging.info(f"appisrunning: {processname}")
    return processname in (p.name() for p in psutil.process_iter(attrs=['name']))
    

def installapp(installer: str):
    logging.info(f"install: {installer}")
    path_installer = os.path.join(_get_download_folder(), 'ai-center-pkgs', installer)

    if not os.path.exists(path_installer):
        return False

    logging.info(f"calling cmd process: {path_installer}")
    ret = subprocess.call([path_installer], shell=True)
    return ret==0

def get_uninstall_string(software_name):
    # path_uninstall = _get_reg_software_value(winreg.HKEY_LOCAL_MACHINE, software_name, "QuietUninstallString")
    # if path_uninstall:
    #     return path_uninstall

    path_uninstall = _get_reg_software_value(winreg.HKEY_LOCAL_MACHINE, software_name, "UninstallString")
    if path_uninstall:
        return path_uninstall

    # path_uninstall = _get_reg_software_value(winreg.HKEY_CURRENT_USER, software_name, "QuietUninstallString")
    # if path_uninstall:
    #     return path_uninstall

    path_uninstall = _get_reg_software_value(winreg.HKEY_CURRENT_USER, software_name, "UninstallString")
    if path_uninstall:
        return path_uninstall

    return path_uninstall


def get_install_localtion(software_name):
    path_uninstall = get_uninstall_string(software_name)
    if not path_uninstall:
        return None
    
    # get "C:\Program Files\Flowy AIPC" from '"C:\Program Files\Flowy AIPC\Uninstall Flowy AIPC.exe" /allusers /S'
    
    # Extract the quoted path
    quoted_path = path_uninstall.split('"')[1]
    # Get the directory
    install_directory = os.path.dirname(quoted_path)

    return install_directory


def uninstallapp(installedname: str, uninstall_process_name=None):
    logging.info(f"uninstall: {installedname}")
    path_uninstall = get_uninstall_string(installedname)
    if not path_uninstall:
        return False

    logging.info(f"calling cmd process: {path_uninstall}")
    cmds = shlex.split(path_uninstall)

    if len(cmds) > 1:
        ret = subprocess.call(cmds, shell=True)    
    else:
        # remove '"' at the begin and end if exists
        if path_uninstall.startswith('"') and path_uninstall.endswith('"'):
            path_uninstall = path_uninstall[1:-1]

        ret = subprocess.call([path_uninstall], shell=True)

    if ret!=0:
        logging.error(f"run uninstall cmd failed: {installedname}, ret:  {ret}")
        return False

    # wait for uninstall window to close
    if uninstall_process_name:
        # wait for the uninstall window to open
        while not appisrunning(uninstall_process_name):
            time.sleep(1)

        logging.info(f"'{uninstall_process_name}' is running")

        # wait for the uninstall window to close
        while appisrunning(uninstall_process_name):
            time.sleep(1)

        logging.info(f"'{uninstall_process_name}' dispapeared")

        # wait for the uninstall process to finish
        time.sleep(2)
        path_uninstall = get_uninstall_string(installedname)
        return path_uninstall is None
    
    return True


def runapp(appname, processname, installedname):
    logging.info(f"runapp: {processname}")

    path_dir = get_install_localtion(installedname)
    if not path_dir:
        logging.error(f"runapp: {appname} not installed")
        return False

    path_exe = os.path.join(path_dir, processname)
    if not os.path.exists(path_exe):
        logging.error(f"runapp: {path_exe} not found")
        return False
    
    logging.info(f"calling cmd process: {path_exe}")
    process = subprocess.Popen([path_exe], shell=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    return True


def closeapp(processname):
    logging.info(f"closeapp: {processname}")

    for proc in psutil.process_iter(attrs=['name', 'pid']):
        if proc.info['name'] == processname:
            proc.terminate()
            proc.wait()  # Wait for the process to terminate

    return True


def printMemuHwnd():
    def winEnumHandler(hwnd, ctx):
        if win32gui.IsWindowVisible(hwnd):
            print(win32gui.GetWindowText(hwnd))
            

    win32gui.EnumWindows(winEnumHandler, None)

if __name__ == "__main__":
    #print("window:", _is_window_running("Flowy AIPC Uninstall"))
    #printMemuHwnd()
    #print(get_uninstall_string("Flowy AIPC"))
    
    
    # print(appisinstalled("AiPPT"))
    # print(get_uninstall_string("AiPPT"))

    # print(appisrunning("AiPPT.exe"))

    print(_is_window_running("AiPPT Uninstall"))
    # print(uninstallapp("AiPPT", "AiPPT Uninstall"))