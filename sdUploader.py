#!/usr/bin/python3


from tkinter import *
import tkinter as tk
from tkinter import ttk
from tkinter import messagebox
from tkinter import filedialog as fd
import tkcalendar
import json
import os
import sys
import shutil
from datetime import datetime
from dotenv import load_dotenv
from loguru import logger
from PIL import Image
from PIL.ExifTags import TAGS, GPSTAGS
import re
import psutil
from exiftool import ExifToolHelper

logger.remove()  # Remove default handler
logger.add(sys.stderr, 
          format="<green>{time:YYYY-MM-DD HH:mm:ss}</green> | <level>{level: <8}</level> | <cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> - <level>{message}</level>",
          level="INFO")
logger.add("sdUploader.log", 
          format="{time:YYYY-MM-DD HH:mm:ss} | {level: <8} | {name}:{function}:{line} - {message}",
          rotation="5 MB",
          retention="1 week",
          level="DEBUG")
load_dotenv()

# Set default values
#DONE Use PSUTIL to get to this folder automaticly
#TODO get EXIF data to 
#TODO create folders based on dates, allow user to manually override date
#TODO organize camera traps differently
#TODO check if data is properly uploaded 
#TODO Handle MISC files and non-media stuff. Determine what misc stuff is needed for certain cameras IE DJI, insta360 Cannon
#TODO Handle duplacate filenames for large folders, IE folders over 1000 repeating names DJI_001 to something better
#DONE get EXIF data to determine camera type
#TODO Use Dronedeploy api to pull mission data and compare GPS coordinates of photos to automaticly sort into folder based on flight


# Insert appropriate path and files extention.
sd_photo_folder = os.getenv("SD_PHOTO_FOLDER") # example: '/media/mycard/disk/DCIM/'
home_folder = os.getenv("HOME_FOLDER") # example: '/media/mycard/disk/DCIM/'4
#for testing computer
# sd_photo_folder = '/media/microscope/' # example: '/media/mycard/disk/DCIM/'
# home_folder = '/home/lin/MediaBackup/'
# sd_photo_folder = os.path.join('/media/',os.environ.get('USER'))
# home_folder = os.path.join('/home/',os.environ.get('USER'),'/MediaBackup')
# logger.info(sd_photo_folder, home_folder)

exif_tags_to_extract = [
    # Basic Device Info
    "Make",
    "Model",
    "CameraSerialNumber",

    # Software/Firmware Details
    "Software",
    "Firmware",

    # Lens Information
    "LensMake",
    "LensModel",
    "LensSerialNumber",

    # Specialized Camera Fields
    "CameraType",
    "CameraOwnerName",

    # Contextual Tags
    "FileSource",
    "SceneType",
    "ImageHistory",

    # GPS/Location Data
    "GPSLatitude",
    "GPSLongitude",
    "GPSAltitude",
    "GPSSpeed",
    "GPSImgDirection",

    # Drone-specific Tags
    "FlightID",
    "FlightNumber",
    "DronePitch",
    "DroneYaw",
    "DroneRoll",

    # Miscellaneous
    "OwnerName",
    "UserComment",
    "UniqueCameraModel",
    "DeviceSettingDescription",

    # IPTC Data
    "By-line",
    "By-lineTitle",

    # XMP Data
    "CreatorTool",
    "HistorySoftwareAgent",

    # Special Tags
    "Rating",
    "ImageUniqueID",

    # Extended Info
    "MakerNote"
]

#list of exif make data
exif_makes = {
    'Trailcam': ['Browning', 'Bushnell', 'Moultrie', 'Stealth Cam', 'Wildgame Innovations', 'BS680BWNx02126'],
    'DSLR': ['Canon', 'Nikon', 'Sony', 'Pentax', 'Fujifilm', 'Olympus', 'Panasonic', 'Leica'],
    'Drone': ['DJI', 'Parrot', 'Yuneec', 'Autel Robotics', 'Hasselblad'],
    'GoPro': ['GoPro'],
    '360Camera': ['Ricoh', 'Insta360', 'GoPro', 'Samsung']
}


