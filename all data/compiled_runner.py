
import sys
import logging
import os
import threading

sys.path.append(os.path.abspath("src"))

from core import pre_md_setup, reconnect
from common import error_screenshot, element_exist
import mirror

connection_event = threading.Event()

status_path = os.path.join("config", "status_selection.txt")
with open(status_path, "r") as f:
    status_list_file = [i.strip().lower() for i in f.readlines()]

def connection_check():
    while True:
        if element_exist("pictures/general/connection.png"):
            connection_event.clear()
        else:
            connection_event.set()

def connection_listener():
    reconnect()

def mirror_dungeon_run(num_runs):
    try:
        run_count = 0
        win_count = 0
        lose_count = 0
        status_list = (status_list_file * ((num_runs // len(status_list_file)) + 1))[:num_runs]
        logging.info("Starting Run")
        for i in range(num_runs):
            logging.info(f"Run {run_count + 1}")
            pre_md_setup()
            logging.info("Current Team: " + status_list[i])
            run_complete = 0
            MD = mirror.Mirror(status_list[i])
            MD.setup_mirror()
            while run_complete != 1:
                if connection_event.is_set():
                    win_flag, run_complete = MD.mirror_loop()
                if element_exist("pictures/general/server_error.png"):
                    connection_event.clear()
                    logging.debug("Disconnected, Pausing")
                    connection_listener_thread = threading.Thread(target=connection_listener)
                    connection_listener_thread.start()
                    connection_listener_thread.join()
                    logging.debug("Reconnected, Resuming")
                    connection_event.set()

            if win_flag == 1:
                win_count += 1
            else:
                lose_count += 1
            run_count += 1
        logging.info(f'Won Runs {win_count}, Lost Runs {lose_count}')
    except Exception as e:
        error_screenshot()
        logging.exception(e)

if __name__ == "__main__":
    logging.basicConfig(
        level=logging.DEBUG,
        format="%(asctime)s - %(levelname)s - %(message)s",
        handlers=[logging.FileHandler("squirrel.log")]
    )
    connection_event.set()
    threading.Thread(target=connection_check, daemon=True).start()
    count = int(sys.argv[1]) if len(sys.argv) > 1 else 1
    mirror_dungeon_run(count)
