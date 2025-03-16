import logging
from pathlib import Path
from sdcard_loader import ComboLoader
from datetime import datetime
import psutil

class ModificationRange:
    def __init__(self, earliest_image, latest_image):
        self.earliest_image = earliest_image
        self.latest_image = latest_image
    def __repr__(self):
        return f"ModificationRange(earliest_image={self.earliest_image}, latest_image={self.latest_image})"

class SDCard:
    def __init__(self, device, mount_point, device_total_space, device_used_space, device_free_space, device_percent_free, file_total_size, file_count, modification_date_range):
        self.device = device
        self.mount_point = mount_point
        self.device_total_space = device_total_space
        self.device_used_space = device_used_space
        self.device_free_space = device_free_space
        self.device_percent_free = device_percent_free
        self.file_total_size = file_total_size
        self.file_count = file_count
        self.modification_date_range = modification_date_range
    def __repr__(self):
        return f"SDCard(device={self.device}, mount_point={self.mount_point}, device_total_space={self.device_total_space}, device_used_space={self.device_used_space}, device_free_space={self.device_free_space}, device_percent_free={self.device_percent_free}, file_total_size={self.file_total_size}, file_count={self.file_count}, modification_date_range={self.modification_date_range})"
    def __str__(self):
        return f"SDCard(device={self.device}, mount_point={self.mount_point}, device_total_space={self.get_device_total_space_gb()} GB, device_used_space={self.get_device_used_space_gb()} GB, device_free_space={self.get_device_free_space_gb()} GB, device_percent_free={self.device_percent_free}, file_total_size={self.get_file_total_size_gb()} GB, file_count={self.file_count}, modification_date_range={self.modification_date_range})"

    def get_device_total_space_gb(self):
        return round(self.device_total_space / (1024.0 **3),2)

    def get_device_used_space_gb(self):
        return round(self.device_used_space / (1024.0 **3),2)

    def get_device_free_space_gb(self):
        return round(self.device_free_space / (1024.0 ** 3), 2)

    def get_file_total_size_gb(self):
        return round(self.file_total_size / (1024.0 ** 3), 2)

    #def __str__(self):
    #    return f"SDCard(device={self.device}, mount_point={self.mount_point}, device_total_space={self.device_total_space} GB, device_used_space={self.device_used_space} GB, device_free_space={self.device_free_space} GB, device_percent_free={self.device_percent_free}%, file_total_size={self.file_total_size} GB, earliest_image={self.modification_date_range.earliest_image}, latest_image={self.modification_date_range.latest_image})"

class SDCardAnalyzer:
    def __init__(self):
        pass

    def analyze_sd_card(self, device, mountpoint):
        device_usage = psutil.disk_usage(mountpoint)
        device_total_space = device_usage.total
        device_used_space = device_usage.used
        device_free_space = device_usage.free
        device_percent_free = device_usage.percent
        modification_date_range = get_modification_range(mountpoint)
        files = find_files_in_sd_card(mountpoint)

        file_total_size = 0
        for file in files:
            file_total_size += file.stat().st_size

        file_count = len(files)

        sd_card = SDCard(device, mountpoint, device_total_space, device_used_space, device_free_space, device_percent_free, file_total_size, file_count, modification_date_range)
        return sd_card



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
    return {'earliest_image': earliest_datetime, 'latest_image': latest_datetime}






if __name__ == "__main__":
    logging.basicConfig(level=logging.DEBUG)
    sdcard_path = ComboLoader().find_sd_cards()[0]
    print_relative_files_in_sd_card(sdcard_path.mountpoint)
    print(f"modification range: {get_modification_range(sdcard_path.mountpoint)}")
    sd_card_analyzer = SDCardAnalyzer()
    sd_card = sd_card_analyzer.analyze_sd_card(sdcard_path.device, sdcard_path.mountpoint)
    print(sd_card)





