import os
import sys
import json
import time
import ctypes
import logging
import secrets
import platform
import threading
import inspect
from functools import partial
from ctypes import wintypes
import cv2
import numpy as np
import pyautogui
from mss import mss
from mss.tools import to_png
from PIL import ImageGrab
import shared_vars

pyautogui.FAILSAFE = False
pyautogui.PAUSE = 0.05

# Template reference resolutions - used only for template matching
REFERENCE_WIDTH_1440P = 2560
REFERENCE_HEIGHT_1440P = 1440
REFERENCE_WIDTH_1080P = 1920
REFERENCE_HEIGHT_1080P = 1080
REFERENCE_ASPECT_RATIO = 16/9


# Monitor configuration - can be adjusted by user if needed
# GAME_MONITOR_INDEX now comes from shared_vars instead of being a module variable

CLEAN_LOGS_ENABLED = True

# Actual monitor resolution (will be set during initialization)
MONITOR_WIDTH: int | None = None
MONITOR_HEIGHT: int | None = None
EXPECTED_WIDTH: int | None = None
EXPECTED_HEIGHT: int | None = None
IS_NON_STANDARD_RATIO: bool | None = None  # Whether current monitor size follow standard 16:9 ratio, e.g. 16:10

# Determine if running as executable or script
def get_base_path():
    """Get the base directory path for resource access"""
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

def resource_path(relative_path):
    """Get absolute path for resource files"""
    base_path = BASE_PATH
    return os.path.join(base_path, relative_path)

class NoMillisecondsFormatter(logging.Formatter):
    def formatTime(self, record, datefmt=None):
        # Always use custom format without milliseconds
        return time.strftime('%d/%m/%Y %H:%M:%S', time.localtime(record.created))
    
    def format(self, record):
        # Add dirty flag to the end of the message if present
        formatted = super().format(record)
        if hasattr(record, 'dirty') and record.dirty:
            formatted += " | DIRTY"
        return formatted

# Setting up basic logging configuration
LOG_FILENAME = os.path.join(BASE_PATH, "Pro_Peepol's.log")

# Create custom handler with no-milliseconds formatter
handler = logging.FileHandler(LOG_FILENAME)
formatter = NoMillisecondsFormatter(
    fmt='%(asctime)s | %(name)s | %(levelname)s | %(funcName)s:%(lineno)d | %(message)s',
    datefmt='%d/%m/%Y %H:%M:%S'
)
handler.setFormatter(formatter)

class DirtyLogger(logging.Logger):
    def _log(self, level, msg, args, exc_info=None, extra=None, stack_info=False, dirty=False):
        if extra is None:
            extra = {}
        extra['dirty'] = dirty
        super()._log(level, msg, args, exc_info, extra, stack_info)
    
    def debug(self, msg, *args, dirty=False, **kwargs):
        if self.isEnabledFor(logging.DEBUG):
            self._log(logging.DEBUG, msg, args, dirty=dirty, **kwargs)
    
    def info(self, msg, *args, dirty=False, **kwargs):
        if self.isEnabledFor(logging.INFO):
            self._log(logging.INFO, msg, args, dirty=dirty, **kwargs)
    
    def warning(self, msg, *args, dirty=False, **kwargs):
        if self.isEnabledFor(logging.WARNING):
            self._log(logging.WARNING, msg, args, dirty=dirty, **kwargs)
    
    def error(self, msg, *args, dirty=False, **kwargs):
        if self.isEnabledFor(logging.ERROR):
            self._log(logging.ERROR, msg, args, dirty=dirty, **kwargs)
    
    def critical(self, msg, *args, dirty=False, **kwargs):
        if self.isEnabledFor(logging.CRITICAL):
            self._log(logging.CRITICAL, msg, args, dirty=dirty, **kwargs)

# Import async logging system
try:
    from logger import AsyncDirtyLogger, start_async_logging, set_logging_enabled, is_logging_enabled
    ASYNC_LOGGING_AVAILABLE = True
except ImportError:
    ASYNC_LOGGING_AVAILABLE = False

# Set the custom logger class globally
if ASYNC_LOGGING_AVAILABLE:
    logging.setLoggerClass(AsyncDirtyLogger)
else:
    logging.setLoggerClass(DirtyLogger)

# Configure root logger AFTER setting the custom logger class
# Clear any existing handlers first
logging.getLogger().handlers.clear()
logging.basicConfig(
    level=logging.DEBUG,
    handlers=[handler],
    force=True
)

# Create logger instance
logger = logging.getLogger(__name__)

def initialize_async_logging():
    """Initialize async logging if available - call this after all imports are done"""
    if ASYNC_LOGGING_AVAILABLE:
        try:
            start_async_logging(LOG_FILENAME)
            return True
        except Exception as e:
            logger.warning(f"Failed to initialize async logging: {e}")
            return False
    return False

