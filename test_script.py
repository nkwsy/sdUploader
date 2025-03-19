import logging
from pathlib import Path
import hashlib
import shutil
from utils.sdcard_loader import ComboLoader
from utils.sdcard import SDCardAnalyzer, ModificationRange
import os
from dotenv import load_dotenv
from datetime import datetime
import jsonpickle
import tkinter as tk
from threading import Thread
import time

from utils.copy_tools import CopyThread, FileManifest, create_temp_folder, CopyProgress

if __name__ == "__main__":
    load_dotenv()
    test_folder = os.getenv("TEST_FOLDER")
    LOG_LEVEL = os.getenv('LOG_LEVEL', 'INFO').upper()
    logging.basicConfig(level=LOG_LEVEL)
    sd_card = ComboLoader().find_sd_cards()[0]
    sd_card.get_file_info()

    #print(jsonpickle.encode(manifest, unpicklable=False))
    copy_thread = CopyThread(
        sd_card.mountpoint,
        create_temp_folder(Path(test_folder)),
        sd_card.file_total_size,
        sd_card.file_count)
    copy_thread.start()
    while copy_thread.is_alive():
        time.sleep(0.1)
        logging.info(f"Copy {copy_thread.current_files} of {copy_thread.total_files} files, {copy_thread.current_size} of {copy_thread.total_size} bytes")
    copy_thread.join()
    if copy_thread.error_message is not None:
        logging.error(copy_thread.error_message)
    else:
        logging.info("Copy complete")

    manifest_file_list = copy_thread.manifest_file_list
    manifest = FileManifest(sd_card.file_count, sd_card.file_total_size, sd_card.modification_date_range, manifest_file_list)
    #print(manifest)
    print(manifest.to_json(indent=2))