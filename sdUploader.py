#!/usr/bin/python3


from tkinter import *
import tkinter as tk
from tkinter import ttk
from tkinter import messagebox
from tkinter import filedialog as fd
import tkcalendar
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

logger.add(sys.stderr, level="INFO")
logger.add("sdUploader.log", rotation="5 MB")
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

# Progress bar
def printProgressBar(value, max):
    phrase = "Uploading... do not exit or pull out SD. Copying file: " + str(value)+ ' of '+ str(max)
    progress = ttk.Progressbar(manual_frame, orient=HORIZONTAL, maximum=max, mode='determinate')
    progress.grid(column=1, row=8, sticky=(W, E))
    ttk.Label(manual_frame, text=phrase).grid(column=2, row=8, sticky=W)
    progress['value'] = value
    progress.update()
    logger.info(value)
    pass

def get_files_in_folder(dir):
    file_extension = (".ORF", ".jpg", ".JPG", ".mp4", ".MP4","MOV","mov") # Set extension of both
    sd_files = os.listdir(dir)
    #Filter for raw extension
    selected_files = [os.path.join(dir, k) for k in sd_files if k.endswith(file_extension)]
    return selected_files

def copy_directory_contents(src_dir, dst_dir):
    # Ensure destination directory exists
    if not os.path.exists(dst_dir):
        os.makedirs(dst_dir)
    
    for item in os.listdir(src_dir):
        src_item = os.path.join(src_dir, item)
        dst_item = os.path.join(dst_dir, item)
        
        # Check if item is a directory
        if os.path.isdir(src_item):
            shutil.copytree(src_item, dst_item)
        else:
            shutil.copy2(src_item, dst_item)

# pass camera, dateEntry/date, location, file_list, info, 
def uploadFiles(camera=None, date=None, location='', notes='', file_list=None):
    #file_extension = 'jpg' # Default file extension - example: '.ORF', '.jpg' or '.CR2'
    base_folder = f"{home_folder}{camera}"
    print(date)
    print(type(date))
    today = datetime.now()
    folder_name = f"{today.strftime('%Y-%m-%d')}"
    year_folder = f"{date.year}"
    # folder_name = today.strftime('%Y-%m-%d') + ' ' + ' '.join(args)
    folder_name = folder_name.strip()
    current_directory = os.path.dirname(os.path.abspath(__file__))
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
    printProgressBar(0, n_files)
    for i, file_name in enumerate(file_list):
        printProgressBar(i+1, n_files)
        try:
            shutil.copy2(os.path.join( file_name), output_folder)
        except Exception as err:
            logger.error(err)
    textFile = output_folder + '/info.txt'
    info = f"{location}\n{camera}\n{date.strftime('%Y-%m-%d')}\n{notes}\n\nFile_list\n{file_list}"
    print(info)
    with open(textFile, 'w') as f:
        f.write(info)
    logger.info('Finished uploading files!')
    pass

#### Download files to local directory
def downloadFiles(camera=None, date=None, location='', notes='', file_list=None):
    #file_extension = 'jpg' # Default file extension - example: '.ORF', '.jpg' or '.CR2'
    base_folder = f"{home_folder}{camera}"
    print(date)
    print(type(date))
    folder_name = f"{date.strftime('%Y-%m-%d')}_{location}"
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
    printProgressBar(0, n_files)
    for i, file_name in enumerate(file_list):
        printProgressBar(i+1, n_files)
        try:
            shutil.copy2(os.path.join( file_name), output_folder)
        except Exception as err:
            logger.error(err)
    logger.info('Finished uploading files!')
    pass
############## EXIF file stuff
def handle_exif_data(img_path):
    try:
        image = Image.open(img_path)
        exifdata = image._getexif()
    except:
        return None
    tags = {}
    if not exifdata:
        return None
    for tag_id, value in exifdata.items():
        tag = TAGS.get(tag_id, tag_id)
        tags[tag] = value
    return tags
        # if tag == 'Make' or tag == 'Model':
        #     print(f"{tag}: {value}")