def detect_monitor_resolution():
    """Detect the actual resolution of the game monitor"""
    global MONITOR_WIDTH, MONITOR_HEIGHT, IS_NON_STANDARD_RATIO, EXPECTED_WIDTH, EXPECTED_HEIGHT
    
    with mss() as sct:
        # Use monitor 1 as default if shared_vars.game_monitor doesn't exist yet
        monitor_index = getattr(shared_vars, 'game_monitor', 1)
        monitor = sct.monitors[monitor_index]
        MONITOR_WIDTH = monitor['width']
        MONITOR_HEIGHT = monitor['height']
        
        logger.info(f"Detected montior size: {MONITOR_WIDTH}x{MONITOR_HEIGHT}")

        # Calculate aspect ratio
        aspect_ratio = MONITOR_WIDTH / MONITOR_HEIGHT
        IS_NON_STANDARD_RATIO = not(abs(aspect_ratio - REFERENCE_ASPECT_RATIO) < 0.0001)

        EXPECTED_WIDTH = MONITOR_WIDTH
        EXPECTED_HEIGHT = MONITOR_HEIGHT
        if IS_NON_STANDARD_RATIO:
            if aspect_ratio > REFERENCE_ASPECT_RATIO:
                EXPECTED_WIDTH = round(MONITOR_HEIGHT * REFERENCE_ASPECT_RATIO)
            else:
                EXPECTED_HEIGHT = round(MONITOR_WIDTH / REFERENCE_ASPECT_RATIO)
            logger.info(f"Non-standard monitor ratio detected (expect {EXPECTED_WIDTH}x{EXPECTED_HEIGHT} instead)")

        return MONITOR_WIDTH, MONITOR_HEIGHT

# Initialize monitor resolution at module load time
detect_monitor_resolution()

def random_choice(list):
    """Pick random item from list"""
    return secrets.choice(list)

def sleep(x):
    """Sleep for x seconds"""
    time.sleep(x)

def mouse_scroll(amount):
    """Scroll mouse wheel"""
    pyautogui.scroll(amount)

def _validate_monitor_index(monitor_index, fallback=1):
    """Validate and return a safe monitor index"""
    with mss() as sct:
        if monitor_index >= len(sct.monitors):
            logger.warning(f"Monitor index {monitor_index} out of range")
            return fallback
        return monitor_index

def get_monitor_info(monitor_index=None):
    """Get information about the specified monitor or the game monitor"""
    with mss() as sct:
        mon_idx = monitor_index if monitor_index is not None else shared_vars.game_monitor
        mon_idx = _validate_monitor_index(mon_idx)
        return sct.monitors[mon_idx]

def get_MonCords(x, y):
    """Convert local coordinates to global monitor coordinates"""
    mon = get_monitor_info()
    return mon['left'] + x, mon['top'] + y

def mouse_move(x, y):
    """Moves the mouse to the X,Y coordinate specified on the game monitor"""
    real_x, real_y = get_MonCords(x, y)
    pyautogui.moveTo(real_x, real_y)

def mouse_click():
    """Performs a left click on the current position"""
    caller_info = _get_caller_info()
    current_pos = pyautogui.position()
    logger.debug(f"Mouse click at ({current_pos.x}, {current_pos.y}) - {caller_info}", dirty=True)
    pyautogui.click()

def mouse_hold():
    """Hold down mouse button for 2 seconds"""
    pyautogui.mouseDown()
    sleep(2)
    pyautogui.mouseUp()

def mouse_down():
    """Press down mouse button"""
    pyautogui.mouseDown()

def mouse_up():
    """Release mouse button"""
    pyautogui.mouseUp()

def mouse_move_click(x, y, log_click=True):
    """Moves the mouse to the X,Y coordinate specified and performs a left click"""
    if log_click:
        caller_info = _get_caller_info()
        logger.debug(f"Mouse move and click to ({x}, {y}) - {caller_info}", dirty=True)
    mouse_move(x, y)
    pyautogui.click()

def mouse_drag(x, y, seconds=1):
    """Drag from current position to the specified coords on the game monitor"""
    caller_info = _get_caller_info()
    logger.debug(f"Mouse drag to ({x}, {y}) over {seconds}s - {caller_info}", dirty=True)
    real_x, real_y = get_MonCords(x, y)
    pyautogui.dragTo(real_x, real_y, seconds, button='left')

def key_press(Key, presses=1):
    """Presses the specified key X amount of times"""
    pyautogui.press(Key, presses)

def capture_screen(monitor_index=None):
    """Captures the specified monitor screen using MSS and converts it to a numpy array for CV2."""
    with mss() as sct:
        # Use specified monitor or default game monitor
        mon_idx = monitor_index if monitor_index is not None else shared_vars.game_monitor
        mon_idx = _validate_monitor_index(mon_idx)
            
        monitor = sct.monitors[mon_idx]
        
        # Capture the screen with the current resolution
        screenshot = sct.grab(monitor)
        img = np.array(screenshot)
        
        # Convert the color from BGRA to BGR for OpenCV compatibility
        img = cv2.cvtColor(img, cv2.COLOR_BGRA2BGR)
        
        return img

def save_match_screenshot(screenshot, top_left, bottom_right, template_path, match_index):
    """Saves a screenshot of the matched region, preserving directory structure in 'higher_res'."""
    # Crop the matched region from the full screenshot
    match_region = screenshot[top_left[1]:bottom_right[1], top_left[0]:bottom_right[0]]
    
    # Create a modified output path in the 'higher_res' folder
    output_path = os.path.join(BASE_PATH, "higher_res", template_path)
    output_dir = os.path.dirname(output_path)
    os.makedirs(output_dir, exist_ok=True)
    
    # Generate a unique filename for each match within the higher_res directory
    output_path = os.path.splitext(output_path)[0]  # Remove original extension
    output_path = f"{output_path}.png"  # Append match index
    if os.path.exists(output_path):
        return
    # Save the cropped region
    cv2.imwrite(output_path, match_region)

