#!/usr/bin/env python3

'''
Import photos from SD card into folder with todays date + nickname
Use: importphotos (--jpg|--raw|--both) <nickname of folder (optional)>
Add script to path
'''

import os
import sys
import shutil
from datetime import datetime

# Insert appropriate path and files extention.

def uploadFiles(*args):
    '''setup folders based on camera, date, and either cameraId or location, then copy files'''
    sd_photo_folder = '/home/lin/test/' # example: '/media/mycard/disk/DCIM/'
    home_folder = '/home/lin/testrec/'
    file_extension = 'jpg' # Default file extension - example: '.ORF', '.jpg' or '.CR2'
    base_folder = home_folder  + str(camera.get())+ ''.join(args)
    year_folder = str(dateEntry.get_date().year)
    
    # If cameraId is missing, use location in folder name instead
    folder_suffix = cameraid.get()
    if folder_suffix is None or folder_suffix == '': 
        folder_suffix = location.get()
    
    folder_name = dateEntry.get_date().strftime('%Y-%m-%d') + folder_suffix + '_'.join()
    args = sys.argv[1:]
    today = datetime.now()

    # year_folder = str('2021')

    if args[0][0:2] == "--":
        if args[0] == "--raw":
            file_extension = '.ORF' # Set extension of raw files
        elif args[0] == "--jpg" or args[0] == "--jpeg":
            file_extension = ".JPG" # Set extension of jpg files
        elif args[0] == "--both":
            file_extension = (".ORF", ".JPG") # Set extension of both
        else:
            exit(f"Unknown parameter: {args[0]}")

        args = args[1:]

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

    # printProgressBar(0, n_files, prefix = 'Copying photos:', suffix = '', length = 50)

    for i, file_name in enumerate(selected_files):
        # printProgressBar(i + 1, n_files, prefix = 'Progress:', suffix = '', length = 50)

        try:
            shutil.copy(os.path.join(sd_photo_folder, file_name), output_folder)
        except Error as err:
            print(err)

    print('Finished!')

    pass
