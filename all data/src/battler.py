import sys
import logging
import os
import core

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
# Use a specific logger name instead of __name__ which becomes "__main__"
logger = logging.getLogger("battler")

def main():
    """Run the battle function and exit immediately"""
    try:
        logger.info("Starting battler.py - Running battle function")
        
        try:
            # Call the battle function
            logger.info("Calling core.battle()")
            core.battle()
            
            logger.info("Battle function completed")
            
        except AttributeError:
            logger.error("Function 'battle' not found in module 'core'")
        except Exception as e:
            logger.error(f"Error running battle function: {e}")
            
    except Exception as e:
        logger.error(f"Unexpected error in battler.py: {e}")
    finally:
        logger.info("battler.py shutting down")
        sys.exit(0)

if __name__ == "__main__":
    main()