#list of exif make data
exif_makes = {
    'Trailcam': ['Browning', 'Bushnell', 'Moultrie', 'Stealth Cam', 'Wildgame Innovations'],
    'DSLR': ['Canon', 'Nikon', 'Sony', 'Pentax', 'Fujifilm', 'Olympus', 'Panasonic', 'Leica'],
    'Drone': ['DJI', 'Parrot', 'Yuneec', 'Autel Robotics', 'Hasselblad'],
    'GoPro': ['GoPro'],
    '360Camera': ['Ricoh', 'Insta360', 'GoPro', 'Samsung']
}

#TODO Check if exif standardizes date info
def parse_date(date_string):
    return datetime.strptime(date_string, '%Y:%m:%d %H:%M:%S')

############# SD drive util

    
def is_sdX_device(device_string):
    match = re.match(r'/dev/sd[a-z]', device_string)
    return match is not None

def check_sd():
    dp = psutil.disk_partitions()
    devices = []
    for drive in dp:
        device = drive.device
        # mountpoint = drive.mountpoint
        if is_sdX_device(device):
            devices.append(SdXDevice(drive))
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



        # {'mountpoint': mountpoint, 
        #         'device_size_in_gb': device_size, 
        #         'device_used_in_gb': device_used}

def return_files_in_sd_card(dir_path):
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
    make = make.replace('\x00', '').strip()
    for camera_type, makes in exif_makes.items():
        if make in makes:
            return camera_type
    return None

def get_image_info(img_path):
    exif_data = handle_exif_data(img_path)
    if exif_data is None:
        return None
    make = exif_data.get('Make')
    date = exif_data.get('DateTimeOriginal')
    camera_type = get_camera_type(make)
    return {'date': parse_date(date), 'make': make, 'file': img_path, 'camera_type': camera_type}

def get_all_image_info(mount_point):
    files = return_files_in_sd_card(mount_point)
    all_images = []
    non_images = []
    for x in files:
        f_info = get_image_info(x)
        if f_info is not None:
            all_images.append(f_info)
        else:
            non_images.append(x)
    return {'images': all_images, 'non_images':non_images }


############## GUI
# root = Tk()
root = tk.Tk()

root.title("SD card uploader")

navbar = ttk.Notebook(root)
tab1 = ttk.Frame(navbar)
tab2 = ttk.Frame(navbar)
navbar.add(tab1, text="Auto Upload")
navbar.add(tab2, text="Manual Upload")
navbar.pack(expand=1, fill="both")

auto_frame = ttk.Frame(tab1, padding="3 3 12 12")
auto_frame.grid(column=0, row=0, sticky=(tk.N, tk.W, tk.E, tk.S))

manual_frame = ttk.Frame(tab2, padding="3 3 12 12")
manual_frame.grid(column=0, row=0, sticky=(tk.N, tk.W, tk.E, tk.S))

root.columnconfigure(0, weight=1)
root.rowconfigure(0, weight=1)

# mainframe = ttk.Frame(root, padding="3 3 12 12")
# mainframe.grid(column=0, row=0, sticky=(N, W, E, S))
# root.columnconfigure(0, weight=1)
# root.rowconfigure(0, weight=1)

feet = StringVar()
feet_entry = ttk.Entry(manual_frame, width=7, textvariable=feet)
feet_entry.grid(column=1, row=1, sticky=(W, E))

meters = StringVar()
ttk.Label(manual_frame, textvariable=meters).grid(column=1, row=2, sticky=(W, E))


def browse_button():
    filename = fd.askdirectory(initialdir= sd_photo_folder)
    print(filename)
    dir.set(filename)

progress = ttk.Progressbar(manual_frame, orient=HORIZONTAL, length=max, mode='determinate')


ttk.Button(manual_frame, text="Submit", command=submit).grid(column=3, row=7, sticky=W)

#### Auto upload frame
#File Directory
#TODO pull SD card info automaticly from list of SD cards
dir = StringVar()
sd_cards = check_sd()
ttk.Label(auto_frame, text="SD card").grid(column=0, row=6, sticky=W)
ttk.Label(auto_frame, text=f"{[x.size if x in sd_cards else None for x in sd_cards]}").grid(column=2, row=2, sticky=W)

sd_entry = ttk.Combobox(auto_frame, textvariable=dir,
   values=(check_sd()))
sd_entry.grid(column=1, row=2, sticky=(W, E))

ttk.Button(auto_frame, text="Select image folder", command=browse_button).grid(column=1, row=6, sticky=W)
ttk.Label(auto_frame, text="Choose directory files are in. Most likely DCIM and the device folder (like Gopro101)").grid(column=2, row=6, sticky=W)

