from tkinter import *
import tkinter as tk
from tkinter import ttk, messagebox
from tkinter import filedialog as fd
import tkcalendar
import sdUploader as sd
from loguru import logger
from datetime import datetime
import time
from datetime import timedelta
import threading
from multiprocessing import Process


def start_download(src, dst):
    """Starts the download process in a separate thread."""
    thread = threading.Thread(target=sd.copy_directory_contents, args=(src, dst))
    thread.start()
    return thread

def start_upload(folder, info):
    """Starts the upload process in a separate thread."""
    thread = threading.Thread(target=sd.simple_upload_files, args=(folder, info))
    thread.start()
    return thread
    # dirEntry.grid(column=1, row=6, sticky=(W, E))


    # root.filename =  filedialog.askopenfilename(initialdir = "/",title = "Select file",filetypes = (("jpeg files","*.jpg"),("all files","*.*")))
    # notes

class SDCardUploaderGUI:

    def __init__(self, master):
        self.master = master
        self.master.title("SD card uploader")

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

        # self.create_manual_upload_frame()


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
        sd_cards = sd.check_sd()
        if sd_cards is None:
            messagebox.showinfo("No SD cards", "Please insert an SD card")
        mounted_drive = [card.device for card in sd_cards]
        if self.mounted_drives != mounted_drive:
            self.mounted_drives = [card.device for card in sd_cards]
            # Clear all the existing widgets in tab1
            for widget in self.tab1.winfo_children():
                widget.destroy()
            self.create_drive_boxes(self.tab1, sd_cards)
            print(f'Updated SD cards: {self.mounted_drives}')
            # create_drive_boxes(self.tab1, sd_cards)
            # return self.update_sd_cards(extended_attributes=True)
        # Call the update_sd_cards function after a certain interval (e.g., every 10 seconds)
        self.master.after(10000, self.update_sd_cards)

    def create_drive_boxes(self, master, sd_cards, extended_attributes=True):
        for index, drive in enumerate(sd_cards):
            drive_frame = ttk.LabelFrame(master, text=drive.device, padding=10)
            drive_frame.grid(row=index, column=0, pady=10, padx=10, sticky=tk.W+tk.E)

            # Displaying drive info
            ttk.Label(drive_frame, text=f"Mount Point: {drive.mountpoint}").grid(row=0, column=0, sticky=tk.W, pady=2)
            ttk.Label(drive_frame, text=f"Size: {drive.size} GB").grid(row=1, column=0, sticky=tk.W, pady=2)
            ttk.Label(drive_frame, text=f"Used: {drive.used} GB").grid(row=2, column=0, sticky=tk.W, pady=2)
            ttk.Label(drive_frame, text=f" {drive.percent} %").grid(row=2, column=0, sticky=tk.E, pady=2)
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
        ttk.Label(drive_frame, text=f"Filecount: {drive.image_count}").grid(row=1, column=0, sticky=tk.E, pady=2)
        ttk.Label(drive_frame, text=f"Devices: {drive.camera_types}").grid(row=3, column=0, sticky=tk.W, pady=2)
        ttk.Label(drive_frame, text=f"Newest file: {drive.newest_file.strftime('%Y-%m-%d %H:%M:%S')}").grid(row=5, column=0, sticky=tk.W, pady=2)
        ttk.Label(drive_frame, text=f"Oldest file: {drive.oldest_file.strftime('%Y-%m-%d %H:%M:%S')}").grid(row=6, column=0, sticky=tk.W, pady=2)
            
    def select_drive(self, drive):
        """Handle the drive selection and display the upload confirmation."""
        print(f"Selected drive: {drive.device}")
        self.drive = drive
        # self.upload_confirmation(self.drive)
        self.create_data_entry(self.master)
    
    def turn_red(self, event):
        event.widget["activeforeground"] = "red"

    def create_data_entry(self, master):
        # Create a container frame
        entry_frame = tk.Frame(self.master)
        entry_frame.grid(row=1, column=3, padx=10, pady=10, sticky=tk.W+tk.E)
        # Create a LabelFrame for the confirmation embedded in the container frame
        self.entry_window = ttk.LabelFrame(entry_frame, text='Upload Progress')
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
        ttk.Label(manual_frame, text="Camera").grid(column=0, row=2, sticky=W)
        ttk.Label(manual_frame, text="Type of device or use").grid(column=2, row=2, sticky=W)
        self.cameraEntry = ttk.Combobox(manual_frame, textvariable=self.camera, values=('360Camera', 'Drone', 'GoPro' , 'Wildlife_Camera', 'DSLR','Underwater_GoPro', 'Mixed', 'Other'))
        self.cameraEntry.grid(column=1, row=2, sticky=(W, E))

        # Date Entry
        self.date = StringVar()
        ttk.Label(manual_frame, text="Date").grid(column=0, row=3, sticky=W)
        self.dateEntry = tkcalendar.DateEntry(manual_frame, width=7, textvariable=self.date)
        self.dateEntry.grid(column=1, row=3, sticky=(W, E))
        
        # Location
        self.location = StringVar()
        ttk.Label(manual_frame, text="Location/Title").grid(column=0, row=4, sticky=W)
        ttk.Label(manual_frame, text="No spaces please as this names folder. For 'Wildlife_Camera', select from drop-down.").grid(column=2, row=4, sticky=W)
        self.nameEntry = ttk.Combobox(manual_frame, textvariable=self.location, values=('BubblyCreek', 'Prologis','WM_Boardwalk_A', 'WM_Boardwalk_B', 'WM_Boardwalk_C', 'WM_Boardwalk_D', 'WM_Boardwalk_E', 'WM_Boardwalk_F', 'WM_Boardwalk_G'))
        self.nameEntry.grid(column=1, row=4, sticky=(W, E))

        self.notes = StringVar()
        ttk.Label(manual_frame, text="Notes").grid(column=0, row=5, sticky=W)
        self.notesEntry = ttk.Entry(manual_frame, width=19, textvariable=self.notes)
        self.notesEntry.grid(column=1, row=5, sticky=(W, E))
        submit_button = ttk.Button(manual_frame, text="Submit", command=self.submit_form)
        submit_button.grid(row=8, column=1, padx=10, pady=10)


    def submit_form(self):
        self.data_entry_info = {'photographer':self.photographer.get(),
                                'camera':self.camera.get(), 
                                'date':self.dateEntry.get_date(), 
                                'location': self.location.get(), 
                                'notes': self.notes.get(),
                                # 'file_list': sd.get_files_in_folder(dir.get())
                                }
        print(self.data_entry_info)
        self.upload_confirmation(self.drive)


    def upload_confirmation(self, drive):
        """Displays a confirmation box with a progress bar and estimated upload time."""

        # Calculate estimated upload time
        # Converting GB to MB for the drive size and then estimating the time at 25MB/s
        estimated_time_seconds = (drive.size * 1024) / 25
        estimated_time = int(timedelta(seconds=estimated_time_seconds) / timedelta(minutes=1))

        # Create a container frame
        container_frame = tk.Frame(self.master)
        container_frame.grid(row=1, column=3, padx=10, pady=10, sticky=tk.W+tk.E)

        # Create a LabelFrame for the confirmation embedded in the container frame
        confirm_window = ttk.LabelFrame(container_frame, text='Upload Progress')
        confirm_window.grid(pady=20, padx=10)

        tk.Label(confirm_window, text=f"Are you sure you want to upload from {drive.device}?").pack(pady=10)
        self.download_time = tk.Label(confirm_window, text=f"Estimated download time: {estimated_time} minutes").pack(pady=10)
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
        self.confirm_btn = tk.Button(confirm_window, text="Start Upload", command=lambda: self.start_card_download(estimated_time_seconds))
        self.confirm_btn.pack(pady=10)

    def start_card_download(self, estimated_time_seconds):
        """Simulates the upload process by updating the progress bar."""
        self.confirm_btn.config(state=tk.DISABLED)
        self.temp_folder = sd.create_temp_folder()
        logger.info(f"Gui Starting upload from {self.drive.device} to {self.temp_folder}")
        self.locked = True
        self.upload_thread = start_download(self.drive.mountpoint, self.temp_folder)
        
        # Start updating the progress in the GUI periodically (e.g., every 1 second)
        self.update_progress()

    def update_progress(self):
        """Updates the progress bar and text."""
        # Get progress from the get_upload_progress function
        progress_value = sd.get_upload_progress(self.drive.mountpoint, self.temp_folder)
        
        # Update the progress bar
        self.progress['value'] = progress_value['progress_percent']
        
        # Update the progress text
        # self.download_time['text'](f"{int(progress_value['progress_percent'] * 100)}%")
        logger.info(f"Progress: {int(progress_value['progress_percent'] * 100)}%")

        # Check if the upload thread is alive, if yes, continue updating
        if self.upload_thread.is_alive():
            self.master.after(1000, self.update_progress)  # Update every second
        else:
            logger.info("Upload completed!")
            self.progress_text.set("100%")
            self.locked = False
            messagebox.showinfo("Upload Complete", "Upload Complete")
            self.wipeSDWindow(self.drive.mountpoint)
            self.download_complete()
            
    def download_complete(self):
        self.locked = True
        messagebox.showinfo("Backing up", "Backing up to server, might take a wee bit")
        start_upload_thread = start_upload(self.temp_folder, self.data_entry_info)
        messagebox.showinfo("Done", "All done you schmuck")
        self.locked = False
        # self.master.quit()
        
       
    def browse_button(self):
        filename = fd.askdirectory(initialdir= sd.sd_photo_folder)
        print(filename)
        dir.set(filename)

    def wipeSDWindow(self, mydir):
        # ... [The rest of the method remains unchanged]
        if self.autodelete.get() == 1:
            result = True
        else:
            result = messagebox.askyesno(
                message='Would you like to Wipe the SD card?',
                icon='question', title='Wipe SD Card', detail='Verify all files are copied correctly. If this is true please wipe card for next user')
        if result:
            try:
                messagebox.showinfo("Wiping SD card", "Please wait")
                print(mydir)
                sd.delete_contents_of_dir(mydir)
                messagebox.showinfo("Wiping SD card", "Wipe complete, you can eject the SD card now")
            except OSError as e:
                logger.error("Error: %s - %s." % (e.filename, e.strerror))
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