def is_custom_1080p_image(template_path):
    """Check if the image is from the CustomAdded1080p folder"""
    return "CustomAdded1080p" in template_path

def is_custom_fuse_image(template_path):
    """Check if the image is from the CustomFuse folder"""
    return "CustomFuse" in template_path

def get_template_reference_resolution(template_path):
    """Determine which reference resolution to use based on the template path"""
    if is_custom_1080p_image(template_path):
        return REFERENCE_WIDTH_1080P, REFERENCE_HEIGHT_1080P
    else:
        # For non-1080p templates, use the 1440p template dimensions
        return REFERENCE_WIDTH_1440P, REFERENCE_HEIGHT_1440P

def _extract_coordinates(filtered_boxes, area="center", crop_offset_x=0, crop_offset_y=0):
    """Extract coordinates from filtered boxes based on area preference"""
    found_elements = []
    for (x1, y1, x2, y2) in filtered_boxes:
        # Adjust coordinates by crop offset to get full screen coordinates
        x1 += crop_offset_x
        y1 += crop_offset_y
        x2 += crop_offset_x
        y2 += crop_offset_y
        
        if area == "all":
            # Return all coordinates: top, left, right, bottom, center
            top_x, top_y = (x1 + x2) // 2, y1
            left_x, left_y = x1, (y1 + y2) // 2
            right_x, right_y = x2, (y1 + y2) // 2
            bottom_x, bottom_y = (x1 + x2) // 2, y2
            center_x, center_y = (x1 + x2) // 2, (y1 + y2) // 2
            found_elements.append({
                'top': (top_x, top_y),
                'left': (left_x, left_y),
                'right': (right_x, right_y),
                'bottom': (bottom_x, bottom_y),
                'center': (center_x, center_y)
            })
        elif area == "bottom":
            x = (x1 + x2) // 2
            y = y2
            found_elements.append((x, y))
        elif area == "top":
            x = (x1 + x2) // 2
            y = y1
            found_elements.append((x, y))
        elif area == "left":
            x = x1
            y = (y1 + y2) // 2
            found_elements.append((x, y))
        elif area == "right":
            x = x2
            y = (y1 + y2) // 2
            found_elements.append((x, y))
        else:  # center
            x = (x1 + x2) // 2
            y = (y1 + y2) // 2
            found_elements.append((x, y))
    
    return found_elements if found_elements else []

def _get_caller_info():
    """Get caller information (file and function name) for debugging"""
    try:
        # Walk through the call stack to find the first frame not in common.py
        stack = inspect.stack()
        for frame_info in stack:
            filename = frame_info.filename
            if not filename.endswith('common.py'):
                # Found the first non-common.py frame
                module_name = os.path.splitext(os.path.basename(filename))[0]
                function_name = frame_info.function
                line_number = frame_info.lineno
                return f"{module_name}.{function_name}:{line_number}"
    except Exception:
        pass
    return "unknown"

