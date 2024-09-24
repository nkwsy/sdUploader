# sdUploader
App for uploading and maybe organizing photos / video from sd cards n stuff

# How to run 

CLI: `python main.py`

Once the sdUploader script is running, the interface will launch when an SD card is mounted.

Click "Select" to enter photographer, date, location, and camera-type info.
- Camera: When possible, use values from the drop-down list.
- Location: If camera-type is "Wildlife_Camera", use values from the drop-down list.

Next, click "Submit" and "Start Upload" to begin transferring files.


# Setup / Troubleshooting

1. Make sure `.env` is set up following  `.env.example`, with variables pointing to appropriate paths.
    - **sdUploader** variables:
      - `SD_PHOTO_FOLDER` = /media/microscope
      - `HOME_FOLDER` = /home/microscope/MediaBackup
      - `WORK_FOLDER` = /Location/To/Work/Folder
      - optional `SD_CARD_MATCH_STRING` = default to "/dev/sd[b-z]"
        - You may need to match this to a different device-string depending on how SD cards are recognized on your hardware.
        - e.g. - You can check with: `python sdUploader.py check_sd`

    - **Camtrap-DP** settings:
      - Copy and paste these from the [.env.example](.env.example) file into your `.env`
      - When needed, these variables can be updated to reference new/other versions of [camtrap-dp](https://camtrap-dp.tdwg.org/) schemas.

3. Check that all dependencies are installed:  `pip install -r requirements.txt`



# Ideas:
Integrate / copy aspects from elodie
https://github.com/jmathai/

Make thumbnail showing drone flight
https://github.com/OpenDroneMap/ODM/tree/master

