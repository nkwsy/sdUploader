from tkinter import *
import tkinter as tk
from tkinter import ttk, messagebox
from tkinter import filedialog as fd
import tkcalendar
from dotenv import load_dotenv

import logging

import sdUploader as sd
from loguru import logger
from datetime import datetime
import time
from datetime import timedelta
import threading
from multiprocessing import Process
import os
import utils.camtrap_prep_1 as ucp
import utils.csv_tools as csv_tools
import sys
from utils.copy_tools import  CopyThread, CameraInfo
from pathlib import Path
from utils.card_metadata import create_download_folder

from utils.sdcard_loader import ComboLoader
from utils.copy_tools import FileManifest

from upload_manager import UploadManager


def start_download(src, dst):
    """Starts the download process in a separate thread."""
    logger.info(f"Starting download thread from {src} to {dst}")
    thread = threading.Thread(target=sd.copy_directory_contents, args=(src, dst))
    thread.start()
    return thread

def start_upload(folder, info):
    """Starts the upload process in a separate thread."""
    logger.info(f"Starting upload thread from {folder} with info: {info}")
    thread = threading.Thread(target=sd.simple_upload_files, args=(folder, info))
    thread.start()
    return thread

class SDCardUploaderGUI:

    def __init__(self, master):
        logger.info("Initializing SD Card Uploader GUI")
        self.master = master
        self.master.title("SD card uploader")
        self.upload_manager = None

        # figure out if busy before shutdown
        self.locked = False
        # Title Label with 90s Aesthetic
        titleLabel = tk.Label(self.master, text="SD Uploader", font=("Comic Sans MS", 24, "bold"), fg="purple")
        # titleLabel.pack(pady=20) # Adjust padding as needed
        titleLabel.grid(row=0, pady=20)

        self.navbar = ttk.Notebook(self.master)
        self.tab1 = ttk.Frame(self.navbar)
        # self.tab2 = ttk.Frame(self.navbar)

        self.navbar.add(self.tab1, text="Auto Upload")
        # self.navbar.add(self.tab2, text="Manual Upload")
        # self.navbar.pack(expand=1, fill="both")
        self.navbar.grid(row=1, sticky=tk.W+tk.E+tk.N+tk.S, padx=10, pady=10)


        self.dir = StringVar()
        self.mounted_drives = []

        self.create_auto_upload_frame()
        self.update_sd_cards()

        upload_manager_button = ttk.Button(self.master,
                                                text="Open Upload Manager",
                                                command=self.open_upload_manager)
        upload_manager_button.grid(row=2, column=0, rowspan=1, padx=10, sticky=tk.E + tk.W + tk.N + tk.S)


        self.download_thread = None

        # self.create_manual_upload_frame()

    def open_upload_manager(self):
        logger.info("Opening upload manager")
        if not self.upload_manager:
            self.upload_manager = UploadManager(self)

    def remove_upload_manager(self):
        logger.info("Removing upload manager")
        self.upload_manager = None

    def printProgressBar(self, value, max):
        phrase = "Uploading... do not exit or pull out SD. Copying file: " + str(value)+ ' of '+ str(max)
        progress = ttk.Progressbar(manual_frame, orient=HORIZONTAL, maximum=max, mode='determinate')
        progress.grid(column=1, row=8, sticky=(W, E))
        ttk.Label(manual_frame, text=phrase).grid(column=2, row=8, sticky=W)
        progress['value'] = value
        progress.update()
        logger.info(value)
        pass
    
    def create_manual_upload_frame(self):
        manual_frame = ttk.LabelFrame(self.master, text='Simple Catagorization', padding=10)
        manual_frame.grid(column=0, row=10, sticky=(tk.N, tk.W, tk.E, tk.S))
        data_entry(manual_frame)

    def create_auto_upload_frame(self):
        # sd_cards = sd.check_sd()
        # create_drive_boxes(self.tab1, sd_cards)

        # row_index = len(sd_cards) + 1
        ttk.Label(self.tab1, text="SD card").grid(column=0, row=1, sticky=W)

        # ... [Rest of the function remains unchanged]
        # ttk.Label(self.tab1, text="SD card").grid(column=0, row=3, sticky=W)
        # ttk.Label(self.tab1, text=f"{[x.size if x in sd_cards else None for x in sd_cards]} GB").grid(column=1, row=8, sticky=W)
        # sd_entry = ttk.Combobox(self.tab1, textvariable=self.dir,
        # values=(sd.check_sd()))
        # create_drive_boxes(self.tab1, sd_cards)
        # sd_entry.grid(column=1, row=3, sticky=(W, E))

        # select_button = ttk.Button(self.tab1, text="Select", command=self.create_file_tree)
        # select_button.grid(row=5, column=1, padx=10, pady=10)
        # sd_entry.current(0)

    def update_sd_cards(self):
        try:
            sd_cards = ComboLoader().find_sd_cards()
            if sd_cards is None:
                logger.debug("No SD cards detected")
                messagebox.showinfo("No SD cards", "Please insert an SD card")
            mounted_drive = [card.device for card in sd_cards]
            if self.mounted_drives != mounted_drive:
                logger.info(f"SD card change detected. Old: {self.mounted_drives}, New: {mounted_drive}")
                self.mounted_drives = [card.device for card in sd_cards]
                for widget in self.tab1.winfo_children():
                    widget.destroy()
                self.create_drive_boxes(self.tab1, sd_cards)
                logger.debug(f'Updated SD cards: {self.mounted_drives}')
        except Exception as e:
            logger.error(f"Error updating SD cards: {str(e)}", exc_info=True)
        
        self.master.after(10000, self.update_sd_cards)

    def create_drive_boxes(self, master, sd_cards, extended_attributes=True):
        for index, drive in enumerate(sd_cards):
            drive_frame = ttk.LabelFrame(master, text=drive.device, padding=10)
            drive_frame.grid(row=index, column=0, pady=10, padx=10, sticky=tk.W+tk.E)

            # Displaying drive info
            ttk.Label(drive_frame, text=f"Mount Point: {drive.mountpoint}").grid(row=0, column=0, sticky=tk.W, pady=4)
            ttk.Label(drive_frame, text=f"Size: {drive.get_device_total_space_gb()} GB").grid(row=1, column=0, sticky=tk.W, pady=4)
            ttk.Label(drive_frame, text=f"Used: {drive.get_device_used_space_gb()} GB").grid(row=2, column=0, sticky=tk.W, pady=4)

            ttk.Label(drive_frame, text=f" {drive.device_percent_free} %").grid(row=2, column=0, sticky=tk.E, pady=2)
            # if extended_attributes == True:
            if extended_attributes:
                # Start thread to get file info and then update the GUI
                thread = threading.Thread(target=self.get_info_and_update_gui, args=(drive, drive_frame))
                thread.start()              
                # drive.get_file_info()
                # ttk.Label(drive_frame, text=f"Filecount: {drive.image_count}").grid(row=1, column=0, sticky=tk.E, pady=2)
                # ttk.Label(drive_frame, text=f"Devices: {drive.camera_types}").grid(row=3, column=0, sticky=tk.W, pady=2)
                # ttk.Label(drive_frame, text=f"Newest file: {drive.newest_file.strftime('%Y-%m-%d %H:%M:%S')}").grid(row=5, column=0, sticky=tk.W, pady=2)
                # ttk.Label(drive_frame, text=f"Oldest file: {drive.oldest_file.strftime('%Y-%m-%d %H:%M:%S')}").grid(row=6, column=0, sticky=tk.W, pady=2)

            # Big square select button
            select_btn = tk.Button(drive_frame, text="SELECT", command=lambda d=drive: self.select_drive(d))
            select_btn.grid(row=0, column=2, rowspan=5, padx=10, sticky=tk.E + tk.W + tk.N + tk.S)
            select_btn.config(width=10, height=5)
            select_btn.bind("<Enter>", self.turn_red)

    def get_info_and_update_gui(self, drive, drive_frame):
        # This will run in the thread
        drive.get_file_info()
        # Now update the GUI with the new values
        # NOTE: We are using the lambda function with after() to make sure the GUI update happens in the main thread
        self.master.after(0, lambda: self.update_gui_with_drive_info(drive, drive_frame))
    
    def update_gui_with_drive_info(self, drive, drive_frame):
        # Update the labels in the GUI with the new info from the drive
        ttk.Label(drive_frame, text=f"File Count: {drive.file_count}").grid(row=1, column=0, sticky=tk.E, pady=4)
        ttk.Label(drive_frame, text=f"Devices: {drive.camera_types}").grid(row=3, column=0, sticky=tk.W, pady=4)
        if drive.modification_date_range:
            ttk.Label(drive_frame, text=f"Newest file: {drive.modification_date_range.latest_image.strftime('%Y-%m-%d %H:%M:%S')}").grid(row=5, column=0, sticky=tk.W, pady=2)
            ttk.Label(drive_frame, text=f"Oldest file: {drive.modification_date_range.earliest_image.strftime('%Y-%m-%d %H:%M:%S')}").grid(row=6, column=0, sticky=tk.W, pady=2)
            
    def select_drive(self, drive):
        """Handle the drive selection and display the upload confirmation."""
        logging.info(f"Selected drive: {drive.device}")
        self.drive = drive
        # self.upload_confirmation(self.drive)
        self.create_data_entry(self.master, drive)
    
    def turn_red(self, event):
        event.widget["activeforeground"] = "red"

    def create_data_entry(self, master, drive):
        # Create a container frame
        entry_frame = tk.Frame(self.master)
        entry_frame.grid(row=1, column=3, padx=10, pady=10, sticky=tk.W + tk.E)
        ttk.Label(entry_frame, text=f"Step 1: Enter card metadata").grid(row=0, column=0, sticky=W, padx=10, pady=10)


        # Create a LabelFrame for the confirmation embedded in the container frame
        self.entry_window = ttk.LabelFrame(entry_frame, text=f'Selected card: {drive.device}')
        self.entry_window.grid(pady=20, padx=10)
        self.data_entry(self.entry_window)

    def data_entry(self, manual_frame):
        self.photographer = StringVar()
        ttk.Label(manual_frame, text="Photographer").grid(column=0, row=1, sticky=W)
        ttk.Label(manual_frame, text="Who took or uploaded these photos").grid(column=2, row=1, sticky=W)
        self.nameEntry = ttk.Entry(manual_frame, width=7, textvariable=self.photographer)
        self.nameEntry.grid(column=1, row=1, sticky=(W, E))

        # Camera Type
        self.camera = StringVar()
        ttk.Label(manual_frame, text="Camera Type").grid(column=0, row=2, sticky=W)
        ttk.Label(manual_frame, text="Type of device or use").grid(column=2, row=2, sticky=W)
        self.cameraEntry = ttk.Combobox(manual_frame, textvariable=self.camera, values=('360Camera', 'Drone', 'GoPro' , 'Wildlife_Camera', 'DSLR','Underwater_GoPro', 'Mixed', 'Other'))
        self.cameraEntry.grid(column=1, row=2, sticky=(W, E))

        # Camera ID
        self.cameraid = StringVar()
        ttk.Label(manual_frame, text="Camera ID").grid(column=0, row=3, sticky=W)
        ttk.Label(manual_frame, text="Recommended - See camera inventory: tinyurl.com/bdhmzhme").grid(column=2, row=3, sticky=W)
        camera_table = csv_tools.rows('data/camera_inventory.csv')
        camera_names = [row['cameraID'] for row in camera_table]
        camera_names.sort()
        self.cameraIDentry = ttk.Combobox(manual_frame, textvariable=self.cameraid, values=(camera_names))
        self.cameraIDentry.grid(column=1, row=3, sticky=(W, E))
        
        # Location
        self.location = StringVar()
        ttk.Label(manual_frame, text="Location/Title").grid(column=0, row=4, sticky=W)
        ttk.Label(manual_frame, text="Required. No spaces. Type or use drop-down. See tinyurl.com/ur-camera-map").grid(column=2, row=4, sticky=W)
        location_table = csv_tools.rows('data/camtrap_locations.csv')
        location_names = [row['locationName'] for row in location_table]
        location_names.sort()
        self.nameEntry = ttk.Combobox(manual_frame, textvariable=self.location, values=(location_names))
        self.nameEntry.grid(column=1, row=4, sticky=(W, E))

        # Date Entry
        self.date = StringVar()
        ttk.Label(manual_frame, text="Date").grid(column=0, row=5, sticky=W)
        self.dateEntry = tkcalendar.DateEntry(manual_frame, width=7, textvariable=self.date)
        self.dateEntry.grid(column=1, row=5, sticky=(W, E))

        self.notes = StringVar()
        ttk.Label(manual_frame, text="Notes").grid(column=0, row=6, sticky=W)
        self.notesEntry = ttk.Entry(manual_frame, width=19, textvariable=self.notes)
        self.notesEntry.grid(column=1, row=6, sticky=(W, E))

        submit_button = ttk.Button(manual_frame, text="Submit", command=self.submit_form)
        submit_button.grid(row=8, column=1, padx=10, pady=10)


    def submit_form(self):
        self.data_entry_info = {'photographer':self.photographer.get(),
                                'camera':self.camera.get(),
                                'date':self.dateEntry.get_date(),
                                'location': self.location.get(),
                                'notes': self.notes.get(),
                                'cameraid':self.cameraid.get(),
                                # 'file_list': sd.get_files_in_folder(dir.get())
                                }
        print(self.data_entry_info)
        self.upload_confirmation(self.drive)
        

    def upload_confirmation(self, drive):
        """Displays a confirmation box with a progress bar and estimated upload time."""

        # Calculate estimated upload time
        # Convert GB to MB, then divide by transfer rate
        #TRANSFER_RATE_MB_PER_SEC = 25  # More conservative estimate
        #estimated_time_seconds = (drive.used * 1024) / TRANSFER_RATE_MB_PER_SEC
        #estimated_time = int(timedelta(seconds=estimated_time_seconds) / timedelta(minutes=1))


        # Create a container frame
        container_frame = tk.Frame(self.master)
        container_frame.grid(row=1, column=3, padx=10, pady=10, sticky=tk.W+tk.E)

        ttk.Label(container_frame, text=f"Step 2: Download card to local machine").grid(row=0, column=0, sticky=W, padx=10, pady=10)

        # Create a LabelFrame for the confirmation embedded in the container frame
        confirm_window = ttk.LabelFrame(container_frame, text='Download status')
        confirm_window.grid(pady=20, padx=10)

        self.confirm_message = tk.Label(confirm_window, text=f"Are you sure you want to upload from {drive.device}?")
        self.confirm_message.pack(pady=10)
        self.download_time = tk.Label(confirm_window, text=f"Will download {drive.get_file_total_size_gb()} GB from {drive.file_count} files on device")
        self.download_time.pack(pady=10)
        # Progress bar setup
        self.progress_text = tk.StringVar()
        self.progress_text.set("0%")
        self.progress = ttk.Progressbar(confirm_window, orient=tk.HORIZONTAL, length=300, mode='determinate', maximum=1, )
        self.progress.pack(pady=20)

        # autodelete checkbox
        self.autodelete = tk.IntVar()
        autodelete_box = tk.Checkbutton(confirm_window, text='Automaticly clear SD after upload?',variable=self.autodelete, onvalue=1, offvalue=0)
        autodelete_box.pack(pady=10)

        # A confirmation button to start the "upload"
        self.confirm_btn = tk.Button(confirm_window, text="Start Download", command=lambda: self.start_card_download())
        self.confirm_btn.pack(pady=10)

    def start_card_download(self):
        """Simulates the upload process by updating the progress bar."""
        try:

            self.confirm_message['text'] = f"Downloading data from card {self.drive.device}..."
            logger.info(f"Starting card download from {self.drive.device}")
            self.confirm_btn.config(state=tk.DISABLED)
            self.download_folder = create_download_folder()
            logger.info(f"Created temp folder: {self.download_folder}")
            
            self.locked = True

            self.camera_info = CameraInfo(photographer=self.data_entry_info['photographer'],
                                     camera=self.data_entry_info['camera'],
                                     date=self.data_entry_info['date'],
                                     location=self.data_entry_info['location'],
                                     notes=self.data_entry_info['notes'],
                                     cameraid=self.data_entry_info['cameraid'])

            self.download_thread = CopyThread(self.drive.mountpoint,
                                              self.download_folder,
                                              camera_info=self.camera_info,
                                              total_size=self.drive.file_total_size,
                                              total_files=self.drive.file_count,
                                              modification_range=self.drive.modification_date_range)
            self.download_thread.start()
            logger.debug("Started download thread")
            
            self.update_progress()
        except Exception as e:
            logger.error(f"Error starting card download: {str(e)}", exc_info=True)
            self.locked = False
            self.confirm_btn.config(state=tk.NORMAL)
            messagebox.showerror("Error", f"Failed to start download: {str(e)}")

    def update_progress(self):
        """Updates the progress bar and text."""
        # Get progress from the get_upload_progress function
        progress = self.download_thread.get_progress()
        
        # Update the progress bar
        self.progress['value'] = progress.percent

        self.download_time['text'] = f"Completed {progress.current_files} of {progress.total_files} files. Progress: {round(progress.percent * 100, 1)}%."
        
        # Update the progress text
        # self.download_time['text'](f"{int(progress_value['progress_percent'] * 100)}%")
        # logger.info(f"Progress: {int(progress_value['progress_percent'] * 100)}%")

        # Check if the download thread is alive, if yes, continue updating
        if self.download_thread.is_alive():
            self.master.after(1000, self.update_progress)  # Update every second
        else:
            ud_progress = self.download_thread.get_progress()
            if not self.download_thread.error_message:
                logger.info("Upload completed!")
                self.progress_text.set("100%")
                self.progress['value'] = 1
                self.download_time['text'] = 'Download complete.'
                self.confirm_message['text'] = ''
                # self.locked = False

                self.open_upload_manager()
                self.upload_manager.add_upload_job(self.download_thread.destination_path, self.download_thread.manifest)
                #self.upload_thread = start_upload(self.temp_folder, self.data_entry_info)
                # self.create_camtrap_tables(self.data_entry_info)

                messagebox.showinfo("Card download complete", "Card download complete.", detail="It is now safe to wipe or remove the card. Contents will be uploaded to the server in the background. View the upload manager for upload progress.")
                self.wipeSDWindow(self.drive.mountpoint)
                # self.download_complete()
            else:
                logger.warning("Upload failed!")
                self.progress_text.set("Upload failed!")
                self.locked = False
                messagebox.showinfo("Upload Failed", "Upload Failed. Check the temp folder to make sure all files are there. May have to manually upload or call for help")
                self.confirm_btn.config(state=tk.NORMAL)
            



    def create_camtrap_tables(self, data_entry_info):
        '''
        After download is complete, prep two corresponding camtrap-dp tables
        (deployments.csv and media.csv) in the temp folder
        '''
        deploy_id = f"{self.data_entry_info['date']}_{self.data_entry_info['cameraid']}"
        if self.data_entry_info['cameraid'] is None or len(self.data_entry_info['cameraid']) < 1:
            deploy_id = f"{self.data_entry_info['date']}_{self.data_entry_info['location']}"
        deploy_type = self.data_entry_info['camera']
        deploy_year = f"{self.data_entry_info['date']}"[0:4]
        deploy_home_folder = f"{os.getenv('HOME_FOLDER')}/{deploy_type}/{deploy_year}/{deploy_id}"
        while not os.path.exists(deploy_home_folder):
            time.sleep(2)
            print(f'Waiting for deploy directory {deploy_home_folder}')
        ucp.prep_camtrap_dp(file_path_raw=deploy_home_folder, data_input=data_entry_info)
       
    def browse_button(self):
        filename = fd.askdirectory(initialdir= sd.sd_photo_folder)
        print(filename)
        dir.set(filename)

    def wipeSDWindow(self, mydir):
        try:
            if self.autodelete.get() == 1:
                result = True
            else:
                result = messagebox.askyesno(
                    message='Would you like to Wipe the SD card?',
                    icon='question', title='Wipe SD Card', 
                    detail='Verify all files are copied correctly. If this is true please wipe card for next user')
            
            if result:
                logger.info(f"Starting SD card wipe for {mydir}")
                messagebox.showinfo("Wiping SD card", "Please wait")
                sd.delete_contents_of_dir(mydir)
                logger.info("SD card wipe completed successfully")
                messagebox.showinfo("Wiping SD card", "Wipe complete, you can eject the SD card now")
        except OSError as e:
            logger.error(f"Error wiping SD card: {str(e)}", exc_info=True)
            messagebox.showerror("Error", f"Failed to wipe SD card: {str(e)}")
    
    def check_if_working(self):
        if self.locked == True:
            if self.upload_manager and self.upload_manager.is_working():
                time.sleep(5)
            elif self.download_thread.is_alive():
                time.sleep(5)
            else:
                self.locked = False
        else:
            pass

    def create_file_tree(self):
        self.tree = ttk.Treeview(self.master)
        self.tree.heading('#0', text='Directory Structure')
        self.tree.pack(fill=tk.BOTH, expand=True)

    def populate_tree(self, tree, parent_path, parent_node=""):
        """Populate the treeview with the directory structure."""
        for item in os.listdir(parent_path):
            item_path = os.path.join(parent_path, item)
            if os.path.isdir(item_path):
                node = tree.insert(parent_node, "end", text=item, open=False)
                self.populate_tree(tree, item_path, node)
            else:
                tree.insert(parent_node, "end", text=item)