def _base_match_template(template_path, threshold=0.8, grayscale=False,no_grayscale=False, debug=False, area="center", quiet_failure=False, x1=None, y1=None, x2=None, y2=None):
    """Internal function that handles all template matching logic"""
    
    full_template_path = resource_path(template_path)
        
    screenshot = capture_screen()
    original_screenshot_height, original_screenshot_width = screenshot.shape[:2]
    
    # Handle region cropping
    crop_offset_x = 0
    crop_offset_y = 0
    if x1 is not None and y1 is not None and x2 is not None and y2 is not None:
        # Ensure coordinates are within bounds
        x1 = max(0, min(x1, original_screenshot_width))
        y1 = max(0, min(y1, original_screenshot_height))
        x2 = max(x1, min(x2, original_screenshot_width))
        y2 = max(y1, min(y2, original_screenshot_height))
        
        # Crop screenshot to specified region
        screenshot = screenshot[y1:y2, x1:x2]
        crop_offset_x = x1
        crop_offset_y = y1
    
    # Use original dimensions for scale factor calculation, not cropped dimensions
    screenshot_height, screenshot_width = original_screenshot_height, original_screenshot_width
    
    # no_grayscale=True should completely prevent grayscale conversion
    if not no_grayscale and (grayscale or shared_vars.convert_images_to_grayscale):
        screenshot = cv2.cvtColor(screenshot, cv2.COLOR_BGR2GRAY)
    
    base_width, base_height = get_template_reference_resolution(full_template_path)
    
    scale_factor_x = screenshot_width / base_width
    scale_factor_y = screenshot_height / base_height
    scale_factor = min(scale_factor_x, scale_factor_y)
    
    # no_grayscale=True should completely prevent grayscale conversion
    if no_grayscale:
        color_flag = cv2.IMREAD_COLOR
    else:
        color_flag = cv2.IMREAD_GRAYSCALE if (grayscale or shared_vars.convert_images_to_grayscale) else cv2.IMREAD_COLOR
    template = cv2.imread(full_template_path, color_flag)
    if template is None:
        raise FileNotFoundError(f"Template image '{full_template_path}' not found.")
    
    # Skip scaling for CustomFuse images - use them at their original resolution
    if is_custom_fuse_image(full_template_path):
        pass
    else:
        template = cv2.resize(template, None, fx=scale_factor, fy=scale_factor, interpolation=cv2.INTER_LINEAR)
    
    template_height, template_width = template.shape[:2]
    
    # Ensure both screenshot and template have matching color formats
    if no_grayscale:
        # Force color mode - ensure both are BGR
        if len(screenshot.shape) == 2:
            screenshot = cv2.cvtColor(screenshot, cv2.COLOR_GRAY2BGR)
        if len(template.shape) == 2:
            template = cv2.cvtColor(template, cv2.COLOR_GRAY2BGR)
    else:
        # Allow grayscale mode - ensure both are grayscale if conversion is enabled
        if (grayscale or shared_vars.convert_images_to_grayscale):
            if len(screenshot.shape) == 3:
                screenshot = cv2.cvtColor(screenshot, cv2.COLOR_BGR2GRAY)
            if len(template.shape) == 3:
                template = cv2.cvtColor(template, cv2.COLOR_BGR2GRAY)
    
    result = cv2.matchTemplate(screenshot, template, cv2.TM_CCOEFF_NORMED)
    
    if scale_factor < 0.75:
        threshold = threshold - 0.05
    
    # Apply threshold adjustment from user configuration
    total_adjustment = get_total_threshold_adjustment(template_path)
    threshold = threshold + total_adjustment
    
    locations = np.where(result >= threshold)
    boxes = []
    match_scores = []
    
    for pt in zip(*locations[::-1]):
        top_left = pt
        bottom_right = (top_left[0] + template_width, top_left[1] + template_height)
        boxes.append([top_left[0], top_left[1], bottom_right[0], bottom_right[1]])
        match_scores.append(result[top_left[1], top_left[0]])
    
    boxes = np.array(boxes)
    filtered_boxes = non_max_suppression_fast(boxes)
    
    if not quiet_failure:
        caller_info = _get_caller_info()
        highest_match_rate = result.max() if result.size > 0 else 0.0
        if len(filtered_boxes) > 0:
            # Get center coordinates of matches for logging (adjusted for crop offset)
            locations = []
            for box in filtered_boxes:
                center_x = int((box[0] + box[2]) / 2) + crop_offset_x
                center_y = int((box[1] + box[3]) / 2) + crop_offset_y
                locations.append(f"({center_x},{center_y})")
            locations_str = ", ".join(locations)
            logger.debug(f"Match found: {template_path} at {locations_str} - found {len(filtered_boxes)} matches - {caller_info}. Highest match rate: {highest_match_rate}", dirty=True)
        else:
            logger.debug(f"Match not found: {template_path} - {caller_info}. Highest match rate: {highest_match_rate}", dirty=True)
    
    if (debug or shared_vars.debug_image_matches) and len(filtered_boxes) > 0:
        
        def draw_debug_rectangle(x, y, width, height, duration=1.0):
            """Draw rectangle directly on desktop using orange color rgb(254, 176, 5)"""
            
            if platform.system() != 'Windows':
                return
                
            def draw_and_erase():
                try:
                    user32 = ctypes.windll.user32
                    gdi32 = ctypes.windll.gdi32
                    
                    mon = get_monitor_info()
                    x_int = int(mon['left'] + x)
                    y_int = int(mon['top'] + y)
                    w_int = int(width)
                    h_int = int(height)
                    
                    desktop_dc = user32.GetDC(0)
                    
                    pen = gdi32.CreatePen(0, 4, 0x05B0FE)
                    old_pen = gdi32.SelectObject(desktop_dc, pen)
                    old_brush = gdi32.SelectObject(desktop_dc, gdi32.GetStockObject(5))
                    
                    gdi32.Rectangle(desktop_dc, x_int, y_int, x_int + w_int, y_int + h_int)
                    
                    time.sleep(duration)
                    
                    rect = wintypes.RECT(x_int - 5, y_int - 5, x_int + w_int + 5, y_int + h_int + 5)
                    user32.InvalidateRect(0, ctypes.byref(rect), 1)
                    
                    gdi32.SelectObject(desktop_dc, old_pen)
                    gdi32.SelectObject(desktop_dc, old_brush)
                    gdi32.DeleteObject(pen)
                    user32.ReleaseDC(0, desktop_dc)
                    
                except Exception as e:
                    print(f"Debug rectangle error: {e}")
            
            threading.Thread(target=draw_and_erase, daemon=True).start()
        
        for (x1, y1, x2, y2) in filtered_boxes:
            padding = 8
            draw_debug_rectangle(
                x1 - padding, 
                y1 - padding, 
                (x2 - x1) + (padding * 2), 
                (y2 - y1) + (padding * 2), 
                2.0
            )
    
    return _extract_coordinates(filtered_boxes, area, crop_offset_x, crop_offset_y)

def get_total_threshold_adjustment(template_path):
    """Get combined threshold adjustment based on global, folder, and path-specific settings"""
    config = shared_vars.image_threshold_config
    
    # Get adjustments
    global_adj = config.get("global_adjustment", 0.0)
    folder_adj = get_folder_specific_adjustment(template_path)
    path_adj = get_path_specific_adjustment(template_path)
    apply_global_to_modified = config.get("apply_global_to_modified", True)
    
    # Logic for combining adjustments (folder + specific image adjustments are additive)
    total_specific_adj = folder_adj + path_adj
    
    if total_specific_adj != 0.0:  # Any specific adjustment exists
        if apply_global_to_modified:
            return global_adj + total_specific_adj  # Global + folder + image-specific
        else:
            return total_specific_adj  # Only folder + image-specific
    else:  # No specific adjustments
        return global_adj  # Only global applied

