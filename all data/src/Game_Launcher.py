import subprocess
import winreg
import os
import common
import sys
import logging
# Determine if running as executable or script
def get_base_path():
    if getattr(sys, 'frozen', False):
        # Running as compiled exe
        return os.path.dirname(sys.executable)
    else:
        # Running as script
        return os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# Set up paths
BASE_PATH = get_base_path()
sys.path.append(BASE_PATH)
sys.path.append(os.path.join(BASE_PATH, 'src'))

# Setting up basic logging configuration
LOG_FILENAME = os.path.join(BASE_PATH, "Pro_Peepol's.log")
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(LOG_FILENAME)
    ]
)
logger = logging.getLogger(__name__)

# Signal handler for clean shutdown
def signal_handler(sig, frame):
    """
    Handle termination signals
    """
    logger.warning(f"Termination signal received, shutting down...")
    sys.exit(0)

def get_steam_exe():
    try:
        key = winreg.OpenKey(winreg.HKEY_CURRENT_USER, r"Software\Valve\Steam")
        steam_path, _ = winreg.QueryValueEx(key, "SteamExe")
        winreg.CloseKey(key)
        if not os.path.isfile(steam_path):
            raise FileNotFoundError(f"Steam.exe not found at {steam_path}")
        return steam_path
    except Exception as e:
        raise RuntimeError(f"Failed to locate Steam.exe: {e}")

def launch_game(appid):
    steam_exe = get_steam_exe()
    subprocess.Popen([steam_exe, f"steam://rungameid/{appid}"])

def launch_limbussy():
    launch_game("1973530")
    while not common.element_exist("pictures/CustomAdded1080p/launch/Clear_All_Caches.png"):
        common.sleep(1)
    while common.element_exist("pictures/CustomAdded1080p/launch/Clear_All_Caches.png"):
        common.mouse_move_click(*common.scale_coordinates_1080p(960, 540))
        common.click_matching("pictures/general/beeg_confirm.png", recursive=False)
        if common.element_exist("pictures/general/maint.png"):
            common.click_matching("pictures/general/close.png", recursive=False)
            return False
        common.sleep(2)
        
    while not common.element_exist("pictures/CustomAdded1080p/Mail/Mail.png"):
        common.click_matching("pictures/general/beeg_confirm.png", recursive=False)
        if common.element_exist("pictures/general/maint.png"):
            common.click_matching("pictures/general/close.png", recursive=False)
            return False
        common.sleep(2)
    common.sleep(2)
    return True