def delete_contents_of_dir(directory_path):
    """Delete all contents of a directory without deleting the directory itself."""
    for item in os.listdir(directory_path):
        item_path = os.path.join(directory_path, item)
        if os.path.isdir(item_path):
            shutil.rmtree(item_path)
        else:
            os.remove(item_path)

def get_files_in_folder(dir):
    file_extension = (".ORF", ".jpg", ".JPG", ".mp4", ".MP4","MOV","mov") # Set extension of both
    
    # sd_files = os.listdir(dir)
    sd_files = os.walk(dir)
    
    # Filter for raw extension
    # # selected_files = [os.path.join(dir, k) for k in sd_files if k.endswith(file_extension)]
    # adjusted following https://stackoverflow.com/questions/3207219/how-do-i-list-all-files-of-a-directory#comment128971338_3207973
    selected_files = [os.path.join(dir, k) for (dir, dirnames, filenames) in sd_files for k in filenames if k.endswith(file_extension)]
    selected_files_out = ('\n').join(selected_files)
    return selected_files_out

def create_temp_folder():
    today = datetime.now()
    folder_name = f"{today.strftime('%Y-%m-%d_%H-%M-%S')}"
    folder_name = folder_name.strip()
    current_directory = os.path.dirname(os.path.abspath(__file__))
    output_folder = os.path.join(current_directory,'temp', folder_name)
    #Create output folder
    try:
        os.makedirs(output_folder)
        logger.info(f'created output folder {output_folder}')
    except FileExistsError as exists:
        print('Folder exists:', exists.filename)
        print('Using existing folder...')
    return output_folder

def copy_directory_contents(src_dir, dst_dir):
    logger.debug(f"Starting copy from {src_dir} to {dst_dir}")
    if not os.path.exists(dst_dir):
        os.makedirs(dst_dir)
        logger.debug(f"Created destination directory: {dst_dir}")
    
    total_size = get_directory_size(src_dir)
    logger.info(f"Total size to copy: {total_size / (1024*1024):.2f} MB")
    
    for item in os.listdir(src_dir):
        src_item = os.path.join(src_dir, item)
        dst_item = os.path.join(dst_dir, item)
        
        try:
            if os.path.isdir(src_item):
                if item != ".Trashes":
                    logger.debug(f"Copying directory: {item}")
                    shutil.copytree(src_item, dst_item)
                else:
                    logger.debug(f"Skipping .Trashes directory")
            else:
                logger.debug(f"Copying file: {item}")
                shutil.copy2(src_item, dst_item)
        except Exception as e:
            logger.error(f"Error copying {src_item}: {str(e)}")
            raise

def start_copy(src_dir):
    # Create temporary folder
    temp_dir = create_temp_folder()
    
    # Copy files to temporary folder
    copy_directory_contents(src_dir, temp_dir)
    
    # Return temporary folder path
    return temp_dir

def get_upload_progress(src_dir, dst_dir):
    # Get total size of source directory
    total_size = get_directory_size(src_dir)
    
    # Get size of files already copied
    copied_size = get_directory_size(dst_dir)
    
    # Calculate progress
    progress = copied_size / total_size
    logger.info(f'Progress download: {progress}, copied/total: {copied_size} / {total_size}')
    return {'progress_percent': progress, 'copied_size': copied_size, 'total_size': total_size}

def get_directory_size(directory):
    total = 0
    with os.scandir(directory) as it:
        for entry in it:
            if entry.is_file():
                total += entry.stat().st_size
            elif entry.is_dir():
                if len(re.findall(r'^\.', entry.name)) < 1:
                    total += get_directory_size(entry.path)
    return total