def get_folder_specific_adjustment(template_path):
    """Get adjustment for folder containing the image"""
    config = shared_vars.image_threshold_config
    folder_adjustments = config.get("folder_adjustments", {})
    
    # Extract folder path from template path
    folder_path = os.path.dirname(template_path)
    return folder_adjustments.get(folder_path, 0.0)

def get_path_specific_adjustment(template_path):
    """Get adjustment for specific image path"""
    config = shared_vars.image_threshold_config
    image_adjustments = config.get("image_adjustments", {})
    return image_adjustments.get(template_path, 0.0)

def match_image(template_path, threshold=0.8, area="center",mousegoto200=False, grayscale=False, no_grayscale=False, debug=False, quiet_failure=False, x1=None, y1=None, x2=None, y2=None):
    """Finds the image specified and returns coordinates depending on area: center, bottom, left, right, top.
    
    Args:
        x1, y1, x2, y2: Optional region coordinates to limit search area. If provided, only searches within this rectangle.
    """
    if mousegoto200:
        mouse_move(*scale_coordinates_1080p(200, 200))
    return _base_match_template(template_path, threshold, grayscale, no_grayscale, debug, area, quiet_failure, x1, y1, x2, y2)

def greyscale_match_image(template_path, threshold=0.75, area="center", no_grayscale=False, debug=False, quiet_failure=False, x1=None, y1=None, x2=None, y2=None):
    """Finds the image specified and returns the center coordinates, regardless of screen resolution,
    and saves screenshots of each match found."""
    return _base_match_template(template_path, threshold, grayscale=True, no_grayscale=no_grayscale, debug=debug, area=area, quiet_failure=quiet_failure, x1=x1, y1=y1, x2=x2, y2=y2)

def debug_match_image(template_path, threshold=0.8, area="center", grayscale=False, no_grayscale=False, x1=None, y1=None, x2=None, y2=None):
    """Finds the image specified and returns the center coordinates, regardless of screen resolution,
       and draws rectangles on each match found."""
    return _base_match_template(template_path, threshold, grayscale=grayscale, no_grayscale=no_grayscale, debug=True, area=area, x1=x1, y1=y1, x2=x2, y2=y2)

def proximity_check(list1, list2, threshold):
    """Check which coordinates in list1 are close to any in list2"""
    close_pairs = set()  # To store pairs of coordinates that are close
    for coord1 in list1:
        for coord2 in list2:
            distance = np.sqrt((coord1[0] - coord2[0]) ** 2 + (coord1[1] - coord2[1]) ** 2)
            if distance < threshold:
                close_pairs.add(coord1)
    return close_pairs

def proximity_check_fuse(list1, list2, x_threshold ,threshold):
    """Check proximity with separate X and Y thresholds for fusion detection"""
    close_pairs = set()  # To store pairs of coordinates meeting the criteria
    for coord1 in list1:
        for coord2 in list2:
            x_difference = abs(coord1[0] - coord2[0])
            if x_difference < x_threshold:  # Check if x values are the same
                y_difference = abs(coord1[1] - coord2[1])
                if y_difference < threshold:  # Check if y difference is within the threshold
                    close_pairs.add(coord1)
    return close_pairs

def enhanced_proximity_check(container_input, content_input, 
                           expand_left=0, expand_right=0, 
                           expand_above=0, expand_below=0, 
                           threshold=0.8, use_bounding_box=True, return_bool=False):
    """
    Unified proximity checking function that can handle both bounding box detection 
    and area-based proximity with expandable regions.
    
    Args:
        container_input: Can be:
                        - List of bounding box data (from area="all" calls)
                        - List of (x, y) coordinates
                        - String path to image (will find coordinates/bounding boxes)
        content_input: Can be:
                      - List of (x, y) coordinates
                      - String path to image (will find coordinates)
        expand_left: Pixels to expand bounding box/area to the left
        expand_right: Pixels to expand bounding box/area to the right  
        expand_above: Pixels to expand bounding box/area above
        expand_below: Pixels to expand bounding box/area below
        threshold: Image matching threshold (default 0.8)
        use_bounding_box: If True, use actual bounding boxes; if False, create fixed areas around points
        return_bool: If True, return boolean; if False, return list of matching coordinates
        
    Returns:
        If return_bool=True: Boolean indicating if any content is found in expanded areas
        If return_bool=False: List of content coordinates that fall inside expanded areas
    """
    # Handle container_input - get coordinates or bounding boxes
    if isinstance(container_input, str):
        if use_bounding_box:
            # Get bounding boxes for expandable detection
            container_data = ifexist_match(container_input, threshold, area="all")
        else:
            # Get coordinates for fixed area detection
            container_data = ifexist_match(container_input, threshold)
        if not container_data:
            return False if return_bool else []
    elif isinstance(container_input, list):
        # Already processed data
        container_data = container_input
        if not container_data:
            return False if return_bool else []
    else:
        # Invalid input type
        return False if return_bool else []
        
    # Handle content_input - convert to coordinates if it's an image path
    if isinstance(content_input, str):
        content_coords = ifexist_match(content_input, threshold)
        if not content_coords:
            return False if return_bool else []
    elif isinstance(content_input, list):
        content_coords = content_input
        if not content_coords:
            return False if return_bool else []
    else:
        # Invalid input type
        return False if return_bool else []
    
    matching_coords = []
    
    # Check each content coordinate against all container areas
    for content_x, content_y in content_coords:
        found_match = False
        
        for container_item in container_data:
            if use_bounding_box and isinstance(container_item, dict):
                # Bounding box mode with expansion
                base_x_min = container_item['left'][0]
                base_x_max = container_item['right'][0]
                base_y_min = container_item['top'][1]
                base_y_max = container_item['bottom'][1]
                
                # Expand the bounding box
                x_min = base_x_min - expand_left
                x_max = base_x_max + expand_right
                y_min = base_y_min - expand_above
                y_max = base_y_max + expand_below
                
            elif not use_bounding_box and isinstance(container_item, tuple):
                # Fixed area mode around coordinates
                center_x, center_y = container_item
                x_min = center_x - expand_left
                x_max = center_x + expand_right
                y_min = center_y - expand_above
                y_max = center_y + expand_below
                
            else:
                # Skip incompatible data
                continue
                
            # Check if content coordinate falls within the expanded area
            if (x_min <= content_x <= x_max and y_min <= content_y <= y_max):
                matching_coords.append((content_x, content_y))
                found_match = True
                break  # Found inside one area, no need to check others for this coordinate
        
        # For boolean mode, return True immediately on first match
        if return_bool and found_match:
            return True
                
    return bool(matching_coords) if return_bool else matching_coords


