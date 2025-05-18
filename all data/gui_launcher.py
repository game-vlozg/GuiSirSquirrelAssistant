import customtkinter as ctk
import subprocess
import signal
import os
import sys
import platform
from tkinter import messagebox
import keyboard
import json
import time
import threading
import logging
import queue
from threading import Thread
import configparser
import re

# Determine if running as executable or script
def get_base_path():
    if getattr(sys, 'frozen', False):
        # Running as compiled exe
        return os.path.dirname(sys.executable)
    else:
        # Running as script
        return os.path.dirname(os.path.abspath(__file__))

# Setting up file and directory paths using the base path
BASE_PATH = get_base_path()
sys.path.append(os.path.join(BASE_PATH, 'src'))

# Define python interpreter path based on whether we're frozen or not
def get_python_command():
    if getattr(sys, 'frozen', False):
        # If running as exe, use the executable path to launch Python modules
        if platform.system() == "Windows":
            return os.path.join(BASE_PATH, "gui_launcher.exe")
        else:
            return os.path.join(BASE_PATH, "gui_launcher")
    else:
        # If running as script, use system's Python interpreter
        return sys.executable

PYTHON_CMD = get_python_command()

# Script paths
MIRROR_SCRIPT_PATH = os.path.join(BASE_PATH, "src", "compiled_runner.py")
EXP_SCRIPT_PATH = os.path.join(BASE_PATH, "src", "exp_runner.py")
THREADS_SCRIPT_PATH = os.path.join(BASE_PATH, "src", "threads_runner.py")
THEME_RESTART_PATH = os.path.join(BASE_PATH, "src", "theme_restart.py")

# Configuration file paths
CONFIG_DIR = os.path.join(BASE_PATH, "config")
JSON_PATH = os.path.join(CONFIG_DIR, "squad_order.json")
SLOW_JSON_PATH = os.path.join(CONFIG_DIR, "slow_squad_order.json")
STATUS_SELECTION_PATH = os.path.join(CONFIG_DIR, "status_selection.txt")
GUI_CONFIG_PATH = os.path.join(CONFIG_DIR, "gui_config.txt")
HELP_TEXT_PATH = os.path.join(BASE_PATH, "Help.txt")

# Create config directory if it doesn't exist
os.makedirs(CONFIG_DIR, exist_ok=True)

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

# Convenience functions for different log levels
def debug(message):
    logger.debug(message)

def info(message):
    logger.info(message)

def warning(message):
    logger.warning(message)

def error(message):
    logger.error(message)

def critical(message):
    logger.critical(message)

# Module names for log filtering
LOG_MODULES = {
    "GUI": "__main__",
    "Mirror Dungeon": "compiled_runner",
    "Exp": "exp_runner",
    "Threads": "threads_runner",
    "Common": "common",
    "Core": "core",
    "Mirror": "mirror",
    "Mirror Utils": "mirror_utils",
    "Theme": "theme_restart",
    "Luxcavation": "luxcavation_functions",
    "Other": "other"
}

# List of log messages to filter out (noise reduction)
FILTERED_MESSAGES = [
    "Saved GUI configuration",
    "Loaded existing log file with filters applied",
    "Log file cleared",
    "GUI initialized",
    "Created tab layout with all tabs",
    "Mirror Dungeon tab setup complete",
    "Exp tab setup complete",
    "Threads tab setup complete",
    "Settings tab setup complete",
    "Help tab setup complete",
    "Logs tab setup complete",
    "Keyboard shortcuts registered from configuration",
    "Starting Pro Peepol Macro application",
    "Application closing",
    "Application closed",
    "Loaded squad data from file",
    "Saved slow squad data to file",
    "Registered keyboard shortcuts: ctrl+q (Mirror), ctrl+e (Exp), ctrl+r (Threads)"
]

# Available themes for the UI - USING ONLY VALIDATED THEMES THAT EXIST
THEMES = {
    "Dark": {"mode": "dark", "theme": "dark-blue"},
    "Blue Dark": {"mode": "dark", "theme": "blue"},
    "Green Dark": {"mode": "dark", "theme": "green"},
    "Light": {"mode": "light", "theme": "blue"}
}

# Game status columns layout
STATUS_COLUMNS = [
    ["sinking", "burn", "poise"],
    ["charge", "rupture", "slash", "blunt"],
    ["bleed", "tremor", "pierce"]
]

# Character list for the game
SINNER_LIST = [
    "Yi Sang", "Faust", "Don Quixote", "Ryōshū", "Meursault",
    "Hong Lu", "Heathcliff", "Ishmael", "Rodion", "Sinclair", "Gregor", "Outis"
]

# Team layout positioning in the grid
TEAM_ORDER = [
    ("sinking", 0, 0), ("charge", 0, 1), ("slash", 0, 2),
    ("blunt", 1, 0), ("burn", 1, 1), ("rupture", 1, 2),
    ("poise", 2, 0), ("bleed", 2, 1), ("tremor", 2, 2),
    ("pierce", 3, 0), ("None", 3, 1)
]

# Global variables for data storage and state tracking
squad_data = {}
slow_squad_data = {}
checkbox_vars = {}
dropdown_vars = {}
expand_frames = {}
process = None
exp_process = None
threads_process = None
filtered_messages_enabled = True

# Helper function for character name normalization
def sinner_key(name):
    """Convert a sinner name to a standardized key"""
    return name.lower().replace(" ", "").replace("ō", "o").replace("ū", "u")

# Functions for JSON data management
def load_json():
    """Load squad data from JSON files"""
    global squad_data, slow_squad_data
    if os.path.exists(JSON_PATH):
        with open(JSON_PATH, "r") as f:
            squad_data = json.load(f)
        debug("Loaded squad data from file")
    else:
        squad_data = {}
        warning("Squad data file not found, using empty data")
    # Copy squad to slow
    slow_squad_data = json.loads(json.dumps(squad_data))
    save_slow_json()

def save_json():
    """Save squad data to JSON file"""
    with open(JSON_PATH, "w") as f:
        json.dump(squad_data, f, indent=4)
    debug("Saved squad data to file")

def save_slow_json():
    """Save slow squad data to JSON file"""
    with open(SLOW_JSON_PATH, "w") as f:
        json.dump(slow_squad_data, f, indent=4)
    debug("Saved slow squad data to file")

def delayed_slow_sync():
    """Sync squad data to slow squad with delay"""
    time.sleep(0.5)
    slow_squad_data.update(json.loads(json.dumps(squad_data)))
    save_slow_json()
    debug("Updated slow squad data after delay")

