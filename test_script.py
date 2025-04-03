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

from utils.copy_tools import CopyThread, FileManifest, CopyProgress, CameraInfo, DeleteThread
from utils.card_metadata import create_upload_folder, write_info_file, write_camera_info_file, \
    write_uploaded_marker_file, create_download_folder, find_download_metadata
from upload_manager import UploadThread


def upload_files(download_folder, camera_info, file_manifest):
    logging.debug(f"Preparing for upload for camera: {camera_info.cameraid}")
    upload_folder = create_upload_folder(camera_info.date,
                                         camera_info.camera,
                                         camera_info.location,
                                         camera_info.cameraid)

    upload_thread = CopyThread(
        download_folder,
        upload_folder,
        file_manifest.file_total_size,
        file_manifest.file_count)
    upload_thread.start()
    while upload_thread.is_alive():
        time.sleep(0.1)
        logging.info(f"Uploading {upload_thread.current_files} of {upload_thread.total_files} files, {upload_thread.current_size} of {upload_thread.total_size} bytes")
    upload_thread.join()
    if copy_thread.error_message is not None:
        logging.error(copy_thread.error_message)
    else:
        logging.info("Upload complete")

    write_info_file(upload_folder, camera_info, file_manifest)
    write_camera_info_file(upload_folder, camera_info)
    write_uploaded_marker_file(download_folder, upload_folder)



if __name__ == "__main__":
    load_dotenv()
    test_folder = os.getenv("TEST_FOLDER")
    LOG_LEVEL = os.getenv('LOG_LEVEL', 'INFO').upper()
    logging.basicConfig(level=LOG_LEVEL)
    sd_card = ComboLoader().find_sd_cards()[0]
    sd_card.get_file_info()

    camera_info = CameraInfo(camera="TestCam",
                             date=datetime.now(),
                             location="Here",
                             notes="No Notes",
                             cameraid="UR101",
                             photographer="Tom Baker")

    download_folder = create_download_folder()
    #print(jsonpickle.encode(manifest, unpicklable=False))
    copy_thread = CopyThread(
        sd_card.mountpoint,
        download_folder,
        camera_info=camera_info,
        total_size=sd_card.file_total_size,
        total_files=sd_card.file_count,
        modification_range=sd_card.modification_date_range)
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
    manifest = FileManifest(camera_info,
                            sd_card.file_count,
                            sd_card.file_total_size,
                            sd_card.modification_date_range,
                            manifest_file_list)
    #print(manifest)
    print(manifest.to_json(indent=2))


    #upload_files(download_folder, camera_info, manifest)

    upload_folder = create_upload_folder(camera_info.date,
                                         camera_info.camera,
                                         camera_info.location,
                                         camera_info.cameraid)
    upload_thread = UploadThread(download_folder,
                                 upload_folder,
                                 camera_info,
                                 manifest)

    upload_thread.start()
    while upload_thread.is_alive():
        time.sleep(0.1)
        logging.info(f"Uploading {upload_thread.current_files} of {upload_thread.total_files} files, {upload_thread.current_size} of {upload_thread.total_size} bytes")
    upload_thread.join()
    if upload_thread.error_message is not None:
        logging.error(upload_thread.error_message)
    else:
        logging.info("Upload complete")


    download_manifest_files = find_download_metadata()
    print(download_manifest_files)

    delete_thread = DeleteThread(download_folder, total_files=manifest.file_count)
    delete_thread.start()
    os.mkdir(download_folder / ".Trashes")
    while delete_thread.is_alive():
        time.sleep(0.1)
        logging.info(f"Deleting {delete_thread.current_files} of {delete_thread.total_files} files")
    delete_thread.join()
    if delete_thread.has_system_files:
        logging.info("Output folder has .Trashes folder!")
    if delete_thread.error_message is not None:
        logging.error(delete_thread.error_message)
    else:
        logging.info("Delete complete")