def get_resolution(monitor_index=None):
    """Gets the resolution of the specified monitor or the game monitor"""
    mon = get_monitor_info(monitor_index)
    return mon['width'], mon['height']

def non_max_suppression_fast(boxes, overlapThresh=0.5):
    """Remove multiple detections on the same position"""
    if len(boxes) == 0:
        return []

    # Convert to float if necessary
    if boxes.dtype.kind == "i":
        boxes = boxes.astype("float")

    # Initialize the list of picked indexes
    pick = []

    # Get coordinates of bounding boxes
    x1 = boxes[:, 0]
    y1 = boxes[:, 1]
    x2 = boxes[:, 2]
    y2 = boxes[:, 3]

    # Compute the area of the bounding boxes and sort by the bottom-right y-coordinate
    area = (x2 - x1 + 1) * (y2 - y1 + 1)
    idxs = np.argsort(y2)

    # Keep looping while some indexes still remain in the indexes list
    while len(idxs) > 0:
        # Grab the last index in the indexes list, add the index value to the list of picked indexes
        last = len(idxs) - 1
        i = idxs[last]
        pick.append(i)

        # Find the largest (x, y) coordinates for the start of the bounding box
        # and the smallest (x, y) coordinates for the end of the bounding box
        xx1 = np.maximum(x1[i], x1[idxs[:last]])
        yy1 = np.maximum(y1[i], y1[idxs[:last]])
        xx2 = np.minimum(x2[i], x2[idxs[:last]])
        yy2 = np.minimum(y2[i], y2[idxs[:last]])

        # Compute the width and height of the bounding box
        w = np.maximum(0, xx2 - xx1 + 1)
        h = np.maximum(0, yy2 - yy1 + 1)

        # Compute the ratio of overlap
        overlap = (w * h) / area[idxs[:last]]

        # Delete all indexes from the index list that have an overlap greater than the threshold
        idxs = np.delete(idxs, np.concatenate(([last], np.where(overlap > overlapThresh)[0])))

    # Return only the bounding boxes that were picked
    return boxes[pick].astype("int")

def get_aspect_ratio(monitor_index=None):
    """Get monitor aspect ratio (4:3, 16:9, 16:10, or None)"""
    width, height = get_resolution(monitor_index)
    if (width / 4) * 3 == height:
        return "4:3"
    if (width / 16) * 9 == height:
        return "16:9"
    if (width / 16) * 10 == height:
        return "16:10"
    else:
        return None

# ==================== INTERNAL DRY SCALING FUNCTIONS ====================

def _uniform_scale_coordinates(x, y, reference_width, reference_height, use_uniform=True):
    """Internal function that does all coordinate scaling work"""
    scale_factor_x = MONITOR_WIDTH / reference_width
    scale_factor_y = MONITOR_HEIGHT / reference_height
    
    # Get offsets from shared_vars with fallback to 0
    x_offset = shared_vars.x_offset
    y_offset = shared_vars.y_offset
    
    if use_uniform:
        # Use minimum scale factor to maintain aspect ratio (true uniform scaling)
        scale_factor = min(scale_factor_x, scale_factor_y)
        scaled_x = round(x * scale_factor) + x_offset
        scaled_y = round(y * scale_factor) + y_offset
    else:
        # Use individual scale factors (stretches to fill screen)
        scaled_x = round(x * scale_factor_x) + x_offset
        scaled_y = round(y * scale_factor_y) + y_offset
    
    return scaled_x, scaled_y

def _scale_single_coordinate(coord, reference_dimension, actual_dimension, offset=0):
    """Scale a single coordinate dimension"""
    return round(coord * actual_dimension / reference_dimension) + offset

# ==================== PUBLIC SCALING FUNCTIONS (BACKWARD COMPATIBLE) ====================

