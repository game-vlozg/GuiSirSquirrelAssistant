import argparse
import logging
import os
import threading
import requests
import keyboard  # Import the keyboard module
from src import mirror
from src.core import pre_md_setup,reconnect
from src.common import error_screenshot, element_exist

connection_event = threading.Event()

with open("config/status_selection.txt", "r") as f:
    status = [i.strip().lower() for i in f.readlines()]
    
def update():
    r = requests.get("https://api.github.com/repos/Samsterr/SirSquirrelAssistant/releases/latest")
    tag = "1.0.5.1"
    r_tag = r.json()["tag_name"]
    if r_tag != tag:
        print("A New Version is Available! Downloading it to your current folder")
        r = requests.get("https://github.com/Samsterr/SirSquirrelAssistant/releases/download/" + r_tag + "/sirsquirrel.7z")
        with open("sirsquirrel.7z", "wb") as f:
            f.write(r.content)
        print("Download Completed. Please look for the 7z and update as per usual before continuing")

def exit_program():
    print("\nHotkey pressed. Exiting the program...")
    os._exit(0)

# Start a background thread to listen for 'Ctrl+Q'
def start_exit_listener():
    keyboard.add_hotkey('ctrl+q', exit_program)  # Register hotkey Ctrl+Q to exit
    # Keep the listener active without blocking the main thread
    while True:
        keyboard.wait('ctrl+q')  # Block until Ctrl+Q is pressed

def connection_listener():
    reconnect()

def connection_check():
    while True:
        while(element_exist("pictures/general/connection.png")):
            connection_event.clear()
        connection_event.set()

def mirror_dungeon_run(num_runs, logger):
    try:
        run_count = 0
        win_count = 0
        lose_count = 0
        status_list = (status * ((num_runs // len(status)) + 1))[:num_runs]
        logger.info("Starting Run")
        for i in range(num_runs):
            logger.info("Run {}".format(run_count + 1))
            pre_md_setup()
            logger.info("Current Team: "+status_list[i])
            run_complete = 0
            MD = mirror.Mirror(status_list[i])
            MD.setup_mirror()
            while(run_complete != 1):
                if connection_event.is_set():
                    win_flag, run_complete = MD.mirror_loop()
                if element_exist("pictures/general/server_error.png"):
                    connection_event.clear()
                    logger.debug("Disconnected, Pausing")
                    connection_listener_thread = threading.Thread(target=connection_listener)
                    connection_listener_thread.start()
                    connection_listener_thread.join()
                    logger.debug("Reconnected, Resuming")
                    connection_event.set()
            if win_flag == 1:
                win_count += 1
            else:
                lose_count += 1
            run_count += 1
        logger.info('Won Runs {}, Lost Runs {}'.format(win_count, lose_count))
    except Exception as e:
        error_screenshot()
        logger.exception(e)

def main():
    logging.basicConfig(
        level=logging.DEBUG,  # Set the logging level (e.g., DEBUG, INFO, WARNING)
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",  # Log format
        handlers=[
            logging.FileHandler("squirrel.log"),  # Output to a file
        ]
    )
    logger = logging.getLogger(__name__)
    parser = argparse.ArgumentParser()
    update()
    parser.add_argument("RunCount", help="How many times you want to run Mirror Dungeons", type=int)
    args = parser.parse_args()

    connection_event.set()
    exit_listener_thread = threading.Thread(target=start_exit_listener, daemon=True)
    exit_listener_thread.start()

    connection_thread = threading.Thread(target=connection_check)
    connection_thread.start()

    mirror_dungeon_run(args.RunCount, logger)

if __name__ == "__main__":
    main()