# TODO: ON CLOSING IS BROKEN WITH NEW UPLOAD MANAGER STUFF
# MAKE ALL THIS STUFF BETTER BETTER BETTER
def on_closing(app_instance):
    logger.info(f"Application closing initiated. Locked status: {app_instance.locked}")
    root.withdraw()
    if app_instance.locked:
        logger.info("Waiting for operations to complete before closing")
        app_instance.check_if_working()
        while app_instance.locked:
            logger.warning("Still waiting for upload to finish")
            time.sleep(10)
        logger.info("Operations completed, proceeding with shutdown")
        time.sleep(3)
    logger.info("Application shutdown complete")
    root.quit()
        
def start_gui():
    global root
    root = tk.Tk()
    root.protocol("WM_DELETE_WINDOW", lambda: on_closing(app))
    # Rest of your GUI setup here...
    app = SDCardUploaderGUI(root)
    root.mainloop()


if __name__ == "__main__":
    load_dotenv()
    LOG_LEVEL = os.getenv('LOG_LEVEL', 'INFO').upper()
    logging.basicConfig(level=LOG_LEVEL)
    start_gui()

############## GUI
# root = Tk()


###start


# root.title("SD card uploader")

# navbar = ttk.Notebook(root)
# tab1 = ttk.Frame(navbar)
# tab2 = ttk.Frame(navbar)
# navbar.add(tab1, text="Auto Upload")
# navbar.add(tab2, text="Manual Upload")
# navbar.pack(expand=1, fill="both")

# self.tab1 = ttk.Frame(tab1, padding="3 3 12 12")
# self.tab1.grid(column=0, row=0, sticky=(tk.N, tk.W, tk.E, tk.S))

# manual_frame = ttk.Frame(tab2, padding="3 3 12 12")
# manual_frame.grid(column=0, row=0, sticky=(tk.N, tk.W, tk.E, tk.S))

# root.columnconfigure(0, weight=1)
# root.rowconfigure(0, weight=1)


###end
# mainframe = ttk.Frame(root, padding="3 3 12 12")
# mainframe.grid(column=0, row=0, sticky=(N, W, E, S))
# root.columnconfigure(0, weight=1)
# root.rowconfigure(0, weight=1)
#TODO make this a class
#### Manual upload frame
# Ranger Name
# # Delete after upload
# wipeSD = BooleanVar(value=True)
# wipeSDEntry = ttk.Checkbutton(mainframe, text='Wipe SD after upload',
# 	    variable=wipeSD