def padding_none_16_9_monitor(x: int, y: int) -> tuple[int, int]:
    """Correct X, Y coordinate when monitor doesn't follow 16:9 standard.
    
    This require setting resultion to 1920x1080 in the game manually.
    """
    if IS_NON_STANDARD_RATIO:
        x_offset = (MONITOR_WIDTH - EXPECTED_WIDTH)//2
        y_offset = (MONITOR_HEIGHT - EXPECTED_HEIGHT)//2
        return x + x_offset, y + y_offset
    return x, y

def scale_x(x: int, *, padding: bool = True) -> int:
    """Scale X coordinate based on 1440p reference to the actual monitor width."""
    _x = _scale_single_coordinate(x, REFERENCE_WIDTH_1440P, EXPECTED_WIDTH, shared_vars.x_offset)
    if padding:
        _x, _ = padding_none_16_9_monitor(_x, 0)
    return _x

def scale_y(y: int, *, padding: bool = True) -> int:
    """Scale Y coordinate based on 1440p reference to the actual monitor height."""
    _y = _scale_single_coordinate(y, REFERENCE_HEIGHT_1440P, EXPECTED_HEIGHT, shared_vars.y_offset)
    if padding:
        _, _y = padding_none_16_9_monitor(0, _y)
    return _y

def scale_x_1080p(x: int, *, padding: bool = True) -> int:
    """Scale X coordinate based on 1080p reference to the actual monitor width."""
    _x = _scale_single_coordinate(x, REFERENCE_WIDTH_1080P, EXPECTED_WIDTH, shared_vars.x_offset)
    if padding:
        _x, _ = padding_none_16_9_monitor(_x, 0)
    return _x

def scale_y_1080p(y: int, *, padding: bool = True) -> int:
    """Scale Y coordinate based on 1080p reference to the actual monitor height."""
    _y = _scale_single_coordinate(y, REFERENCE_HEIGHT_1080P, EXPECTED_HEIGHT, shared_vars.y_offset)
    if padding:
        _, _y = padding_none_16_9_monitor(0, _y)
    return _y

def uniform_scale_single(coord):
    """Scale a single coordinate using the minimum scale factor to maintain aspect ratio"""
    scale_factor_x = MONITOR_WIDTH / REFERENCE_WIDTH_1440P
    scale_factor_y = MONITOR_HEIGHT / REFERENCE_HEIGHT_1440P
    scale_factor = min(scale_factor_x, scale_factor_y)
    return round(scale_factor * coord)

def uniform_scale_coordinates(x, y):
    """Scale (x, y) coordinates from 1440p reference to the current screen resolution."""
    return _uniform_scale_coordinates(x, y, REFERENCE_WIDTH_1440P, REFERENCE_HEIGHT_1440P, use_uniform=False)

def uniform_scale_coordinates_1080p(x, y):
    """Scale (x, y) coordinates from 1080p reference to the current screen resolution."""
    return _uniform_scale_coordinates(x, y, REFERENCE_WIDTH_1080P, REFERENCE_HEIGHT_1080P, use_uniform=False)

def scale_coordinates_1440p(x, y):
    """Scale (x, y) coordinates from 1440p reference to actual screen resolution"""
    return scale_x(x), scale_y(y)

def scale_coordinates_1080p(x, y):
    """Scale (x, y) coordinates from 1080p reference to actual screen resolution"""
    return scale_x_1080p(x), scale_y_1080p(y)

def scale_offset_1440p(x: int, y: int) -> tuple[int, int]:
    """Scale (x, y) offset from 1440p reference to actual screen resolution. Will not perform non 16:9 screen padding."""
    return scale_x(x, padding=False), scale_y(y, padding=False)

def scale_offset_1080p(x: int, y: int) -> tuple[int, int]:
    """Scale (x, y) offset from 1080p reference to actual screen resolution. Will not perform non 16:9 screen padding."""
    return scale_x_1080p(x, padding=False), scale_y_1080p(y, padding=False)

# ==================== GAME-SPECIFIC FUNCTIONS ====================

def click_skip(times):
    """Click Skip the amount of time specified"""
    mouse_move_click(*scale_coordinates_1080p(895, 465))
    for i in range(times):
        mouse_click()

def wait_skip(img_path, threshold=0.8):
    """Clicks on the skip button and waits for specified element to appear"""
    mouse_move_click(*scale_coordinates_1080p(895, 465))
    while(not element_exist(img_path, threshold)):
        mouse_click()
    click_matching(img_path, threshold)

def click_matching(image_path, threshold=0.8, area="center", mousegoto200=False, grayscale=False, no_grayscale=False, debug=False, recursive=True, x1=None, y1=None, x2=None, y2=None):
    """Find and click on image match. Returns True if clicked, False if not found."""
    found = ifexist_match(image_path, threshold, area,mousegoto200, grayscale, no_grayscale, debug, x1, y1, x2, y2)
    if found:
        x, y = found[0]
        mouse_move_click(x, y, log_click=False)
        # Handle both multiprocessing.Value and plain float
        delay = shared_vars.click_delay.value if hasattr(shared_vars.click_delay, 'value') else shared_vars.click_delay
        time.sleep(delay)
        return True
    elif recursive:
        return click_matching(image_path, threshold, area, mousegoto200, grayscale=grayscale, no_grayscale=no_grayscale, debug=debug, x1=x1, y1=y1, x2=x2, y2=y2)
    else:
        return False
    
