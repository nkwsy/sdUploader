#!/usr/bin/python3


from tkinter import *
from tkinter import ttk
from tkinter import messagebox
from tkinter import filedialog as fd
import tkcalendar
import uploader
import os
import sys
import shutil
from datetime import datetime

# Insert appropriate path and files extention.
sd_photo_folder = '/media/microscope/' # example: '/media/mycard/disk/DCIM/'
home_folder = '/home/microscope/MediaBackup/'
def uploadFiles(*args):

    file_extension = 'jpg' # Default file extension - example: '.ORF', '.jpg' or '.CR2'
    base_folder = home_folder  + str(dir.get())+ ''.join(args)
    year_folder = str(dateEntry.get_date().year)
    folder_name = dateEntry.get_date().strftime('%Y-%m-%d') + location.get() + ' '.join(args)
    today = datetime.now()

    # year_folder = str('2021')

    file_extension = (".ORF", ".jpg", ".JPG", ".mp4", ".MP4") # Set extension of both


    # folder_name = today.strftime('%Y-%m-%d') + ' ' + ' '.join(args)


    folder_name = folder_name.strip()

    output_folder = os.path.join(base_folder, year_folder, folder_name)

    #Create output folder
    try:
        os.makedirs(output_folder)
    except FileExistsError as exists:
        print('Folder exists:', exists.filename)
        print('Using existing folder...')

    sd_files = os.listdir(sd_photo_folder)
    #Filter for raw extension
    selected_files = [k for k in sd_files if k.endswith(file_extension)]

    #Copy files
    #Progress bar
    n_files = len(selected_files)

    print(f'Copying {n_files} {file_extension} files to {output_folder}')

    printProgressBar(0, n_files)

    for i, file_name in enumerate(selected_files):
        printProgressBar(i + 1, n_files)

        try:
            shutil.copy(os.path.join(sd_photo_folder, file_name), output_folder)
        except Error as err:
            print(err)
    textFile = output_folder + '/info.txt'
    file1 = open(textFile,"w")
    info = name.get()+  '\n'+ camera.get()+  '\n'+  date.get()+  '\n'
    print(info)
    with open(textFile, 'w') as f:
        f.write(info)
    print('Finished!')
    wipeSDWindow(sd_photo_folder)
    pass


############## GUI
root = Tk()
root.title("SD card uploader")

mainframe = ttk.Frame(root, padding="3 3 12 12")
mainframe.grid(column=0, row=0, sticky=(N, W, E, S))
root.columnconfigure(0, weight=1)
root.rowconfigure(0, weight=1)

feet = StringVar()
feet_entry = ttk.Entry(mainframe, width=7, textvariable=feet)
feet_entry.grid(column=1, row=1, sticky=(W, E))

meters = StringVar()
ttk.Label(mainframe, textvariable=meters).grid(column=1, row=2, sticky=(W, E))


def browse_button():
    filename = fd.askdirectory(initialdir= sd_photo_folder)
    print(filename)
    dir = filename


# Ranger Name
name = StringVar()
ttk.Label(mainframe, text="Photographer").grid(column=0, row=1, sticky=W)
ttk.Label(mainframe, text="Who took or uploaded these photos").grid(column=2, row=1, sticky=W)
nameEntry = ttk.Entry(mainframe, width=7, textvariable=name)
nameEntry.grid(column=1, row=1, sticky=(W, E))

# Camera Type
camera = StringVar()
ttk.Label(mainframe, text="Camera").grid(column=0, row=2, sticky=W)
ttk.Label(mainframe, text="Type of device or use").grid(column=2, row=2, sticky=W)
cameraEntry = ttk.Combobox(mainframe, textvariable=camera,
   values=('Drone', 'UnderwaterGopro', 'Gopro' , 'CameraTrap'))
cameraEntry.grid(column=1, row=2, sticky=(W, E))

# Date Entry
date = StringVar()
ttk.Label(mainframe, text="Date").grid(column=0, row=3, sticky=W)
dateEntry = tkcalendar.DateEntry(mainframe, width=7, textvariable=date)
dateEntry.grid(column=1, row=3, sticky=(W, E))

# Location
location = StringVar()
ttk.Label(mainframe, text="Location/Title").grid(column=0, row=4, sticky=W)
ttk.Label(mainframe, text="No spaces please as this names folder").grid(column=2, row=4, sticky=W)
nameEntry = ttk.Entry(mainframe, width=7, textvariable=location)
nameEntry.grid(column=1, row=4, sticky=(W, E))

#File Directory
dir = StringVar()
ttk.Label(mainframe, text="image folder").grid(column=0, row=6, sticky=W)
ttk.Button(mainframe, text="Select image folder", command=browse_button).grid(column=1, row=6, sticky=W)

# dirEntry.grid(column=1, row=6, sticky=(W, E))

# root.filename =  filedialog.askopenfilename(initialdir = "/",title = "Select file",filetypes = (("jpeg files","*.jpg"),("all files","*.*")))
# notes
notes = StringVar()
ttk.Label(mainframe, text="Notes").grid(column=0, row=5, sticky=W)
nameEntry = ttk.Entry(mainframe, width=19, textvariable=notes)
nameEntry.grid(column=1, row=5, sticky=(W, E))

# # Delete after upload
# wipeSD = BooleanVar(value=True)
# wipeSDEntry = ttk.Checkbutton(mainframe, text='Wipe SD after upload',
# 	    variable=wipeSD)

# Submit
def submit(*args):
    # mainFolder =  'home_folder' + str(camera.get())+ ''.join(args)
    # folderNameYear = str(dateEntry.get_date().year)
    # subfolder_name = dateEntry.get_date().strftime('%Y-%m-%d') + ' ' + ' '.join(args)
    uploadFiles(*args)
    pass

ttk.Button(mainframe, text="Submit", command=submit).grid(column=3, row=7, sticky=W)

# Progress bar
def printProgressBar(value, max):
    progress = ttk.Progressbar(mainframe, orient=HORIZONTAL, length=max, mode='determinate')
    progress.grid(column=1, row=8, sticky=(W, E))
    ttk.Label(mainframe, text="Uploading... do not exit or pull out SD").grid(column=2, row=8, sticky=W)
    progress['value'] = value
    pass

# wipeSD wipeSD window
def wipeSDWindow(mydir):
    result = messagebox.askyesno(
        message='Would you like to Wipe the SD card?',
        icon='question', title='Wipe SD Card', detail='Verify all files are copied correctly. If this is true please wipe card for next user')
    if result:
        try:
            shutil.rmtree(mydir)
        except OSError as e:
            print ("Error: %s - %s." % (e.filename, e.strerror))
        pass

# feet_entry.grid(column=1, row=1, sticky=(W, E))

for child in mainframe.winfo_children():
    child.grid_configure(padx=5, pady=5)

feet_entry.focus()
root.bind("<Return>", submit)

root.mainloop()

#!/usr/bin/env python3