#TODO make this a class
#### Manual upload frame
# Ranger Name
name = StringVar()
ttk.Label(manual_frame, text="Photographer").grid(column=0, row=1, sticky=W)
ttk.Label(manual_frame, text="Who took or uploaded these photos").grid(column=2, row=1, sticky=W)
nameEntry = ttk.Entry(manual_frame, width=7, textvariable=name)
nameEntry.grid(column=1, row=1, sticky=(W, E))

# Camera Type
camera = StringVar()
ttk.Label(manual_frame, text="Camera").grid(column=0, row=2, sticky=W)
ttk.Label(manual_frame, text="Type of device or use").grid(column=2, row=2, sticky=W)
cameraEntry = ttk.Combobox(manual_frame, textvariable=camera,
   values=('Drone', 'UnderwaterGoPro', 'GoPro' , 'CameraTrap'))
cameraEntry.grid(column=1, row=2, sticky=(W, E))

# Date Entry
date = StringVar()
ttk.Label(manual_frame, text="Date").grid(column=0, row=3, sticky=W)
dateEntry = tkcalendar.DateEntry(manual_frame, width=7, textvariable=date)
dateEntry.grid(column=1, row=3, sticky=(W, E))

# Location
location = StringVar()
ttk.Label(manual_frame, text="Location/Title").grid(column=0, row=4, sticky=W)
ttk.Label(manual_frame, text="No spaces please as this names folder").grid(column=2, row=4, sticky=W)
nameEntry = ttk.Entry(manual_frame, width=7, textvariable=location)
nameEntry.grid(column=1, row=4, sticky=(W, E))

#File Directory
dir = StringVar()
ttk.Label(manual_frame, text="image folder").grid(column=0, row=6, sticky=W)
ttk.Button(manual_frame, text="Select image folder", command=browse_button).grid(column=1, row=6, sticky=W)
ttk.Label(manual_frame, text="Choose directory files are in. Most likely DCIM and the device folder (like Gopro101)").grid(column=2, row=6, sticky=W)

print(dir)
# dirEntry.grid(column=1, row=6, sticky=(W, E))

# root.filename =  filedialog.askopenfilename(initialdir = "/",title = "Select file",filetypes = (("jpeg files","*.jpg"),("all files","*.*")))
# notes
notes = StringVar()
ttk.Label(manual_frame, text="Notes").grid(column=0, row=5, sticky=W)
nameEntry = ttk.Entry(manual_frame, width=19, textvariable=notes)
nameEntry.grid(column=1, row=5, sticky=(W, E))

# # Delete after upload
# wipeSD = BooleanVar(value=True)
# wipeSDEntry = ttk.Checkbutton(mainframe, text='Wipe SD after upload',
# 	    variable=wipeSD)

# Submit
def submit():
    # mainFolder =  'home_folder' + str(camera.get())+ ''.join(args)
    # folderNameYear = str(dateEntry.get_date().year)
    # subfolder_name = dateEntry.get_date().strftime('%Y-%m-%d') + ' ' + ' '.join(args)
    print(notes.get())
    # args = {'camera':camera.get(), 'date':dateEntry.get_date(), 'location': location.get(), 'notes': notes.get(),'file_list': get_files_in_folder(dir.get())}
    uploadFiles(camera.get(), dateEntry.get_date(),  location.get(), notes.get(), get_files_in_folder(dir.get()))
    wipeSDWindow(dir)
    pass

ttk.Button(manual_frame, text="Submit", command=submit).grid(column=3, row=7, sticky=W)



# wipeSD wipeSD window
def wipeSDWindow(mydir):
    result = messagebox.askyesno(
        message='Would you like to Wipe the SD card?',
        icon='question', title='Wipe SD Card', detail='Verify all files are copied correctly. If this is true please wipe card for next user')
    if result:
        try:
            shutil.rmtree(mydir)
        except OSError as e:
            logger.error("Error: %s - %s." % (e.filename, e.strerror))
        pass

# feet_entry.grid(column=1, row=1, sticky=(W, E))

for child in manual_frame.winfo_children():
    child.grid_configure(padx=5, pady=5)

feet_entry.focus()
root.bind("<Return>", submit)

root.mainloop()

#!/usr/bin/env python3
