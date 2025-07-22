import common
import time
import sys
import signal
import os
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

# Register signal handlers
signal.signal(signal.SIGTERM, signal_handler)
signal.signal(signal.SIGINT, signal_handler)

def main():
    while not common.element_exist("pictures/CustomAdded1080p/general/info.png"):
        common.mouse_move_click(*common.scale_coordinates_1080p(1600, 965))
        common.sleep(0.1)
    extract() # 1st
    common.sleep(0.3)
    common.mouse_move_click(*common.scale_coordinates_1080p(300, 420))
    common.sleep(0.1)
    extract() # 2nd
    common.sleep(0.3)
    common.mouse_move_click(*common.scale_coordinates_1080p(300, 570))
    common.sleep(0.1)
    extract() # 3rd
    common.sleep(0.3)


def extract():
    duration = 4
    end_time = time.time() + duration

    while not common.element_exist("pictures/CustomAdded1080p/general/confirm.png", mousegoto200=True, threshold=0.9):
        common.mouse_move_click(*common.scale_coordinates_1080p(1000, 660))
        if time.time() > end_time:
            return
        common.sleep(0.5)
        
    while common.click_matching("pictures/CustomAdded1080p/general/confirm.png", mousegoto200=True, recursive=False):
        pass

    while not common.click_matching("pictures/CustomAdded1080p/extraction/Return.png", recursive=False):
        common.mouse_move_click(*common.scale_coordinates_1080p(1040, 540))
        if common.element_exist("pictures/CustomAdded1080p/extraction/Exchange.png"):
            while common.element_exist("pictures/CustomAdded1080p/extraction/Exchange.png"):
                common.key_press("esc")
                common.sleep(0.5)
            extract()
            return
        common.sleep(0.5)