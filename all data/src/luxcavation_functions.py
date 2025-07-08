import sys
import os
import json
import common
import core
import logging
import keyboard
import time
import threading
import signal
import mirror
import mirror_utils
import pyautogui

# Determine if running as executable or script
def get_base_path():
    if getattr(sys, 'frozen', False):
        # Running as compiled exe
        return os.path.dirname(sys.executable)
    else:
        # Running as script
        folder_path = os.path.dirname(os.path.abspath(__file__))
        # Check if we're in the src folder or main folder
        if os.path.basename(folder_path) == 'src':
            return os.path.dirname(folder_path)
        return folder_path

# Get base path for resource access
BASE_PATH = get_base_path()

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

# Read status and create Mirror instance globally
status_json_path = os.path.join(BASE_PATH, "config", "status_selection.json")

status = "poise"  # Default fallback

try:
    if os.path.exists(status_json_path):
        with open(status_json_path) as f:
            data = json.load(f)
            # Handle numbered priority format: {"1": "burn", "2": "poise"}
            if all(key.isdigit() for key in data.keys()):
                # Sort by number and extract values in priority order
                sorted_items = sorted(data.items(), key=lambda x: int(x[0]))
                statuses = [item[1] for item in sorted_items]
            else:
                # Fallback to old format: {"selected_statuses": [...]}
                statuses = data.get("selected_statuses", [])
            if statuses:
                status = statuses[0].strip().lower()
    
    m = mirror.Mirror(status)
    logger.info(f"Initialized Mirror with status: {status}")
except Exception as e:
    logger.error(f"Error initializing Mirror with status file: {e}")
    status = "poise"  # Default fallback
    m = mirror.Mirror(status)
    logger.info(f"Initialized Mirror with default status: {status}")

screen_width, screen_height = pyautogui.size()
logger.debug(f"Screen dimensions: {screen_width}x{screen_height}")

def click_matching_EXP(image_path, threshold=0.8, area="center", 
                      movewidth=0, moveheight=0, move2width=0, move2height=0,
                      dragwidth=0, dragheight=0, drag2width=0, drag2height=0,
                      dragspeed=1):
    """
    Find and click an image with fallback drag strategies if not found initially.
    
    Attempts to find an image on screen and click it. If the image isn't found or isn't 
    stable, tries two different drag operations to reveal the element.
    
    Args:
        image_path: Path to target image file
        threshold: Match confidence threshold (0.0-1.0)
        area: Screen area to search ("center", "bottom", etc.)
        movewidth/moveheight: First mouse move coordinates
        move2width/move2height: Second mouse move coordinates
        dragwidth/dragheight: First drag destination coordinates
        drag2width/drag2height: Second drag destination coordinates
        dragspeed: Speed of drag operations (lower is faster)
        
    Returns:
        bool: True if element was found and clicked, False otherwise
    """
    
    def verify_element_visible(image_path, threshold):
        """Check if element exists, wait 0.5 seconds, then check again for stability."""
        try:
            if common.element_exist(image_path, threshold):
                time.sleep(0.5)  # Wait to verify stability
                
                if common.element_exist(image_path, threshold):
                    return True
                else:
                    return False
            else:
                return False
        except Exception as e:
            logger.error(f"Exception during element verification: {e}")
            return False
    
    def try_click_element(image_path, threshold, area, attempt_name):
        """Try to get coordinates and click the element."""
        try:
            found = common.match_image(image_path, threshold, area)
            
            if found and len(found) > 0:
                x, y = found[0]
                common.mouse_move_click(x, y)
                return True
            else:
                return False
        except Exception as e:
            logger.error(f"Exception during click attempt ({attempt_name}): {e}")
            return False
    
    # Attempt 1: Direct check and click
    if verify_element_visible(image_path, threshold):
        if try_click_element(image_path, threshold, area, "initial check"):
            return True
    
    # Attempt 2: First drag
    try:
        common.mouse_move(movewidth, moveheight)
        common.mouse_drag(dragwidth, dragheight, dragspeed)
        time.sleep(0.5)  # Wait after drag
        
        if verify_element_visible(image_path, threshold):
            if try_click_element(image_path, threshold, area, "first drag"):
                return True
    except Exception as e:
        logger.error(f"Exception during first drag attempt: {e}")
    
    # Attempt 3: Second drag
    try:
        common.mouse_move(move2width, move2height)
        common.mouse_drag(drag2width, drag2height, dragspeed)
        time.sleep(0.5)  # Wait after drag
        
        if verify_element_visible(image_path, threshold):
            if try_click_element(image_path, threshold, area, "second drag"):
                return True
    except Exception as e:
        logger.error(f"Exception during second drag attempt: {e}")
    
    logger.warning(f"All attempts to find {os.path.basename(image_path)} failed")
    return False