# Functions for status selection management
def load_initial_selections():
    """Load previously selected checkboxes"""
    try:
        with open(STATUS_SELECTION_PATH, "r") as f:
            return {line.strip() for line in f if line.strip()}
    except FileNotFoundError:
        warning("Status selection file not found")
        return set()

# Process state checking functions
def is_any_process_running():
    """Check if any automation is currently running"""
    return process is not None or exp_process is not None or threads_process is not None

def get_running_process_name():
    """Get the name of the currently running process"""
    if process is not None:
        return "Mirror Dungeon"
    if exp_process is not None:
        return "Exp"
    if threads_process is not None:
        return "Threads"
    return None

# Initialize the main application window
root = ctk.CTk()
root.geometry("433x344")  # Default window size
root.title("Pro Peepol Macro😎")

# Configuration management functions
def load_gui_config():
    """Load GUI configuration from file"""
    config = configparser.ConfigParser()
    
    # Default values
    defaults = {
        'theme': 'Dark',
        'mirror_runs': '1',
        'exp_runs': '1',
        'exp_stage': '1',
        'threads_runs': '1',
        'threads_difficulty': '20',
        'window_width': '433',
        'window_height': '344',
        'filter_noise': 'True'
    }
    
    # Default log filter values
    log_filter_defaults = {
        'debug': 'False',
        'info': 'False',
        'warning': 'True',
        'error': 'True',
        'critical': 'True'
    }
    
    # Default module filter values
    module_filter_defaults = {}
    for module in LOG_MODULES:
        module_filter_defaults[module.lower().replace(' ', '_')] = 'True'
    
    # Default keyboard shortcut values
    shortcut_defaults = {
        'mirror_dungeon': 'ctrl+q',
        'exp': 'ctrl+e',
        'threads': 'ctrl+r'
    }
    
    # See if the file exists and load it
    if os.path.exists(GUI_CONFIG_PATH):
        try:
            config.read(GUI_CONFIG_PATH)
            if 'Settings' not in config:
                config['Settings'] = {}
            
            # Ensure all defaults are present
            for key, value in defaults.items():
                if key not in config['Settings']:
                    config['Settings'][key] = value
            
            # Add LogFilters section if it doesn't exist
            if 'LogFilters' not in config:
                config['LogFilters'] = {}
                
            # Ensure all log filter defaults are present
            for key, value in log_filter_defaults.items():
                if key not in config['LogFilters']:
                    config['LogFilters'][key] = value
            
            # Add ModuleFilters section if it doesn't exist
            if 'ModuleFilters' not in config:
                config['ModuleFilters'] = {}
                
            # Ensure all module filter defaults are present
            for key, value in module_filter_defaults.items():
                if key not in config['ModuleFilters']:
                    config['ModuleFilters'][key] = value
            
            # Add Shortcuts section if it doesn't exist
            if 'Shortcuts' not in config:
                config['Shortcuts'] = {}
                
            # Ensure all shortcut defaults are present
            for key, value in shortcut_defaults.items():
                if key not in config['Shortcuts']:
                    config['Shortcuts'][key] = value
                    
            # Make sure saved theme is one of the available themes
            if config['Settings']['theme'] not in THEMES:
                config['Settings']['theme'] = 'Dark'
                    
        except Exception as e:
            error(f"Error loading GUI config: {e}")
            config['Settings'] = defaults
            config['LogFilters'] = log_filter_defaults
            config['ModuleFilters'] = module_filter_defaults
            config['Shortcuts'] = shortcut_defaults
    else:
        # First launch - use defaults
        config['Settings'] = defaults
        config['LogFilters'] = log_filter_defaults
        config['ModuleFilters'] = module_filter_defaults
        config['Shortcuts'] = shortcut_defaults
    
    save_gui_config(config)
    return config

def save_gui_config(config=None):
    """Save GUI configuration to file"""
    if config is None:
        # Create config from current state
        config = configparser.ConfigParser()
        config['Settings'] = {
            'theme': theme_var.get(),
            'mirror_runs': entry.get(),
            'exp_runs': exp_entry.get(),
            'exp_stage': exp_stage_var.get(),
            'threads_runs': threads_entry.get(),
            'threads_difficulty': threads_difficulty_var.get(),
            'window_width': str(root.winfo_width()),
            'window_height': str(root.winfo_height()),
            'filter_noise': str(filtered_messages_enabled)
        }
        
        # Save log filter settings
        config['LogFilters'] = {
            'debug': str(log_filters['DEBUG'].get()),
            'info': str(log_filters['INFO'].get()),
            'warning': str(log_filters['WARNING'].get()),
            'error': str(log_filters['ERROR'].get()),
            'critical': str(log_filters['CRITICAL'].get())
        }
        
        # Save module filter settings
        config['ModuleFilters'] = {}
        for module in LOG_MODULES:
            config['ModuleFilters'][module.lower().replace(' ', '_')] = str(module_filters[module].get())
        
        # Save keyboard shortcuts
        config['Shortcuts'] = {
            'mirror_dungeon': shortcut_vars['mirror_dungeon'].get(),
            'exp': shortcut_vars['exp'].get(),
            'threads': shortcut_vars['threads'].get()
        }
    
    try:
        with open(GUI_CONFIG_PATH, 'w') as f:
            config.write(f)
        debug("Saved GUI configuration")
    except Exception as e:
        error(f"Error saving GUI config: {e}")

# Load configuration before creating UI elements
config = load_gui_config()
filtered_messages_enabled = config['Settings'].getboolean('filter_noise', True)

# Create log filter UI variables from config
log_filters = {
    "DEBUG": ctk.BooleanVar(value=config['LogFilters'].getboolean('debug', False)),
    "INFO": ctk.BooleanVar(value=config['LogFilters'].getboolean('info', False)),
    "WARNING": ctk.BooleanVar(value=config['LogFilters'].getboolean('warning', True)),
    "ERROR": ctk.BooleanVar(value=config['LogFilters'].getboolean('error', True)),
    "CRITICAL": ctk.BooleanVar(value=config['LogFilters'].getboolean('critical', True))
}

# Create module filter UI variables from config
module_filters = {}
for module in LOG_MODULES:
    key = module.lower().replace(' ', '_')
    module_filters[module] = ctk.BooleanVar(value=config['ModuleFilters'].getboolean(key, True))

# Create keyboard shortcut variables from config
shortcut_vars = {
    'mirror_dungeon': ctk.StringVar(value=config['Shortcuts'].get('mirror_dungeon', 'ctrl+q')),
    'exp': ctk.StringVar(value=config['Shortcuts'].get('exp', 'ctrl+e')),
    'threads': ctk.StringVar(value=config['Shortcuts'].get('threads', 'ctrl+r'))
}

