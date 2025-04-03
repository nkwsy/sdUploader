from loguru import logger
from pathlib import Path
from datetime import datetime
import psutil
from dotenv import load_dotenv
import os
import sys
import jsonpickle


class DatetimeHandler(jsonpickle.handlers.BaseHandler):
    def flatten(self, obj, data):
        return obj.isoformat()

class ModificationRange:
    def __init__(self, earliest_image, latest_image):
        self.earliest_image = earliest_image
        self.latest_image = latest_image
    def __repr__(self):
        return f"ModificationRange(earliest_image={self.earliest_image}, latest_image={self.latest_image})"

    def to_json(self, indent=None):
        return jsonpickle.encode(self, unpicklable=False, indent=indent)
    @staticmethod
    def from_json(json):
        return ModificationRange(datetime.fromisoformat(json["earliest_image"]), datetime.fromisoformat(json["latest_image"]))


class SDCard:
    def __init__(self, device, mountpoint, device_total_space, device_used_space, device_free_space, device_percent_free):
        self.device = device
        self.mountpoint = mountpoint
        self.device_total_space = device_total_space
        self.device_used_space = device_used_space
        self.device_free_space = device_free_space
        self.device_percent_free = device_percent_free
        self.file_total_size = None
        self.file_count = None
        self.camera_types = ""
        self.modification_date_range = None


    def __repr__(self):
        return f"SDCard(device={self.device}, mountpoint={self.mountpoint}, device_total_space={self.device_total_space}, device_used_space={self.device_used_space}, device_free_space={self.device_free_space}, device_percent_free={self.device_percent_free}, file_total_size={self.file_total_size}, file_count={self.file_count}, modification_date_range={self.modification_date_range})"
    def __str__(self):
        return f"SDCard(device={self.device}, mountpoint={self.mountpoint}, device_total_space={self.get_device_total_space_gb()} GB, device_used_space={self.get_device_used_space_gb()} GB, device_free_space={self.get_device_free_space_gb()} GB, device_percent_free={self.device_percent_free}, file_total_size={self.get_file_total_size_gb()} GB, file_count={self.file_count}, modification_date_range={self.modification_date_range})"

    def get_device_total_space_gb(self):
        return round(self.device_total_space / (1024.0 **3),2)

    def get_device_used_space_gb(self):
        return round(self.device_used_space / (1024.0 **3),2)

    def get_device_free_space_gb(self):
        return round(self.device_free_space / (1024.0 ** 3), 2)

    def get_file_total_size_gb(self):
        return round(self.file_total_size / (1024.0 ** 3), 2)

    def get_file_info(self):
        file_paths = find_files_in_sd_card(self.mountpoint)
        file_total_size = 0
        for file in file_paths:
            file_total_size += file.stat().st_size
        self.file_total_size = file_total_size
        self.file_count = len(file_paths)
        self.modification_date_range = get_modification_range(self.mountpoint)


    #def __str__(self):
    #    return f"SDCard(device={self.device}, mountpoint={self.mountpoint}, device_total_space={self.device_total_space} GB, device_used_space={self.device_used_space} GB, device_free_space={self.device_free_space} GB, device_percent_free={self.device_percent_free}%, file_total_size={self.file_total_size} GB, earliest_image={self.modification_date_range.earliest_image}, latest_image={self.modification_date_range.latest_image})"

class SDCardAnalyzer:
    def __init__(self):
        pass

    def analyze_sd_card(self, device, mountpoint):
        device_usage = psutil.disk_usage(mountpoint)
        device_total_space = device_usage.total
        device_used_space = device_usage.used
        device_free_space = device_usage.free
        device_percent_free = device_usage.percent

        return SDCard(device, mountpoint, device_total_space, device_used_space, device_free_space, device_percent_free)



def find_files_in_sd_card(path):
    '''Gets the absolute file paths of all files in the SD card'''
    file_paths = []
    for root, dirs, files in path.walk():
        for file in files:
            file_paths.append(root / file)
    return file_paths

def print_relative_files_in_sd_card(path):
    '''Prints the relative file paths of all files in the SD card'''
    for file in find_files_in_sd_card(path):
        print(file.relative_to(path))

def get_modification_range(path):
    """
    Return the most recent modification date found in the path directory or any of its sub-directories.
    """
    latest_time = path.stat().st_mtime  # Initialize with the current directory's modification time
    earliest_time = latest_time
    for root, _, files in path.walk():
        for file in files:
            file_path = root / file
            if file_path.stat().st_mtime > latest_time:
                latest_time = file_path.stat().st_mtime
            if file_path.stat().st_mtime < earliest_time:
                earliest_time = file_path.stat().st_mtime
    latest_datetime = datetime.fromtimestamp(latest_time)
    earliest_datetime = datetime.fromtimestamp(earliest_time)
    return ModificationRange(earliest_datetime, latest_datetime)






if __name__ == "__main__":
    load_dotenv()
    test_mountpoint = Path(os.getenv("TEST_MOUNTPOINT"))
    test_device = os.getenv("TEST_DEVICE")
    logger.configure(handlers=[{"sink": sys.stdout, "level": "DEBUG"}])
    print_relative_files_in_sd_card(test_mountpoint)
    print(f"modification range: {get_modification_range(test_mountpoint)}")
    sd_card_analyzer = SDCardAnalyzer()
    sd_card = sd_card_analyzer.analyze_sd_card(test_device, test_mountpoint)
    sd_card.get_file_info()
    print(sd_card)