# pass camera, dateEntry/date, location, file_list, info, cameraid
# 
def simple_upload_files(src_dir, camera_info):
    logger.debug(f"Starting upload with info: {camera_info}")
    try:
        camera = camera_info.get('camera', 'to_be_sorted')
        date = camera_info.get('date', datetime.now().strftime('%Y-%m-%d'))
        location = camera_info.get('location', '')
        notes = camera_info.get('notes', '')
        cameraid = camera_info.get('cameraid', '')
        photographer = camera_info.get('photographer', '')
        
        base_folder = os.path.join(home_folder, camera)
        logger.info(f"Base folder: {base_folder}")
        
        folder_suffix = cameraid if cameraid else location
        folder_name = f"{date.strftime('%Y-%m-%d')}_{folder_suffix}"
        year_folder = f"{date.year}"
        output_folder = os.path.join(base_folder, year_folder, folder_name)
        
        logger.debug(f"Creating output folder: {output_folder}")
        os.makedirs(output_folder, exist_ok=True)
        
        logger.info(f"Starting file copy to {output_folder}")
        copy_directory_contents(src_dir, output_folder)
        
        # Write metadata files
        file_list = get_files_in_folder(src_dir)
        info = f"{location}\n{camera}\n{date.strftime('%Y-%m-%d')}\n{notes}\n{cameraid}\n{photographer}\n\nFile_list\n{file_list}"
        
        logger.debug("Writing metadata files")
        with open(f"{output_folder}/info.txt", 'w') as f:
            f.write(info)
        
        with open(f"{output_folder}/camera_info.json", 'w') as f:
            f.write(json.dumps(camera_info, indent=2, default=str))
            
        with open(f"{src_dir}/uploaded.txt", 'w') as f:
            f.write(f'{output_folder}\n')
            
        logger.info("Upload completed successfully")
        return True
        
    except Exception as e:
        logger.error(f"Upload failed: {str(e)}", exc_info=True)
        return False


def uploadFiles(camera=None, date=None, location='', notes='', file_list=None, cameraid=''):
    #file_extension = 'jpg' # Default file extension - example: '.ORF', '.jpg' or '.CR2'
    base_folder = f"{home_folder}{camera}"
    print(date)
    print(type(date))
    # If cameraId is missing, use location in folder name instead
    folder_suffix = cameraid
    if folder_suffix is None or folder_suffix == '': 
        folder_suffix = location

    folder_name = f"{date.strftime('%Y-%m-%d')}_{folder_suffix}"
    today = datetime.now()
    year_folder = f"{date.year}"
    # folder_name = today.strftime('%Y-%m-%d') + ' ' + ' '.join(args)
    folder_name = folder_name.strip()
    output_folder = os.path.join(base_folder, year_folder, folder_name)
    #Create output folder
    try:
        os.makedirs(output_folder)
        logger.info(f'created output folder {output_folder}')
    except FileExistsError as exists:
        print('Folder exists:', exists.filename)
        print('Using existing folder...')
    #Copy files
    #Progress bar
    n_files = len(file_list)
    logger.info(f'Copying {n_files} files to {output_folder}')
    for i, file_name in enumerate(file_list):
        try:
            shutil.copy2(os.path.join( file_name), output_folder)
        except Exception as err:
            logger.error(err)

    textFile = output_folder + '/info.txt'
    info = f"{location}\n{camera}\n{date.strftime('%Y-%m-%d')}\n{notes}\n{cameraid}\n\nFile_list\n{file_list}"

    print(info)
    with open(textFile, 'w') as f:
        f.write(info)
    logger.info('Finished uploading files!')

    pass

#### Download files to local directory
def downloadFiles(mount_point=None, date=None, location='', notes='', file_list=None):
        #file_extension = 'jpg' # Default file extension - example: '.ORF', '.jpg' or '.CR2'
    # base_folder = f"{home_folder}{camera}"
    file_list = get_files_in_sd_card(mount_point)
    today = datetime.now()
    folder_name = f"{today.strftime('%Y-%m-%d_%H-%M-%S')}"
    folder_name = folder_name.strip()
    current_directory = os.path.dirname(os.path.abspath(__file__))
    output_folder = os.path.join(current_directory,'temp', folder_name)
    #Create output folder
    try:
        os.makedirs(output_folder)
        logger.info(f'created output folder {output_folder}')
    except FileExistsError as exists:
        print('Folder exists:', exists.filename)
        print('Using existing folder...')
    #Copy files
    #Progress bar
    n_files = len(file_list)
    logger.info(f'Copying {n_files} files to {output_folder}')
    # printProgressBar(0, n_files)
    # for i, file_name in enumerate(file_list):
    #     printProgressBar(i+1, n_files)
    #     try:
    #         shutil.copy2(os.path.join( file_name), output_folder)
    #     except Exception as err:
    #         logger.error(err)
    # textFile = output_folder + '/info.txt'
    # info = f"{location}\n{camera}\n{date.strftime('%Y-%m-%d')}\n{notes}\n\nFile_list\n{file_list}"
    # print(info)
    # with open(textFile, 'w') as f:
    #     f.write(info)
    logger.info('Finished uploading files!')
    pass
