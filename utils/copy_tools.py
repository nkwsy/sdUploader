
import logging
from pathlib import Path
import hashlib
import shutil
from sdcard_loader import ComboLoader
from sdcard import SDCardAnalyzer
import os
from dotenv import load_dotenv
from datetime import datetime
import jsonpickle

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
    with open(file, 'rb') as f:
        for chunk in iter(lambda: f.read(chunk_size), b''):
            md5.update(chunk)
    return md5.hexdigest()


def digest_tree(path, total_size=None, total_files=None, progress_callback=None):
    manifest = []
    current_size = 0
    current_files = 0
    for root, dirs, files in path.walk():
        for file in files:
            logging.debug(f"processing file: {root / file}")
            # Store the relative path of the file in the manifest
            relative_path = (root / file).relative_to(path)
            stat = (root / file).stat()
            try:

                md5_hash = file_md5(root / file)
            except Exception as e:
                logging.error(f"Error reading file: {root / file}: {str(e)}")
                raise
            file_info = FileInfo(relative_path, stat.st_size, stat.st_mtime, md5_hash)
            manifest.append(file_info)
            logging.debug(f"processed file: {file_info}")

            current_size += stat.st_size
            current_files += 1
            if progress_callback is not None:
                progress_callback(current_size, current_files, total_size, total_files)
    return manifest




def copy_tree(source, destination, total_size=None, total_files=None, progress_callback=None):
    all_subdirs = []
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
                    logging.error(f"Error creating directory: {(destination / relative_path)}: {str(e)}")
                    raise
        # Copy all the files
        for file in files:
            relative_path = (root / file).relative_to(source)
            logging.debug(f"processing file: {relative_path}")
            logging.debug(f"copying file: {root / file} to {destination / relative_path}")
            try:
                shutil.copy2(root / file, destination / relative_path)
            except Exception as e:
                logging.error(f"Error copying file: {root / file}: {str(e)}")
                raise
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
                logging.error(f"Error copying stats: {source / relative_path}: {str(e)}")
                raise


def progress_callback(current_size, current_files, total_size, total_files):
    pass
    #print(f"Processing {current_files} of {total_files} files, {current_size} of {total_size} bytes")

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


if __name__ == "__main__":
    load_dotenv()
    test_folder = os.getenv("TEST_FOLDER")
    LOG_LEVEL = os.getenv('LOG_LEVEL', 'INFO').upper()
    logging.basicConfig(level=LOG_LEVEL)
    sdcard_path = ComboLoader().find_sd_cards()[0]
    sd_card_analyzer = SDCardAnalyzer()
    sd_card = sd_card_analyzer.analyze_sd_card(sdcard_path.device, sdcard_path.mountpoint)
    copy_tree(sd_card.mount_point,
              create_temp_folder(Path(test_folder)),
              total_size=sd_card.file_total_size,
              total_files=sd_card.file_count,
              progress_callback=progress_callback)
    manifest = digest_tree(sd_card.mount_point,
                                  total_size=sd_card.file_total_size,
                                  total_files=sd_card.file_count,
                                  progress_callback=progress_callback)
    logging.debug(manifest)
    print(jsonpickle.encode(manifest, unpicklable=False))
