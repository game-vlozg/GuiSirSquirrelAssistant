import common
import time
import sys
import signal
import logging
import os

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
    while not common.element_exist("pictures/CustomAdded1080p/Mail/Mail.png"):
        common.mouse_move_click(*common.scale_coordinates_1080p(1000, 970))
    common.mouse_move_click(*common.scale_coordinates_1080p(1650,350))
    while not common.element_exist("pictures/CustomAdded1080p/battlepass/in_pass_missions.png"):
        common.click_matching("pictures/CustomAdded1080p/battlepass/pass_missions.png", recursive=False, mousegoto200=True)
        common.mouse_move_click(*common.scale_coordinates_1080p(1650,350))
        common.sleep(0.1)

    claim_missions()

    common.mouse_move_click(*common.scale_coordinates_1080p(400,600))
    common.sleep(0.1)

    claim_missions()

    common.mouse_move_click(*common.scale_coordinates_1080p(350,80))

    claim_rewards()
    common.key_press("esc")
    while common.element_exist("pictures/CustomAdded1080p/battlepass/pass_missions.png", x1=common.scale_x_1080p(450), y1=common.scale_y_1080p(65), x2=common.scale_x_1080p(640), y2=common.scale_y_1080p(100)):
        common.key_press("esc")

def claim_missions():
    while True:
        matches = common.ifexist_match("pictures/CustomAdded1080p/battlepass/notification.png", x1=common.scale_x_1080p(985), y1=common.scale_y_1080p(270), x2=common.scale_x_1080p(1050), y2=common.scale_y_1080p(850))
        if not matches:
            break
        for x, y in matches:
            common.mouse_move_click(x, y)
            common.sleep(0.1)


def claim_rewards():
    common.mouse_move_click(*common.scale_coordinates_1080p(1140, 890))
    duration = 4
    end_time = time.time() + duration
    while not common.click_matching("pictures/general/beeg_confirm.png", recursive=False):
        if time.time() > end_time:
            logger.info("aww nothing to claim, here have 10 cents go eat a candy")
            return
        common.sleep(0.1)