############## EXIF file stuff
def get_metadata(file_path, tags=['Make', 'Model', 'CameraType', 'MakerNote','MIMEType', 'Software', 'DateTimeOriginal']):
    """Retrieve metadata for any media type."""
    try:
        with ExifToolHelper() as et:
            # logger.info(f'Getting metadata for {file_path}')
            metadata = et.get_tags(file_path, tags)
    except Exception as e:
        logger.error(e)
        return None
    return metadata[0]

def handle_exif_data(img_path):
    try:
        metadata = get_metadata(img_path)
        # image = Image.open(img_path)
        # exifdata = image._getexif()   
        print(metadata)    
        exifdata = metadata
    except:
        return None
    tags = {}
    if not exifdata:
        return None
    # for tag_id, value in exifdata.items():
    #     tag = TAGS.get(tag_id, tag_id)
    #     tags[tag] = value
    # return tags
        # if tag == 'Make' or tag == 'Model':
        #     print(f"{tag}: {value}")



#TODO Check if exif standardizes date info
def parse_date(date_string):
    if date_string is None:
        return None
    return datetime.strptime(date_string, '%Y:%m:%d %H:%M:%S')
############# SD drive util
#TODO use mountpoint or something else to make sure you do not accidently mount important drive. 
    
def is_sdX_device(device_string):
    '''Check if a mounted storage device is an SD card'''
    sd_card_device_string = os.getenv("SD_CARD_MATCH_STRING")
    if sd_card_device_string is None:
        sd_card_device_string = "/dev/sd[b-z]"
    match = re.match(rf'{sd_card_device_string}', device_string)
    # match = re.match(r'/dev/sd[b-z]', device_string)
    return match is not None

def check_sd():
    dp = psutil.disk_partitions()
    devices = []
    for drive in dp:
        device = drive.device
        print(f"device={device}")
        mountpoint = drive.mountpoint
        if is_sdX_device(device):
            devices.append(SdXDevice(drive))
            print(device)
    return devices

class SdXDevice:
    def __init__(self,disk_partition) -> None:
        print(disk_partition)
        self.dp = disk_partition
        self.device = self.dp.device
        self.mountpoint = self.dp.mountpoint
        self.device_usage = psutil.disk_usage(self.mountpoint)
        self.size = self.check_mount_size()
        self.used = self.check_mount_used()
        self.free = self.check_mount_free()
        self.percent = self.check_mount_percent()
        self.files = None
        self.fstype = None
        pass
    
    def get_file_info(self):
        self.update_range = get_modification_range(path=self.mountpoint)
        self.newest_file = self.update_range['latest_image']
        self.oldest_file = self.update_range['earliest_image']
        self.all_image_info = get_all_image_info(self.mountpoint)
        self.camera_types = self.all_image_info['cameras_used']
        self.image_count = self.all_image_info['image_count']
        self.images = self.all_image_info['images']
        self.non_images = self.all_image_info['non_images']
        print(self.all_image_info)

    def check_mount_size(self):
        device_size = round(self.device_usage.total / (1024.0 **3),2)
        return device_size
    
    def check_mount_used(self):
        device_used = round(self.device_usage.used/(1024.0 **3),2)
        return device_used
    
    def check_mount_free(self):
        device_free = round(self.device_usage.free/(1024.0 **3),2)
        return device_free
    
    def check_mount_percent(self):
        device_percent = round(self.device_usage.percent,2)
        return device_percent
    
    def check_mount_files(self):
        file_locations = []
        for root, dirs, files in os.walk(self.mountpoint):
            for file in files:
                file_location = os.path.join(root, file)
                file_locations.append(file_location)
                print(dirs)
        return file_locations

    def check_last_updated_date(self):
        # Get the timestamp of the last modification
        timestamp = os.path.getmtime(self.mountpoint)
        # Convert the timestamp into a readable format
        date = datetime.datetime.fromtimestamp(timestamp)
        return date

        # {'mountpoint': mountpoint, 
        #         'device_size_in_gb': device_size, 
        #         'device_used_in_gb': device_used}