def on_closing(app_instance):
    logger.info(f"Closing GUI: app_instance.locked = {app_instance.locked}")
    root.withdraw()
    if app_instance.locked == True:
        logger.warning("Upload in progress, please wait")
        time.sleep(10)
    root.quit()
        
def start_gui():
    global root
    root = tk.Tk()
    root.protocol("WM_DELETE_WINDOW", lambda: on_closing(app))
    # Rest of your GUI setup here...
    app = SDCardUploaderGUI(root)
    root.mainloop()

def check_sd_loop():
    old_sd_card = None
    while True:
        sd_card_check = sd.check_sd()
        mounted_drive_check = [card.device for card in sd_card_check]
        #logger.info(f"Checking for SD cards: {mounted_drive_check}, old: {old_sd_card}")
        if not sd_card_check:
            print(sd_card_check)
            print(type(sd_card_check))
            old_sd_card = None
            time.sleep(5)
        elif mounted_drive_check == old_sd_card:
            # logger.info(f"Identical SD cards detected: {mounted_drive_check} == {old_sd_card}")
            time.sleep(5)
        else:
            logger.info(f"Starting Gui, SD card detected: {mounted_drive_check}")
            old_sd_card = [card.device for card in sd_card_check]
            start_gui()

if __name__ == "__main__":
    check_sd_loop()
    # sd_card_detected = check_sd_loop()
    # if sd_card_detected:
        # root = tk.Tk()
        # root.mainloop()

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