def element_exist(img_path, threshold=0.8, area="center",mousegoto200=False, grayscale=False, no_grayscale=False, debug=False, quiet_failure=False, x1=None, y1=None, x2=None, y2=None):
    """Checks if the element exists if not returns none"""
    result = match_image(img_path, threshold, area, mousegoto200, grayscale, no_grayscale, debug, quiet_failure, x1, y1, x2, y2)
    return result

def ifexist_match(img_path, threshold=0.8, area="center",mousegoto200=False, grayscale=False, no_grayscale=False, debug=False, x1=None, y1=None, x2=None, y2=None):
    """checks if exists and returns the image location if found"""
    result = match_image(img_path, threshold, area,mousegoto200, grayscale, no_grayscale, debug, False, x1, y1, x2, y2)
    return result

def squad_order(status):
    """Returns a list of the image locations depending on the sinner order specified in the json file"""
    # Use cached config instead of file I/O
    squads = shared_vars.ConfigCache.get_config("squad_order")
    squad = squads.get(status, {})
    
    # Calculate scaled character positions directly
    character_positions = {
        "yisang": (580, 500),
        "faust": (847, 500),
        "donquixote": (1113, 500),
        "ryoshu": (1380, 500),
        "meursault": (1647, 500),
        "honglu": (1913, 500),
        "heathcliff": (580, 900),
        "ishmael": (847, 900),
        "rodion": (1113, 900),
        "sinclair": (1380, 900),
        "outis": (1647, 900),
        "gregor": (1913, 900)
    }
    
    # Create reverse lookup for O(n) performance
    position_to_char = {pos: name for name, pos in squad.items()}
    
    sinner_order = []
    for i in range(1, 13):
        char_name = position_to_char.get(i)
        if char_name and char_name in character_positions:
            base_x, base_y = character_positions[char_name]
            scaled_x, scaled_y = scale_coordinates_1440p(base_x, base_y)
            sinner_order.append((scaled_x, scaled_y))
    
    return sinner_order

def luminence(x,y):
    """Get Luminence of the pixel and return overall coefficient"""
    screenshot = capture_screen()
    pixel_image = screenshot[y, x]
    coeff = (int(pixel_image[0]) + int(pixel_image[1]) + int(pixel_image[2])) / 3
    return coeff

def error_screenshot():
    """Take a screenshot for error debugging"""
    error_dir = os.path.join(BASE_PATH, "error")
    os.makedirs(error_dir, exist_ok=True)
    with mss() as sct:
        monitor = sct.monitors[shared_vars.game_monitor]  # Use the configured game monitor
        screenshot = sct.grab(monitor)
        png = to_png(screenshot.rgb, screenshot.size)
        timestamp = time.strftime("%Y%m%d_%H%M%S")
        with open(os.path.join(error_dir, timestamp + ".png"), "wb") as f:
            f.write(png)

def set_game_monitor(monitor_index):
    """Set which monitor the game is running on"""
    with mss() as sct:
        if monitor_index < 1 or monitor_index >= len(sct.monitors):
            logger.warning(f"Invalid monitor index {monitor_index} (valid: 1-{len(sct.monitors)-1})")
            shared_vars.game_monitor = 1
        else:
            shared_vars.game_monitor = monitor_index
    
    # Re-detect monitor resolution after changing monitor
    detect_monitor_resolution()
    return shared_vars.game_monitor

def list_available_monitors():
    """List all available monitors and their properties"""
    with mss() as sct:
        monitors = []
        for i, monitor in enumerate(sct.monitors):
            if i == 0:  # Skip the "all monitors" entry
                continue
            monitors.append({
                "index": i,
                "left": monitor["left"],
                "top": monitor["top"],
                "width": monitor["width"],
                "height": monitor["height"]
            })
        return monitors

def get_monitor_resolution():
    """Get the current monitor resolution"""
    return MONITOR_WIDTH, MONITOR_HEIGHT

def check_internet_connection(timeout=5):
    """Check if internet is reachable by attempting to connect to Google"""
    import urllib.request
    import urllib.error
    
    try:
        urllib.request.urlopen('https://www.google.com', timeout=timeout)
        return True
    except (urllib.error.URLError, OSError):
        return False

def draw_debug_rect(x, y, width, height, duration=2):
    """Draw a rectangle on screen for debugging"""
    user32 = ctypes.windll.user32
    gdi32 = ctypes.windll.gdi32
    
    desktop_dc = user32.GetDC(0)
    pen = gdi32.CreatePen(0, 4, 0x05B0FE)
    old_pen = gdi32.SelectObject(desktop_dc, pen)
    old_brush = gdi32.SelectObject(desktop_dc, gdi32.GetStockObject(5))
    
    gdi32.Rectangle(desktop_dc, int(x), int(y), int(x + width), int(y + height))
    
    time.sleep(duration)
    
    rect = wintypes.RECT(int(x) - 5, int(y) - 5, int(x + width) + 5, int(y + height) + 5)
    user32.InvalidateRect(0, ctypes.byref(rect), 1)
    
    gdi32.SelectObject(desktop_dc, old_pen)
    gdi32.SelectObject(desktop_dc, old_brush)
    gdi32.DeleteObject(pen)
    user32.ReleaseDC(0, desktop_dc)