def click_continue():
    start_time = time.time()

    continue_clicked = False

    while time.time() - start_time < 60:  # 60 second maximum check time
        
        if common.element_exist("pictures/CustomAdded1080p/luxcavation/thread/confirminverted.png"):
            logger.info(f"Confirmation dialog found, clicking it")
            common.click_matching("pictures/CustomAdded1080p/luxcavation/thread/confirminverted.png")
            common.mouse_move(200, 200)
            logger.info(f"clicked comfirm")
            continue_clicked = True
        elif common.element_exist("pictures/general/confirm_w.png"):
            common.click_matching("pictures/general/confirm_w.png")
            time.sleep(0.5)
        elif common.element_exist("pictures/CustomAdded1080p/battle/in_battle_area.png"):
            logger.info(f"tried to click continue but battle ongoing")
            common.error_screenshot()
            core.battle()
        if not common.element_exist("pictures/CustomAdded1080p/luxcavation/thread/confirminverted.png") and continue_clicked:
            break
        time.sleep(0.5)
            
    if time.time() - start_time >= 60:
        return

def squad_select_lux(mirror_instance, SelectTeam=False):
    """
    Select squad members and initiate battle.
    
    Selects sinners according to squad order in configuration,
    initiates battle, and waits for battle screen to appear before
    calling the battle function.
    """
    
    global status
    if SelectTeam:
        status = mirror_utils.squad_choice(status)
        if status is None:
            return
        #This is to bring us to the first entry of teams
        found = common.match_image("pictures/CustomAdded1080p/general/squads/squad_select.png")
        x,y = found[0]
        common.mouse_move(x+common.uniform_scale_single(90),y+common.uniform_scale_single(90))
        for i in range(30):
            common.mouse_scroll(1000)
        common.sleep(1)
        #scrolls through all the squads in steps to look for the name
        for _ in range(4):
            if not common.element_exist(status):
                for i in range(7):
                    common.mouse_scroll(-1000)
                common.sleep(1)
                if common.element_exist(status):
                    common.click_matching(status)
                    break
                continue
            else:
                common.click_matching(status)
                break
    if SelectTeam or not (common.element_exist("pictures/CustomAdded1080p/general/squads/five_squad.png") or common.element_exist("pictures/CustomAdded1080p/general/squads/full_squad.png")):
        # Click squad members according to the configuration
        common.click_matching("pictures/CustomAdded1080p/general/squads/clear_selection.png", mousegoto200=True)
        common.click_matching("pictures/CustomAdded1080p/general/confirm.png", recursive=False)
        for i, position in enumerate(mirror_instance.squad_order):
            x, y = position
            common.mouse_move_click(x, y)
        
    # Start battle
    common.click_matching("pictures/CustomAdded1080p/general/squads/to_battle.png")
    
    # Wait for battle screen
    while not common.element_exist("pictures/battle/winrate.png"):
        common.sleep(0.5)
        
    logger.info(f"Battle screen detected, entering battle")
    core.battle()
    common.mouse_move(200, 200)
    # After squad selection and battle finished:
    logger.info(f"Battle completed, checking for confirmation dialog")
    core.check_loading()
    click_continue()

