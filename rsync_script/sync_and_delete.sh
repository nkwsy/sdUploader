#!/bin/bash

# Define source and destination directories
SRC_DIR="/home/microscope/projects/sdUploader/temp/"
DEST_DIR="/home/microscope/ur_media/sdUploader_temp_backup"

# Rsync command to copy files
rsync -av --remove-source-files "$SRC_DIR" "$DEST_DIR"

# Remove any empty directories that were in the source after rsync
find "$SRC_DIR" -type d -empty -delete

# Make script executable
# chmod +x /path/to/sync_and_delete.sh

# Add script to crontab
# crontab -e
# 0 3 * * 2 /home/microscope/projects/sdUploader/sync_and_delete.sh