def get_modification_range(path):
    """
    Return the most recent modification date found in the path directory or any of its sub-directories.
    """
    latest_time = os.path.getmtime(path)  # Initialize with the current directory's modification time
    latest_datetime = datetime.fromtimestamp(latest_time)
    earliest_time = os.path.getmtime(path)
    earliest_datetime = latest_datetime
    for root, _, files in os.walk(path):
        for file in files:
            file_path = os.path.join(root, file)
            if os.path.getmtime(file_path) > latest_time:
                latest_time = os.path.getmtime(file_path)
                latest_datetime = datetime.fromtimestamp(latest_time)
            if os.path.getmtime(file_path) < earliest_time:
                earliest_time = os.path.getmtime(file_path)
                earliest_datetime = datetime.fromtimestamp(earliest_time)
    return {'earliest_image': earliest_datetime, 'latest_image': latest_datetime}

def get_files_in_sd_card(dir_path):
    file_locations = []
    for root, dirs, files in os.walk(dir_path):
        for file in files:
            file_location = os.path.join(root, file)
            file_locations.append(file_location)
    return file_locations

def print_files_in_dir(dir_path):
    file_locations = []
    for root, dirs, files in os.walk(dir_path):
        for file in files:
            file_location = os.path.join(root, file)
            file_locations.append(file_location)
    return file_locations

def get_camera_type(make):
    # make = make.replace('\x00', '').strip()
    for camera_type, makes in exif_makes.items():
        if set(make.values()) & set(makes):
            return camera_type
    return 'Unknown'

def get_only_tag(data, keyword):
    for key, value in data.items():
        if keyword in key:
            return value
    return None

def get_image_info(img_path):
    logger.debug(f"Getting image info for: {img_path}")
    try:
        exif_data = get_metadata(img_path)
        if exif_data is None:
            logger.warning(f"No EXIF data found for {img_path}")
            return None
            
        make = get_only_tag(exif_data, 'Make')
        date = get_only_tag(exif_data, 'DateTimeOriginal')
        mediatype = get_only_tag(exif_data, 'MIMEType')
        camera_type = get_camera_type(exif_data)
        
        logger.debug(f"Image info: make={make}, date={date}, type={camera_type}, media={mediatype}")
        return {
            'date': parse_date(date),
            'make': make,
            'file': img_path,
            'camera_type': camera_type,
            'mediatype': mediatype,
            'SourceFile': img_path
        }
    except Exception as e:
        logger.error(f"Error getting image info for {img_path}: {str(e)}", exc_info=True)
        return None

def get_all_image_info(mount_point):
    files = get_files_in_sd_card(mount_point)
    # Sample up to 50 random files, or all files if less than 50
    import random
    sample_size = min(50, len(files))
    sampled_files = random.sample(files, sample_size)
    
    all_images = []
    non_images = []
    for x in sampled_files:
        f_info = get_image_info(x)
        if f_info is not None:
            all_images.append(f_info)
        else:
            non_images.append(x)
    
    cameras_used = set([x['camera_type'] for x in all_images])
    # Return total count of all files, not just sampled ones
    image_count = len(files)
    return {
        'images': all_images, 
        'non_images': non_images, 
        'cameras_used': cameras_used, 
        'image_count': image_count
    }


#!/usr/bin/env python3
