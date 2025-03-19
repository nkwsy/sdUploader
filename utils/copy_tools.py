
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


class DatetimeHandler(jsonpickle.handlers.BaseHandler):
    def flatten(self, obj, data):
        return obj.isoformat()


class FileManifest:
    def __init__(self, file_count, file_total_size, modification_range, file_list):
        self.file_count = file_count
        self.file_total_size = file_total_size
        self.modification_range = modification_range
        self.file_list = file_list

    def __repr__(self):
        return f"FileManifest(file_count={self.file_count}, file_total_size={self.file_total_size}, modification_range={self.modification_range}, file_list={len(self.file_list)} total files)"
    def __str__(self):
        return f"FileManifest(file_count={self.file_count}, file_total_size={self.file_total_size}, modification_range={self.modification_range}, file_list={len(self.file_list)} total files)"
    def to_json(self, indent=None):
        return jsonpickle.encode(self, unpicklable=False, indent=indent)


class FileInfo:
    def __init__(self, filename, size, mtime, md5_hash):
        self.filename = str(filename)  # to make pickling easier
        self.size = size
        self.mtime = mtime
        self.md5_hash = md5_hash
    def __repr__(self):
        return f"FileInfo(filename={self.filename}, size={self.size}, mtime={self.mtime}, md5_hash={self.md5_hash})"


def file_md5(file):
    chunk_size = 1024 * 1024
    md5 = hashlib.md5()
    try:
        with open(file, 'rb') as f:
            for chunk in iter(lambda: f.read(chunk_size), b''):
                md5.update(chunk)
        return md5.hexdigest()
    except Exception as e:
        msg = f"Error calculating MD5 hash of file {file}: {str(e)}"
        logging.error(msg)
        raise Exception(msg) from e


def copy_tree(source, destination, verify_destination_md5=True, total_size=None, total_files=None, progress_callback=None):
    all_subdirs = []
    manifest = []
    current_size = 0
    current_files = 0
    for root, dirs, files in source.walk():
        # Make the directory hierarchy
        for dir in dirs:
            relative_path = (root / dir).relative_to(source)
            all_subdirs.append((root, relative_path))
            logging.debug(f"processing dir: {relative_path}")
            if dir in [".Trashes", ".Spotlight-V100",".fseventsd"]:
                continue
            elif not (destination / relative_path).exists():
                logging.debug(f"creating directory: {(destination / relative_path)}")
                try:
                    (destination / relative_path).mkdir(parents=True, exist_ok=True)
                except Exception as e:
                    msg = f"Could not create directory: {(destination / relative_path)}"
                    logging.error(msg)
                    raise Exception(msg) from e
        # Copy all the files
        for file in files:
            relative_path = (root / file).relative_to(source)
            logging.debug(f"processing file: {relative_path}")
            logging.debug(f"copying file: {root / file} to {destination / relative_path}")
            try:
                stat = (root / file).stat()
                md5_hash = file_md5(root / file)
                shutil.copy2(root / file, destination / relative_path)
                file_info = FileInfo(relative_path, stat.st_size, stat.st_mtime, md5_hash)
                manifest.append(file_info)
                logging.debug(f"copied file: {file_info}")
                if verify_destination_md5:
                    logging.debug(f"verifying md5 hash of {destination / relative_path}")
                    if md5_hash != file_md5(destination / relative_path):
                        logging.error(f"MD5 hash of {destination / relative_path} does not match source file")
                        raise Exception(f"MD5 hash of {destination / relative_path} does not match source file")
                    else:
                        logging.debug(f"MD5 hash of {destination / relative_path} matches source file")
            except Exception as e:
                msg = f"Could not copy file: {root / file}: {str(e)}"
                logging.error(msg)
                raise Exception(msg) from e
            current_size += (root / file).stat().st_size
            current_files += 1
            if progress_callback is not None:
                progress_callback(current_size, current_files, total_size, total_files)
    # Stat all the directories so their modification times and permissions and such are correct
    for root, relative_path in reversed(all_subdirs):
        if relative_path.name in [".Trashes", ".Spotlight-V100",".fseventsd"]:
            continue
        else:
            logging.debug(f"copying stats: {source / relative_path} to {(destination / relative_path)}")
            try:
                shutil.copystat(source / relative_path, destination / relative_path)
            except Exception as e:
                msg = f"Could not copy directory stats: {source / relative_path}: {str(e)}"
                logging.error(msg)
                raise Exception(msg) from e
    return manifest


def create_temp_folder(path):
    today = datetime.now()
    folder_name = f"{today.strftime('%Y-%m-%d_%H-%M-%S')}".strip()
    temp_path = path / folder_name
    try:
        temp_path.mkdir(parents=True, exist_ok=True)
    except Exception as e:
        logging.error(f"Error creating temp folder: {temp_path}: {str(e)}")
        raise
    return temp_path


class CopyProgress:
    def __init__(self, current_size, current_files, total_size, total_files, percent):
        self.current_size = current_size
        self.current_files = current_files
        self.total_size = total_size
        self.total_files = total_files
        self.percent = percent

class CopyThread(Thread):
    def __init__(self, source_path, destination_path, total_size, total_files):
        super().__init__()
        self.current_size = 0
        self.current_files = 0
        self.total_size = total_size
        self.total_files = total_files
        self.source_path = source_path
        self.destination_path = destination_path
        self.manifest_file_list = None
        self.error_message = None

    def get_progress(self):
        current_progress = self.current_size / self.total_size
        logging.debug(f"Current copy progress: {current_progress}")
        progress = CopyProgress(self.current_size, self.current_files, self.total_size, self.total_files, current_progress)
        return progress

    def progress_callback(self, current_size, current_files, total_size, total_files):
        self.current_size = current_size
        self.current_files = current_files

    def run(self):
        logging.debug("Starting copy thread")
        try:
            self.manifest_file_list = copy_tree(self.source_path, self.destination_path, total_size=self.total_size, total_files=self.total_files, progress_callback=self.progress_callback)
        except Exception as e:
            msg = f"Error copying files: {str(e)}"
            logging.error(msg)
            self.error_message = msg




def threaded_download_card(sdcard_path, temp_location):

    logging.debug("Starting hashing")


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
    manifest = FileManifest(
        sd_card.file_count,
        sd_card.file_total_size,
        sd_card.modification_date_range,
        manifest_file_list)
    #print(manifest)
    print(manifest.to_json(indent=2))