def navigate_to_lux():
    """
    Navigate to Luxcavation from the main menu.
    
    Checks if already on Luxcavation screen, and if not,
    navigates through the menu system to reach it.
    """
    
    if common.element_exist("pictures/CustomAdded1080p/luxcavation/luxcavation.png"):
        common.click_matching("pictures/CustomAdded1080p/luxcavation/luxcavation.png")
        return
    
    # Only execute this section if not already on the correct screen
    attempts = 0
    max_attempts = 5
    
    while not common.element_exist("pictures/CustomAdded1080p/luxcavation/luxcavation.png"):
        attempts += 1
        if attempts > max_attempts:
            logger.warning(f"Failed to find Luxcavation after {max_attempts} attempts")
            break
            
        common.click_matching("pictures/general/window.png")
        common.click_matching("pictures/general/drive.png")
        time.sleep(0.5)
        
    common.click_matching("pictures/CustomAdded1080p/luxcavation/luxcavation.png")

def pre_exp_setup(Stage, SelectTeam=False):
    """
    Perform setup before Luxcavation missions.
    
    Refills enkephalin and navigates to the specified exp stage.
    
    Args:
        Stage: The exp stage number to navigate to (1-7)
    """
    core.refill_enkephalin()
    navigate_to_exp(Stage, SelectTeam)

def pre_threads_setup(Difficulty, SelectTeam=False):
    """
    Perform setup before Luxcavation missions.
    
    Refills enkephalin and navigates to the specified threads stage.
    
    Args:
        Difficulty: The thread difficulty to navigate to (20,30,40,50)
        SelectTeam: Whether to select team on first run (default: False)
    """
    core.refill_enkephalin()
    navigate_to_threads(Difficulty, SelectTeam)

def navigate_to_exp(Stage, SelectTeam=False):
    """
    Navigate to a specific Exp stage in Luxcavation.
    
    Checks if already on Luxcavation screen, navigates there if needed,
    then finds and clicks the specified exp stage. Handles squad selection
    and battle process, including confirming any post-battle dialogs.
    
    Args:
        Stage: The exp stage number to navigate to (1-7)
    """
    
    # Check if already on Luxcavation screen
    already_on_lux_screen = common.element_exist("pictures/CustomAdded1080p/luxcavation/luxcavation_brown.png")
    
    if not already_on_lux_screen:
        logger.debug(f"Not on Luxcavation screen, navigating there first")
        navigate_to_lux()
    else:
        common.click_matching("pictures/CustomAdded1080p/luxcavation/exp/exp.png", 0.8)
    
    # latest stage check
    if Stage == "latest":
        logger.info(f"clicking latest using coordinates")
        common.mouse_move_click(screen_width * 0.8401, screen_height * 0.6616)
        success = True
    else:
        # Stage-specific thresholds
        thresholds = {
            1: 0.95, 2: 0.95, 3: 0.95, 4: 0.97, 
            5: 0.95, 6: 0.95, 7: 0.99
        }
        # Get threshold and construct image path
        threshold = thresholds[Stage]
        stage_image = f"pictures/CustomAdded1080p/luxcavation/exp/stage{Stage}.png"
        
        # Attempt to click the stage
        success = click_matching_EXP(
            stage_image, 
            threshold, 
            "bottom",
            screen_width * 0.2068, screen_height * 0.0444,
            screen_width * 1.0, screen_height * 0.0444,
            screen_width * 1.0, screen_height * 0.0444,
            screen_width * 0.6, screen_height * 0.0444,
            0.3
        )
    
    # Handle failure by going back and retrying
    if not success:
        logger.warning(f"Failed to click Stage {Stage}")
        if common.element_exist("pictures/battle/winrate.png"):
            core.battle()
            click_continue()
            return

        common.click_matching("pictures/CustomAdded1080p/general/goback.png")
        navigate_to_exp(Stage, SelectTeam)
        return
    
    # Add a delay to allow UI to settle after successful click
    logger.debug(f"Click successful, waiting for UI to settle...")
    time.sleep(0.5)  # Wait 0.5 seconds for UI transition
    
    # Check if we're in squad select
    if common.element_exist("pictures/CustomAdded1080p/general/squads/squad_select.png"):
        logger.info(f"Squad select screen detected")
        squad_select_lux(m, SelectTeam)
        common.key_press(Key="esc", presses=2)
    else:
        logger.warning(f"Squad select screen not detected, retrying")
        common.key_press(Key="esc", presses=2)
        time.sleep(1)
        common.key_press(Key="esc", presses=2)
        navigate_to_exp(Stage, SelectTeam)
        return
    