# Custom logging handler for displaying logs in the GUI
class TextWidgetHandler(logging.Handler):
    """Log handler that redirects logs to a CTkTextbox widget with filtering"""
    
    def __init__(self, text_widget, filters, module_filters):
        super().__init__()
        self.text_widget = text_widget
        self.filters = filters
        self.module_filters = module_filters
        self.queue = queue.Queue()
        self.running = True
        self.update_thread = Thread(target=self._update_widget)
        self.update_thread.daemon = True
        self.update_thread.start()
        
        # Set formatter for the handler
        self.setFormatter(logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s'))
        
    def emit(self, record):
        """Put log message in queue for the update thread"""
        self.queue.put(record)
    
    def _update_widget(self):
        """Thread that updates the text widget with new log messages"""
        while self.running:
            try:
                # Get log message from queue (with timeout to allow thread to exit)
                record = self.queue.get(block=True, timeout=0.2)
                
                # Check if we should display this level based on BooleanVar value
                level_name = record.levelname
                module_name = self._get_module_name(record.name)
                
                # Check both level and module filters
                if level_name in self.filters and module_name in self.module_filters:
                    show_level = self.filters[level_name].get()
                    show_module = self.module_filters[module_name].get()
                    
                    if show_level and show_module and self._should_show_message(record.getMessage()):
                        # Format the message and schedule GUI update
                        msg = self.format(record)
                        # Replace "__main__" with "GUI" in the formatted message
                        msg = msg.replace(" - __main__ - ", " - GUI - ")
                        root.after(0, self._append_log, msg)
                
                self.queue.task_done()
            except queue.Empty:
                pass
            except Exception as e:
                # Avoid crashing the thread on any error
                try:
                    print(f"Error in log update thread: {e}")
                except:
                    pass
    
    def _get_module_name(self, logger_name):
        """Map logger name to module name for filtering"""
        # Map "__main__" to "GUI"
        if logger_name == "__main__":
            return "GUI"
        
        # Try to match other module names
        for module, pattern in LOG_MODULES.items():
            if pattern in logger_name:
                return module
        
        # Default to "Other" if no match
        return "Other"
    
    def _should_show_message(self, message):
        """Check if the message should be shown or filtered out as noise"""
        if not filtered_messages_enabled:
            return True
            
        # Check if the message contains any filtered message
        for filtered_msg in FILTERED_MESSAGES:
            if filtered_msg in message:
                return False
                
        # Check for loaded pre-checked statuses pattern
        if re.match(r"Loaded pre-checked statuses: .+", message):
            return False
            
        return True
    
    def _append_log(self, msg):
        """Append log message to the text widget"""
        try:
            self.text_widget.configure(state="normal")  # Enable editing
            self.text_widget.insert("end", msg + "\n")  # Add new log with newline
            self.text_widget.see("end")  # Scroll to the end
            self.text_widget.configure(state="disabled")  # Disable editing
        except Exception as e:
            # Handle any errors that might occur
            pass
    
    def close(self):
        """Clean up resources when handler is closed"""
        self.running = False
        if self.update_thread.is_alive():
            self.update_thread.join(timeout=1.0)
        super().close()

    # Override the filter method to avoid using the built-in filters
    def filter(self, record):
        """Don't use standard filtering"""
        return True

# Log file monitor class for real-time log display
class LogFileMonitor:
    """Monitors the log file for changes and updates the GUI log display"""
    
    def __init__(self, log_file_path, text_widget, level_filters, module_filters, update_interval=500):
        self.log_file_path = log_file_path
        self.text_widget = text_widget
        self.level_filters = level_filters
        self.module_filters = module_filters
        self.update_interval = update_interval  # Check every 500ms
        self.last_position = 0
        self.running = True
    
    def start_monitoring(self, root):
        """Start the monitoring process using tkinter's after method"""
        self._check_for_updates(root)
    
    def stop_monitoring(self):
        """Stop the monitoring process"""
        self.running = False
    
    def _check_for_updates(self, root):
        """Check for new content in the log file and update the display"""
        if not self.running:
            return
            
        try:
            # Get current file size
            file_size = os.path.getsize(self.log_file_path)
            
            # If file has grown
            if file_size > self.last_position:
                with open(self.log_file_path, 'r') as f:
                    # Seek to the last position we read
                    f.seek(self.last_position)
                    # Read new lines
                    new_lines = f.readlines()
                
                # Update the last read position
                self.last_position = file_size
                
                # Apply filters and add new lines to the display
                self.text_widget.configure(state="normal")
                for line in new_lines:
                    # Process the line for filtering
                    self._process_log_line(line)
                
                # Scroll to the end if there were new lines
                if new_lines:
                    self.text_widget.see("end")
                
                self.text_widget.configure(state="disabled")
            
            # If file size has decreased (file was rotated or cleared)
            elif file_size < self.last_position:
                self.last_position = 0
                # Clear the display
                self.text_widget.configure(state="normal")
                self.text_widget.delete("1.0", "end")
                self.text_widget.configure(state="disabled")
                
        except Exception as e:
            print(f"Error monitoring log file: {e}")
        
        # Schedule the next check
        if self.running:
            root.after(self.update_interval, lambda: self._check_for_updates(root))
    
    def _process_log_line(self, line):
        """Process a single log line, applying filters and formatting"""
        try:
            # Check log level filters
            if " - DEBUG - " in line and not self.level_filters["DEBUG"].get():
                return
            elif " - INFO - " in line and not self.level_filters["INFO"].get():
                return
            elif " - WARNING - " in line and not self.level_filters["WARNING"].get():
                return
            elif " - ERROR - " in line and not self.level_filters["ERROR"].get():
                return
            elif " - CRITICAL - " in line and not self.level_filters["CRITICAL"].get():
                return
            
            # Check module filters
            module_found = False
            for module, pattern in LOG_MODULES.items():
                if f" - {pattern} - " in line:
                    module_found = True
                    if not self.module_filters[module].get():
                        return
                    # Replace "__main__" with "GUI" if needed
                    if pattern == "__main__":
                        line = line.replace(" - __main__ - ", " - GUI - ")
                    break
            
            # If no specific module was found, check the "Other" filter
            if not module_found and not self.module_filters["Other"].get():
                return
            
            # Filter out noisy messages
            if filtered_messages_enabled:
                # Skip if message contains any filtered text
                for filtered_msg in FILTERED_MESSAGES:
                    if filtered_msg in line:
                        return
                        
                # Skip pre-checked statuses logs
                if re.search(r"Loaded pre-checked statuses: .+", line):
                    return
            
            # If we made it here, the line passes all filters
            self.text_widget.insert("end", line)
            
        except Exception as e:
            print(f"Error processing log line: {e}")

# Status selection management functions
def save_selected_statuses():
    """Save selected checkboxes to file with most recent at the bottom"""
    selected = [name for name, var in checkbox_vars.items() if var.get()]
    
    # Try to read existing selections to determine order
    try:
        with open(STATUS_SELECTION_PATH, "r") as f:
            existing_selections = [line.strip() for line in f if line.strip()]
    except FileNotFoundError:
        existing_selections = []
    
    # Remove any selections that are no longer selected
    existing_selections = [s for s in existing_selections if s in selected]
    
    # Add new selections at the bottom
    for s in selected:
        if s in existing_selections:
            # Move to the end by removing and re-adding
            existing_selections.remove(s)
            existing_selections.append(s)
        else:
            # New selection, add at the end
            existing_selections.append(s)
    
    # Save the updated selections
    with open(STATUS_SELECTION_PATH, "w") as f:
        f.write("\n".join(existing_selections))
    
    info(f"Saved selected statuses: {existing_selections}")

def on_checkbox_toggle(changed_option):
    """Handle checkbox toggle events"""
    # Remove this block to allow multiple selections
    # for name, var in checkbox_vars.items():
    #     if name != changed_option:
    #         var.set(False)
    save_selected_statuses()
    info(f"Status toggled: {changed_option}")

# UI interaction functions
def toggle_expand(frame, arrow_var):
    """Toggle expansion of frames"""
    if frame.winfo_ismapped():
        frame.pack_forget()
        arrow_var.set("▶")
    else:
        frame.pack(pady=(2, 8), fill="x")
        arrow_var.set("▼")

# Dropdown management functions
def update_json_from_dropdown(status):
    """Update JSON data from dropdown selections"""
    entries = dropdown_vars[status]
    updated = {}
    for i, var in enumerate(entries):
        val = var.get()
        if val != "None":
            updated[sinner_key(val)] = i + 1
    squad_data[status] = updated
    save_json()
    threading.Thread(target=delayed_slow_sync, daemon=True).start()
    debug(f"Updated squad data for status: {status}")

def dropdown_callback(status, index, *_):
    """Handle dropdown selection changes"""
    new_val = dropdown_vars[status][index].get()
    if new_val == "None":
        update_json_from_dropdown(status)
        return

    # Check if duplicate exists
    for i, var in enumerate(dropdown_vars[status]):
        if i != index and var.get() == new_val:
            # Swap with old value from slow_squad
            old_key = next((k for k, v in slow_squad_data.get(status, {}).items() if v == index + 1), None)
            if old_key:
                old_pretty = next((x for x in SINNER_LIST if sinner_key(x) == old_key), "None")
                var.set(old_pretty)
            break

    update_json_from_dropdown(status)

# Process management functions
def kill_bot():
    """Kill Mirror Dungeon subprocess"""
    global process
    if process:
        try:
            os.kill(process.pid, signal.SIGTERM)
            info(f"Terminated Mirror Dungeon process (PID: {process.pid})")
        except Exception as e:
            error(f"Failed to kill process: {e}")
        process = None
    start_button.configure(text="Start")

def kill_exp_bot():
    """Kill Exp subprocess"""
    global exp_process
    if exp_process:
        try:
            os.kill(exp_process.pid, signal.SIGTERM)
            info(f"Terminated Exp process (PID: {exp_process.pid})")
        except Exception as e:
            error(f"Failed to kill exp process: {e}")
        exp_process = None
    exp_start_button.configure(text="Start")

def kill_threads_bot():
    """Kill Threads subprocess"""
    global threads_process
    if threads_process:
        try:
            os.kill(threads_process.pid, signal.SIGTERM)
            info(f"Terminated Threads process (PID: {threads_process.pid})")
        except Exception as e:
            error(f"Failed to kill threads process: {e}")
        threads_process = None
    threads_start_button.configure(text="Start")

# Process start functions
def start_run():
    """Start Mirror Dungeon automation"""
    global process
    
    # Check if another process is running
    if is_any_process_running() and process is None:
        running_name = get_running_process_name()
        warning(f"Cannot start Mirror Dungeon while {running_name} is running")
        return
    
    if start_button.cget("text") == "Stop":
        kill_bot()
        return
        
    try:
        count = int(entry.get())
    except ValueError:
        messagebox.showerror("Invalid Input", "Enter a valid number of runs.")
        warning("Invalid number of runs entered for Mirror Dungeon")
        return
        
    save_selected_statuses()
    
    # Create environment variables with correct paths
    env = os.environ.copy()
    env['PYTHONPATH'] = os.pathsep.join([BASE_PATH, os.path.join(BASE_PATH, 'src')])
    
    # Launch process with appropriate command
    if getattr(sys, 'frozen', False):
        # If frozen (exe), launch the script using the bundled Python
        process = subprocess.Popen([PYTHON_CMD, "-m", "src.compiled_runner", str(count)], env=env)
    else:
        # If script, use the regular Python command
        process = subprocess.Popen([sys.executable, MIRROR_SCRIPT_PATH, str(count)], env=env)
        
    start_button.configure(text="Stop")
    info(f"Started Mirror Dungeon automation with {count} runs (PID: {process.pid})")
    
    # Save the configuration
    save_gui_config()

def start_exp_run():
    """Start Exp automation"""
    global exp_process
    
    # Check if another process is running
    if is_any_process_running() and exp_process is None:
        running_name = get_running_process_name()
        warning(f"Cannot start Exp while {running_name} is running")
        return
    
    if exp_start_button.cget("text") == "Stop":
        kill_exp_bot()
        return
    
    try:
        runs = int(exp_entry.get())
        stage = int(exp_stage_var.get())
        if runs < 1 or stage < 1 or stage > 7:
            messagebox.showerror("Invalid Input", "Enter a valid number of runs and stage (1-7).")
            warning(f"Invalid input: runs={runs}, stage={stage}")
            return
    except ValueError:
        messagebox.showerror("Invalid Input", "Enter valid numbers.")
        warning("Invalid numeric input for Exp automation")
        return
    
    # Create environment variables with correct paths
    env = os.environ.copy()
    env['PYTHONPATH'] = os.pathsep.join([BASE_PATH, os.path.join(BASE_PATH, 'src')])
    
    # Launch process with appropriate command
    if getattr(sys, 'frozen', False):
        # If frozen (exe), launch the script using the bundled Python
        exp_process = subprocess.Popen([PYTHON_CMD, "-m", "src.exp_runner", str(runs), str(stage)], env=env)
    else:
        # If script, use the regular Python command
        exp_process = subprocess.Popen([sys.executable, EXP_SCRIPT_PATH, str(runs), str(stage)], env=env)
    
    exp_start_button.configure(text="Stop")
    info(f"Started Exp automation with {runs} runs on stage {stage} (PID: {exp_process.pid})")
    
    # Save the configuration
    save_gui_config()

def start_threads_run():
    """Start Threads automation"""
    global threads_process
    
    # Check if another process is running
    if is_any_process_running() and threads_process is None:
        running_name = get_running_process_name()
        warning(f"Cannot start Threads while {running_name} is running")
        return
    
    if threads_start_button.cget("text") == "Stop":
        kill_threads_bot()
        return
    
    try:
        runs = int(threads_entry.get())
        difficulty = int(threads_difficulty_var.get())
        if runs < 1 or difficulty not in [20, 30, 40, 50]:
            messagebox.showerror("Invalid Input", "Enter a valid number of runs and difficulty (20, 30, 40, or 50).")
            warning(f"Invalid input: runs={runs}, difficulty={difficulty}")
            return
    except ValueError:
        messagebox.showerror("Invalid Input", "Enter valid numbers.")
        warning("Invalid numeric input for Threads automation")
        return
    
    # Ensure the threads script path is correct
    if not os.path.exists(THREADS_SCRIPT_PATH):
        error(f"Threads runner script not found at: {THREADS_SCRIPT_PATH}")
        messagebox.showerror("Error", f"Could not find threads_runner.py in src directory. Please ensure it exists.")
        return
    
    try:
        # Create an environment with the correct paths
        env = os.environ.copy()
        env['PYTHONPATH'] = os.pathsep.join([BASE_PATH, os.path.join(BASE_PATH, 'src')])
        
        # Launch with the appropriate command
        if getattr(sys, 'frozen', False):
            # If frozen (exe), launch the script using the bundled Python
            threads_process = subprocess.Popen(
                [PYTHON_CMD, "-m", "src.threads_runner", str(runs), str(difficulty)],
                env=env
            )
        else:
            # If script, use the regular Python command
            threads_process = subprocess.Popen(
                [sys.executable, THREADS_SCRIPT_PATH, str(runs), str(difficulty)],
                env=env
            )
        
        threads_start_button.configure(text="Stop")
        info(f"Started Threads automation with {runs} runs on difficulty {difficulty} (PID: {threads_process.pid})")
        
        # Save the configuration
        save_gui_config()
    except Exception as e:
        error(f"Failed to start Threads process: {e}")
        messagebox.showerror("Error", f"Failed to start Threads automation: {e}")

# Button toggle functions
def toggle_button():
    """Toggle Mirror Dungeon button state"""
    if start_button.cget("text") == "Start":
        start_run()
    else:
        kill_bot()

def toggle_exp_button():
    """Toggle Exp button state"""
    if exp_start_button.cget("text") == "Start":
        start_exp_run()
    else:
        kill_exp_bot()

def toggle_threads_button():
    """Toggle Threads button state"""
    if threads_start_button.cget("text") == "Start":
        start_threads_run()
    else:
        kill_threads_bot()

# Theme application function
def apply_theme():
    """Apply the selected theme by restarting with theme_restart.py"""
    theme_name = theme_var.get()
    if theme_name in THEMES:
        # Show feedback immediately
        theme_label = ctk.CTkLabel(
            master=root, 
            text=f"Applying {theme_name} theme...",
            font=ctk.CTkFont(size=14)
        )
        theme_label.place(relx=0.5, rely=0.5, anchor="center")
        root.update_idletasks()  # Force update to show message
        
        # Save the current configuration before restarting
        save_gui_config()
        
        info(f"Applying theme: {theme_name} - Restarting application...")
        
        # Start theme_restart.py with the theme name and specify "Settings" tab
        subprocess.Popen([sys.executable, THEME_RESTART_PATH, theme_name, "Settings"])
        
        # Short delay then exit
        root.after(100, lambda: os._exit(0))

# Keyboard shortcut management
def register_keyboard_shortcuts():
    """Register keyboard shortcuts based on current settings"""
    # Unhook all existing keyboard shortcuts
    keyboard.unhook_all()
    
    try:
        # Register the shortcuts from the configuration
        keyboard.add_hotkey(shortcut_vars['mirror_dungeon'].get(), toggle_button)
        keyboard.add_hotkey(shortcut_vars['exp'].get(), toggle_exp_button)
        keyboard.add_hotkey(shortcut_vars['threads'].get(), toggle_threads_button)
        
        debug(f"Registered keyboard shortcuts: {shortcut_vars['mirror_dungeon'].get()} (Mirror), "
              f"{shortcut_vars['exp'].get()} (Exp), {shortcut_vars['threads'].get()} (Threads)")
    except Exception as e:
        error(f"Error registering keyboard shortcuts: {e}")
        messagebox.showerror("Invalid Shortcut", f"Failed to register shortcuts: {e}\nPlease check your shortcut format.")

# Initialize theme settings
theme_var = ctk.StringVar(value=config['Settings'].get('theme', 'Dark'))

# Make sure theme is one of the valid ones
if theme_var.get() not in THEMES:
    theme_var.set("Dark")
    
ctk.set_appearance_mode(THEMES[theme_var.get()]["mode"])
ctk.set_default_color_theme(THEMES[theme_var.get()]["theme"])

# Set window size from config
window_width = config['Settings'].getint('window_width', 433)
window_height = config['Settings'].getint('window_height', 344)
root.geometry(f"{window_width}x{window_height}")

# Performance improvement: Disable complex logging at startup
info("GUI initialized")

# Tab layout
tabs = ctk.CTkTabview(master=root, width=window_width-40, height=window_height-60)
tabs.pack(padx=20, pady=20, fill="both", expand=True)

# Create all tabs
tab_md = tabs.add("Mirror Dungeon")
tab_exp = tabs.add("Exp")
tab_threads = tabs.add("Threads")
tab_settings = tabs.add("Settings")
tab_help = tabs.add("Help")
tab_logs = tabs.add("Logs")

# Check if we're starting after a theme change and set the tab immediately
if len(sys.argv) > 1 and sys.argv[1] in THEMES.keys():
    # Theme was specified as first argument (restarted after theme change)
    if len(sys.argv) > 2 and sys.argv[2] == "Settings":
        tabs.set("Settings")
        
# Setting up the Mirror Dungeon tab
scroll = ctk.CTkScrollableFrame(master=tab_md)
scroll.pack(fill="both", expand=True)

ctk.CTkLabel(scroll, text="Number of Runs:", font=ctk.CTkFont(size=16, weight="bold")).pack(pady=(10, 0))
entry = ctk.CTkEntry(scroll)
entry.pack(pady=(0, 5))
entry.insert(0, config['Settings'].get('mirror_runs', '1'))  # Set from config

start_button = ctk.CTkButton(scroll, text="Start", command=start_run)
start_button.pack(pady=(0, 15))

# Setting up the Exp tab
exp_scroll = ctk.CTkScrollableFrame(master=tab_exp)
exp_scroll.pack(fill="both", expand=True)

ctk.CTkLabel(exp_scroll, text="Number of Runs:", font=ctk.CTkFont(size=16, weight="bold")).pack(pady=(10, 0))
exp_entry = ctk.CTkEntry(exp_scroll)
exp_entry.pack(pady=(0, 5))
exp_entry.insert(0, config['Settings'].get('exp_runs', '1'))  # Set from config

ctk.CTkLabel(exp_scroll, text="Choose Stage:", font=ctk.CTkFont(size=16, weight="bold")).pack(pady=(10, 0))
exp_stage_var = ctk.StringVar(value=config['Settings'].get('exp_stage', '1'))  # Set from config
exp_stage_dropdown = ctk.CTkOptionMenu(
    master=exp_scroll,
    variable=exp_stage_var,
    values=["1", "2", "3", "4", "5", "6", "7"],
    width=200,
    font=ctk.CTkFont(size=16)
)
exp_stage_dropdown.pack(pady=(0, 15))

exp_start_button = ctk.CTkButton(exp_scroll, text="Start", command=start_exp_run)
exp_start_button.pack(pady=(0, 15))

# Setting up the Threads tab
threads_scroll = ctk.CTkScrollableFrame(master=tab_threads)
threads_scroll.pack(fill="both", expand=True)

ctk.CTkLabel(threads_scroll, text="Number of Runs:", font=ctk.CTkFont(size=16, weight="bold")).pack(pady=(10, 0))
threads_entry = ctk.CTkEntry(threads_scroll)
threads_entry.pack(pady=(0, 5))
threads_entry.insert(0, config['Settings'].get('threads_runs', '1'))  # Set from config

ctk.CTkLabel(threads_scroll, text="Choose Difficulty:", font=ctk.CTkFont(size=16, weight="bold")).pack(pady=(10, 0))
threads_difficulty_var = ctk.StringVar(value=config['Settings'].get('threads_difficulty', '20'))  # Set from config
threads_difficulty_dropdown = ctk.CTkOptionMenu(
    master=threads_scroll,
    variable=threads_difficulty_var,
    values=["20", "30", "40", "50"],
    width=200,
    font=ctk.CTkFont(size=16)
)
threads_difficulty_dropdown.pack(pady=(0, 15))

threads_start_button = ctk.CTkButton(threads_scroll, text="Start", command=start_threads_run)
threads_start_button.pack(pady=(0, 15))

# Setting up the Settings tab
settings_scroll = ctk.CTkScrollableFrame(master=tab_settings)
settings_scroll.pack(fill="both", expand=True)

# Reordered settings sections as requested: 1. Team, 2. Assign Sinners, 3. Keyboard Shortcuts, 4. Theme

# 1. Team selection section
ctk.CTkLabel(settings_scroll, text="Your Team", font=ctk.CTkFont(size=16, weight="bold")).pack(pady=(10, 0))
team_frame = ctk.CTkFrame(settings_scroll)
team_frame.pack(pady=(0, 15))

prechecked = load_initial_selections()

for name, row, col in TEAM_ORDER:
    var = ctk.BooleanVar(value=name in prechecked)
    chk = ctk.CTkCheckBox(
        master=team_frame,
        text=name.capitalize(),
        variable=var,
        command=lambda opt=name: on_checkbox_toggle(opt),
        font=ctk.CTkFont(size=16)
    )
    chk.grid(row=row, column=col, padx=5, pady=2, sticky="w")
    checkbox_vars[name] = var

# 2. Sinner assignment section
ctk.CTkLabel(settings_scroll, text="Assign Sinners to Name", font=ctk.CTkFont(size=16, weight="bold")).pack(anchor="center", pady=(0, 10))

container = ctk.CTkFrame(settings_scroll)
container.pack()

load_json()

for col_idx, group in enumerate(STATUS_COLUMNS):
    col = ctk.CTkFrame(container, fg_color="transparent")
    col.grid(row=0, column=col_idx, padx=15, sticky="n")

    for row_idx, status in enumerate(group):
        wrapper = ctk.CTkFrame(master=col, fg_color="transparent")
        wrapper.grid(row=row_idx, column=0, sticky="nw")

        arrow_var = ctk.StringVar(value="▶")
        full_text = ctk.StringVar(value=f"{arrow_var.get()} {status.capitalize()}")

        def make_toggle(stat=status, arrow=arrow_var):
            return lambda: toggle_expand(expand_frames[stat], arrow)

        btn = ctk.CTkButton(
            master=wrapper,
            textvariable=full_text,
            command=make_toggle(),
            width=200,
            height=38,
            font=ctk.CTkFont(size=18),
            anchor="w"
        )
        btn.pack(anchor="w", pady=(0, 6))

        arrow_var.trace_add("write", lambda *a, var=arrow_var, textvar=full_text, name=status: textvar.set(f"{var.get()} {name.capitalize()}"))

        frame = ctk.CTkFrame(master=wrapper, fg_color="transparent", corner_radius=0)
        expand_frames[status] = frame
        frame.pack_forget()

        dropdown_vars[status] = []
        default_order = squad_data.get(status, {})
        reverse_map = {v: k for k, v in default_order.items()}

        for i in range(12):
            row = ctk.CTkFrame(master=frame, fg_color="transparent")
            row.pack(pady=1, anchor="w")

            label = ctk.CTkLabel(
                master=row,
                text=f"{i+1}.",
                anchor="e",
                font=ctk.CTkFont(size=18),
                text_color="#b0b0b0",
                width=30
            )
            label.pack(side="left", padx=(0, 10))

            var = ctk.StringVar()
            raw_name = reverse_map.get(i + 1)
            pretty = next((x for x in SINNER_LIST if sinner_key(x) == raw_name), "None") if raw_name else "None"
            var.set(pretty)

            def bind_callback(status=status, idx=i, v=var):
                v.trace_add("write", lambda *a: dropdown_callback(status, idx))

            dropdown = ctk.CTkOptionMenu(
                master=row,
                variable=var,
                values=SINNER_LIST + ["None"],
                width=160,
                font=ctk.CTkFont(size=16)
            )
            dropdown.pack(side="left")
            bind_callback()
            dropdown_vars[status].append(var)

# 3. Keyboard shortcut configuration section
ctk.CTkLabel(settings_scroll, text="Keyboard Shortcuts", font=ctk.CTkFont(size=16, weight="bold")).pack(pady=(10, 0))
shortcuts_frame = ctk.CTkFrame(settings_scroll)
shortcuts_frame.pack(pady=(0, 15), fill="x", padx=20)

def update_shortcut(shortcut_type):
    """Update and apply a keyboard shortcut"""
    try:
        # Try to register the shortcuts to see if they're valid
        test_key = keyboard.add_hotkey(shortcut_vars[shortcut_type].get(), lambda: None)
        keyboard.remove_hotkey(test_key)
        
        # Save configuration
        save_gui_config()
        # Re-register all shortcuts
        register_keyboard_shortcuts()
        info(f"Updated {shortcut_type} shortcut to: {shortcut_vars[shortcut_type].get()}")
        
    except Exception as e:
        error(f"Invalid shortcut format: {e}")
        # Reset to previous value
        shortcut_vars[shortcut_type].set(config['Shortcuts'].get(shortcut_type))
        messagebox.showerror("Invalid Shortcut", f"Invalid shortcut format: {shortcut_vars[shortcut_type].get()}\n\nValid examples: ctrl+q, alt+s, shift+x")

# Mirror Dungeon shortcut
shortcut_row = ctk.CTkFrame(shortcuts_frame)
shortcut_row.pack(fill="x", pady=5)
ctk.CTkLabel(shortcut_row, text="Mirror Dungeon:", width=120, anchor="e").pack(side="left", padx=(10, 10))
md_shortcut_entry = ctk.CTkEntry(shortcut_row, textvariable=shortcut_vars['mirror_dungeon'], width=100)
md_shortcut_entry.pack(side="left", padx=(0, 10))
ctk.CTkButton(shortcut_row, text="Apply", width=60, 
              command=lambda: update_shortcut('mirror_dungeon')).pack(side="left")

# Exp shortcut
shortcut_row = ctk.CTkFrame(shortcuts_frame)
shortcut_row.pack(fill="x", pady=5)
ctk.CTkLabel(shortcut_row, text="Exp:", width=120, anchor="e").pack(side="left", padx=(10, 10))
exp_shortcut_entry = ctk.CTkEntry(shortcut_row, textvariable=shortcut_vars['exp'], width=100)
exp_shortcut_entry.pack(side="left", padx=(0, 10))
ctk.CTkButton(shortcut_row, text="Apply", width=60, 
              command=lambda: update_shortcut('exp')).pack(side="left")

# Threads shortcut
shortcut_row = ctk.CTkFrame(shortcuts_frame)
shortcut_row.pack(fill="x", pady=5)
ctk.CTkLabel(shortcut_row, text="Threads:", width=120, anchor="e").pack(side="left", padx=(10, 10))
threads_shortcut_entry = ctk.CTkEntry(shortcut_row, textvariable=shortcut_vars['threads'], width=100)
threads_shortcut_entry.pack(side="left", padx=(0, 10))
ctk.CTkButton(shortcut_row, text="Apply", width=60, 
              command=lambda: update_shortcut('threads')).pack(side="left")

# Help text for keyboard shortcuts
shortcut_help = ctk.CTkLabel(shortcuts_frame, text="Format examples: ctrl+q, alt+s, shift+x", 
                            font=ctk.CTkFont(size=12), text_color="gray")
shortcut_help.pack(pady=(5, 10))

# 4. Theme selection section
ctk.CTkLabel(settings_scroll, text="Theme", font=ctk.CTkFont(size=16, weight="bold")).pack(pady=(10, 0))
theme_dropdown = ctk.CTkOptionMenu(
    master=settings_scroll,
    variable=theme_var,
    values=list(THEMES.keys()),
    width=200,
    font=ctk.CTkFont(size=16),
    command=lambda _: apply_theme()
)
theme_dropdown.pack(pady=(0, 15))

# Setting up the Help tab
help_scroll = ctk.CTkScrollableFrame(master=tab_help)
help_scroll.pack(fill="both", expand=True)

# Add a text widget for help
help_text = ctk.CTkTextbox(help_scroll, height=700, width=920, font=ctk.CTkFont(size=12))
help_text.pack(fill="both", expand=True)

# Load help text
try:
    if os.path.exists(HELP_TEXT_PATH):
        with open(HELP_TEXT_PATH, 'r') as f:
            help_content = f.read()
        help_text.insert("1.0", help_content)
    else:
        help_text.insert("1.0", "Help.txt file not found. Please create this file with usage instructions.")
    
    help_text.configure(state="disabled")  # Make it read-only
except Exception as e:
    error(f"Error loading help text: {e}")
    help_text.insert("1.0", f"Error loading Help.txt: {e}")
    help_text.configure(state="disabled")

# Setting up the Logs tab
logs_frame = ctk.CTkFrame(tab_logs)
logs_frame.pack(fill="both", expand=True, padx=10, pady=10)

# Create a text widget for displaying logs
log_text = ctk.CTkTextbox(logs_frame, height=700, width=920, font=ctk.CTkFont(size=12))
log_text.pack(fill="both", expand=True)
log_text.configure(state="disabled")  # Make it read-only

# Create filter control panel for log visibility
filter_frame = ctk.CTkFrame(logs_frame)
filter_frame.pack(fill="x", pady=(0, 10))

def apply_filter():
    """Re-load log file with current filters and save filter settings"""
    load_log_file()
    save_gui_config()

# Create filters in a single section
filter_section = ctk.CTkFrame(filter_frame)
filter_section.pack(fill="x", pady=5, padx=5)

# Create sections for log levels and modules
left_panel = ctk.CTkFrame(filter_section)
left_panel.pack(side="left", fill="y", padx=10)

right_panel = ctk.CTkFrame(filter_section)
right_panel.pack(side="left", fill="y", padx=10)

# Add filter toggle for noise reduction
ctk.CTkLabel(filter_section, text="Clean Logs:", font=ctk.CTkFont(size=14, weight="bold")).pack(side="left", padx=20)
filter_toggle = ctk.CTkSwitch(
    master=filter_section,
    text="",
    variable=ctk.BooleanVar(value=filtered_messages_enabled),
    command=lambda: toggle_filtered_messages(),
    onvalue=True,
    offvalue=False
)
filter_toggle.pack(side="left", padx=5)

def toggle_filtered_messages():
    """Toggle filtering of noisy messages"""
    global filtered_messages_enabled
    filtered_messages_enabled = filter_toggle.get()
    save_gui_config()
    load_log_file()  # Reload logs with new filter setting

# Add log level filters
ctk.CTkLabel(left_panel, text="Show log levels:", font=ctk.CTkFont(size=14, weight="bold")).pack(anchor="w", padx=5, pady=5)

level_filter_frame = ctk.CTkFrame(left_panel)
level_filter_frame.pack(fill="x", padx=5)

# Create checkboxes for each log level in one row
for level in log_filters:
    chk = ctk.CTkCheckBox(
        master=level_filter_frame,
        text=level,
        variable=log_filters[level],
        command=apply_filter,
        font=ctk.CTkFont(size=12)
    )
    chk.pack(anchor="w", padx=5, pady=2)

# Add module filters
ctk.CTkLabel(right_panel, text="Show modules:", font=ctk.CTkFont(size=14, weight="bold")).pack(anchor="w", padx=5, pady=5)

# Create a grid layout for module checkboxes
module_filter_frame = ctk.CTkFrame(right_panel)
module_filter_frame.pack(fill="x", padx=5)

# Calculate number of modules per column (3 columns)
modules_per_column = len(LOG_MODULES) // 3 + (1 if len(LOG_MODULES) % 3 > 0 else 0)

# Organize module checkboxes in three columns
for i, module in enumerate(LOG_MODULES):
    col = i // modules_per_column
    row = i % modules_per_column
    
    chk = ctk.CTkCheckBox(
        master=module_filter_frame,
        text=module,
        variable=module_filters[module],
        command=apply_filter,
        font=ctk.CTkFont(size=12)
    )
    chk.grid(row=row, column=col, sticky="w", padx=5, pady=2)

# Create and add the custom handler with filters
text_handler = TextWidgetHandler(log_text, log_filters, module_filters)

# Add the handler to the ROOT logger to capture logs from all scripts
root_logger = logging.getLogger()
root_logger.addHandler(text_handler)

# Create log file monitor
log_monitor = LogFileMonitor(LOG_FILENAME, log_text, log_filters, module_filters)

# Create log control button panel
logs_button_frame = ctk.CTkFrame(logs_frame)
logs_button_frame.pack(fill="x", pady=(10, 0))

def clear_gui_logs():
    """Clear only the log display in the GUI"""
    log_text.configure(state="normal")
    log_text.delete("1.0", "end")
    log_text.configure(state="disabled")
    info("GUI log display cleared")

# GUI log clearing button
clear_gui_logs_btn = ctk.CTkButton(logs_button_frame, text="Clear GUI Logs", command=clear_gui_logs)
clear_gui_logs_btn.pack(side="left", padx=5)

def clear_log_file():
    """Clear the content of the log file on disk"""
    try:
        # Close and reopen the log file in write mode to truncate it
        for handler in logger.handlers:
            if isinstance(handler, logging.FileHandler):
                handler.close()
                
        # Truncate the file
        with open(LOG_FILENAME, 'w') as f:
            f.write("")
            
        # Reinitialize the file handler
        for handler in logger.handlers:
            if isinstance(handler, logging.FileHandler):
                handler.stream = open(handler.baseFilename, handler.mode)
                
        # Reset the log monitor position
        log_monitor.last_position = 0
                
        info("Log file cleared")
        
        # Refresh the display
        load_log_file()
    except Exception as e:
        error(f"Error clearing log file: {e}")
        messagebox.showerror("Error", f"Failed to clear log file: {e}")

# Log file clearing button
clear_log_file_btn = ctk.CTkButton(logs_button_frame, text="Clear Log File", command=clear_log_file)
clear_log_file_btn.pack(side="left", padx=5)

def load_log_file():
    """Load existing log file into the display with filters applied"""
    try:
        # Reset the file monitor's position to 0 to force a full reload
        log_monitor.last_position = 0
        
        with open(LOG_FILENAME, 'r') as f:
            log_lines = f.readlines()
        
        # Clear current display
        log_text.configure(state="normal")
        log_text.delete("1.0", "end")
        
        # Apply filters and add matching lines
        for line in log_lines:
            # Process the line with the same filtering logic as the monitor
            log_monitor._process_log_line(line)
        
        # Update the monitor's position to the end of the file
        log_monitor.last_position = os.path.getsize(LOG_FILENAME)
        
        log_text.see("end")  # Scroll to the end
        log_text.configure(state="disabled")
        info("Loaded existing log file with filters applied")
    except Exception as e:
        error(f"Error loading log file: {e}")

# Log file loading button
load_logs_btn = ctk.CTkButton(logs_button_frame, text="Load Log File", command=load_log_file)
load_logs_btn.pack(side="left", padx=5)

# Register keyboard shortcuts based on config values
register_keyboard_shortcuts()

# Process monitoring function
def check_processes():
    """Check if processes are still running and update UI accordingly"""
    global process, exp_process, threads_process
    
    # Check Mirror Dungeon process
    if process is not None:
        if process.poll() is not None:
            # Process has ended
            info(f"Mirror Dungeon process ended with code: {process.returncode}")
            process = None
            start_button.configure(text="Start")
    
    # Check Exp process
    if exp_process is not None:
        if exp_process.poll() is not None:
            # Process has ended
            info(f"Exp process ended with code: {exp_process.returncode}")
            exp_process = None
            exp_start_button.configure(text="Start")
    
    # Check Threads process
    if threads_process is not None:
        if threads_process.poll() is not None:
            # Process has ended
            info(f"Threads process ended with code: {threads_process.returncode}")
            threads_process = None
            threads_start_button.configure(text="Start")
    
    # Schedule next check
    root.after(1000, check_processes)

# Application exit handling
def on_closing():
    """Handle application exit cleanup"""
    info("Application closing")
    
    # Save current configuration with window size
    save_gui_config()
    
    # Clean up text handler
    text_handler.close()
    
    # Stop log file monitoring
    log_monitor.stop_monitoring()
    
    # Kill any running processes
    if process:
        kill_bot()
    if exp_process:
        kill_exp_bot()
    if threads_process:
        kill_threads_bot()
        
    root.destroy()

# Set the callback for window close
root.protocol("WM_DELETE_WINDOW", on_closing)

# Start the application
if __name__ == "__main__":
    # Use deferred tasks to improve startup time
    def start_application():
        # Load logs after UI is visible
        load_log_file()
        
        # Start log file monitoring
        log_monitor.start_monitoring(root)
        
        # Start process monitoring
        check_processes()
    
    # Schedule startup tasks with a small delay
    root.after(10, start_application)
    
    root.mainloop()