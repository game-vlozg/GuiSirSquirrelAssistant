import sys
import logging
import os
import threading

logger = logging.getLogger(__name__)
try:
    # Log all environment and path information
    logger.debug(f"Python executable: {sys.executable}")
    logger.debug(f"Working directory: {os.getcwd()}")
    logger.debug(f"Script path: {__file__}")
    logger.debug(f"System path: {sys.path}")
    
    # Determine if running as executable or script
    def get_base_path():
        if getattr(sys, 'frozen', False):
            # Running as compiled exe
            base_path = os.path.dirname(sys.executable)
            logger.debug(f"Running as frozen executable, base path: {base_path}")
            return base_path
        else:
            # Running as script - go up one level to reach the "all data" directory
            base_path = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
            logger.debug(f"Running as script, base path: {base_path}")
            return base_path

    # Set up paths using base path
    BASE_PATH = get_base_path()
    logger.debug(f"Final BASE_PATH: {BASE_PATH}")
    
    # Add necessary paths
    src_path = os.path.join(BASE_PATH, 'src')
    logger.debug(f"Adding src path: {src_path}")
    sys.path.append(src_path)
    sys.path.append(BASE_PATH)
    
    # Log the paths for config files
    config_path = os.path.join(BASE_PATH, "config")
    status_path = os.path.join(config_path, "status_selection.txt")
    logger.debug(f"Config path: {config_path}")
    logger.debug(f"Status selection path: {status_path}")
    
    # Verify file exists before importing modules
    if not os.path.exists(status_path):
        logger.critical(f"Status selection file not found at: {status_path}")
        raise FileNotFoundError(f"Status selection file not found: {status_path}")
        
    # Now import modules after path setup
    logger.debug(f"Importing modules...")
    
    try:
        from core import pre_md_setup, reconnect
        logger.debug(f"Successfully imported from core")
    except ImportError as e:
        logger.critical(f"Failed to import from core: {e}")
        raise
        
    try:
        from common import error_screenshot, element_exist
        logger.debug(f"Successfully imported from common")
    except ImportError as e:
        logger.critical(f"Failed to import from common: {e}")
        raise
        
    try:
        import mirror
        logger.debug(f"Successfully imported mirror")
    except ImportError as e:
        logger.critical(f"Failed to import mirror: {e}")
        raise

    connection_event = threading.Event()

    # Correctly resolve status selection file path
    try:
        logger.debug(f"Opening status selection file: {status_path}")
        with open(status_path, "r") as f:
            status_list_file = [i.strip().lower() for i in f.readlines()]
        logger.debug(f"Status list loaded: {status_list_file}")
    except Exception as e:
        logger.critical(f"Error reading status selection file: {e}")
        raise

    def connection_check():
        while True:
            try:
                if element_exist("pictures/general/connection.png"):
                    connection_event.clear()
                    logger.debug(f"Connection check: connection issue found")
                else:
                    connection_event.set()
                    logger.debug(f"Connection check: connection OK")
            except Exception as e:
                logger.error(f"Error in connection check: {e}")

    def connection_listener():
        try:
            logger.debug(f"Connection listener started")
            reconnect()
            logger.debug(f"Connection listener completed")
        except Exception as e:
            logger.error(f"Error in connection listener: {e}")

    def mirror_dungeon_run(num_runs):
        try:
            run_count = 0
            win_count = 0
            lose_count = 0
            
            # Ensure we have status selections
            if not status_list_file:
                logger.critical(f"Status list file is empty, cannot proceed")
                return
                
            # Create status list for runs
            status_list = (status_list_file * ((num_runs // len(status_list_file)) + 1))[:num_runs]
            logger.info(f"Starting Run with statuses: {status_list}")
            
            for i in range(num_runs):
                logger.info(f"Run {run_count + 1}")
                try:
                    pre_md_setup()
                    logger.info(f"Current Team: " + status_list[i])
                    run_complete = 0
                    
                    # Create Mirror instance
                    logger.debug(f"Creating Mirror instance with status: {status_list[i]}")
                    MD = mirror.Mirror(status_list[i])
                    
                    # Set up mirror
                    logger.debug(f"Setting up mirror")
                    MD.setup_mirror()
                    
                    # Main loop for this run
                    while run_complete != 1:
                        if connection_event.is_set():
                            logger.debug(f"Connection is set, running mirror loop")
                            win_flag, run_complete = MD.mirror_loop()
                            logger.debug(f"Mirror loop returned: win_flag={win_flag}, run_complete={run_complete}")
                        
                        if element_exist("pictures/general/server_error.png"):
                            logger.warning(f"Server error detected")
                            connection_event.clear()
                            logger.debug(f"Disconnected, Pausing")
                            connection_listener_thread = threading.Thread(target=connection_listener)
                            connection_listener_thread.start()
                            connection_listener_thread.join()
                            logger.debug(f"Reconnected, Resuming")
                            connection_event.set()

                    # Update counters
                    if win_flag == 1:
                        win_count += 1
                        logger.info(f"Run {run_count + 1} completed with a win")
                    else:
                        lose_count += 1
                        logger.info(f"Run {run_count + 1} completed with a loss")
                    run_count += 1
                    
                except Exception as e:
                    logger.exception(f"Error in run {run_count + 1}: {e}")
                    error_screenshot()
                    # Continue with next run instead of breaking out
                    run_count += 1
                
            logger.info(f'Completed all runs. Won: {win_count}, Lost: {lose_count}')
        except Exception as e:
            logger.exception(f"Critical error in mirror_dungeon_run: {e}")
            error_screenshot()

    if __name__ == "__main__":
        logger.info(f"compiled_runner.py main execution started")
        
        try:
            # Setting up basic logging configuration
            LOG_FILENAME = os.path.join(BASE_PATH, "Pro_Peepol's.log")
            logging.basicConfig(
                level=logging.DEBUG,
                format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                handlers=[
                    logging.FileHandler(LOG_FILENAME)
                ]
            )
            
            # Set connection event
            logger.debug(f"Setting connection event")
            connection_event.set()
            
            # Start connection check thread
            logger.debug(f"Starting connection check thread")
            connection_thread = threading.Thread(target=connection_check, daemon=True)
            connection_thread.start()
            
            # Get run count from command line
            if len(sys.argv) > 1:
                try:
                    count = int(sys.argv[1])
                    logger.info(f"Run count from arguments: {count}")
                except ValueError:
                    count = 1
                    logger.warning(f"Invalid run count argument: {sys.argv[1]}, using default 1")
            else:
                count = 1
                logger.info(f"No run count specified, using default 1")
            
            # Start mirror dungeon
            logger.info(f"Starting mirror_dungeon_run with {count} runs")
            mirror_dungeon_run(count)
            logger.info(f"mirror_dungeon_run completed")
            
        except Exception as e:
            logger.critical(f"Unhandled exception in compiled_runner main: {e}")
            error_screenshot()
            sys.exit(1)  # Exit with error code
        
        # Successful completion
        logger.info(f"compiled_runner.py completed successfully")
        
except Exception as e:
    # Catch any errors that happen during module setup
    if 'logger' in locals():
        logger.critical(f"Fatal error during setup: {e}")
    else:
        # Fallback if logger isn't set up yet
        print(f"FATAL ERROR: {e}")
    sys.exit(1)  # Exit with error code