def navigate_to_threads(Difficulty, SelectTeam=False):
    """
    Navigate to a specific Thread difficulty in Luxcavation.
    
    Navigates to the Thread section, selects the specified difficulty level,
    handles squad selection, and manages post-battle confirmations.
    
    Args:
        Difficulty: The thread difficulty level to navigate to (20, 30, 40, 50, or 'latest')
        SelectTeam: Whether to select team on first run (default: False)
    """
    
    # Validate input
    if Difficulty != "latest" and Difficulty not in [20, 30, 40, 50]:
        logger.error(f"Invalid thread difficulty: {Difficulty}")
        return
        
    # Check if already on Luxcavation screen
    already_on_lux_screen = common.element_exist("pictures/CustomAdded1080p/luxcavation/luxcavation_brown.png")
    
    # Navigate to Luxcavation if needed and click on thread
    if not already_on_lux_screen:
        logger.debug(f"Not on Luxcavation screen, navigating there first")
        navigate_to_lux()
        
    common.click_matching("pictures/CustomAdded1080p/luxcavation/thread/thread.png")
    
    # Check if we can enter thread
    if not common.element_exist("pictures/CustomAdded1080p/luxcavation/thread/enter.png"):
        logger.warning("Enter button not found")
        navigate_to_threads(Difficulty)
        return
        
    # Click enter
    common.mouse_move_click(common.scale_x_1080p(564), common.scale_y_1080p(722))
    time.sleep(0.5)
    
    # Handle "latest" vs numeric difficulties
    if Difficulty == "latest":
        logger.info(f"clicking latest using coordinates")
        screen_width, screen_height = common.get_resolution()
        common.mouse_move_click(screen_width * 0.4817, screen_height * 0.6713)
        success = True
    else:
        # Construct the difficulty-specific image path
        difficulty_image = f"pictures/CustomAdded1080p/luxcavation/thread/difficulty{Difficulty}.png"
        
        # Check if the difficulty is immediately visible
        if common.element_exist(difficulty_image, 0.97):
            common.click_matching(difficulty_image, 0.97, area="center", mousegoto200=False)
            success = True
        else:
            # Scroll to find the difficulty
            for i in range(7):
                found_matches = common.match_image("pictures/CustomAdded1080p/luxcavation/thread/difficulty.png", 0.97, area="left")
                if found_matches:
                    x, y = found_matches[0]
                    common.mouse_move(x, y)
                    common.mouse_scroll(1000)
                    
            common.click_matching(difficulty_image, 0.97, area="center", mousegoto200=False)
            success = True
        
    logger.debug(f"Click successful, waiting for UI to settle...")
    time.sleep(0.5)  # Wait 0.5 seconds for UI transition
        
    if common.element_exist("pictures/CustomAdded1080p/general/squads/squad_select.png"):
        logger.info(f"Squad select screen detected")
        squad_select_lux(m, SelectTeam)
        common.key_press(Key="esc", presses=2)
    else:
        logger.warning(f"Squad select screen not detected, retrying")
        common.key_press(Key="esc", presses=2)
        time.sleep(1)
        common.key_press(Key="esc", presses=2)
        navigate_to_threads(Difficulty, SelectTeam)
        return
