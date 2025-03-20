
from pathlib import Path
import os
import logging

import jsonpickle


from utils.copy_tools import create_temp_folder, BLACKLIST_FOLDERS, FileManifest
from utils.sdcard import ModificationRange



def create_download_folder():
    return create_temp_folder(Path(os.getenv('DOWNLOAD_FOLDER')))




def find_download_metadata():
    download_path = Path(os.getenv('DOWNLOAD_FOLDER'))
    logging.debug(f"Looking for SD downloads in download folder: {download_path}")
    manifest_files = []
    for dir in download_path.iterdir():
        if not dir.is_dir() or dir.name in BLACKLIST_FOLDERS:
            continue
        manifest_file = dir / "manifest.json"
        if manifest_file.is_file():
            try:
                with open(manifest_file, 'r') as f:
                    manifest_json = jsonpickle.decode(f.read())
                    manifest = FileManifest.from_json(manifest_json)
                    logging.debug(f"Found manifest file: {manifest_file}")
                    logging.debug(f"Manifest file contents: {manifest}")
                    manifest_files.append((dir, manifest))
            except Exception as e:
                msg = f"Error reading manifest file: {manifest_file}: {str(e)}"
                logging.error(msg)
                continue

    return manifest_files


def create_upload_folder(date, location, cameraid):
    base_path = Path(os.getenv('UPLOAD_FOLDER'))
    folder_suffix = cameraid if cameraid else location
    folder_name = f"{date.strftime('%Y-%m-%d')}_{folder_suffix}"

    year_folder = f"{date.year}"
    upload_folder = base_path / year_folder / folder_name
    logging.debug(f"Creating upload folder: {upload_folder}")
    try:
        upload_folder.mkdir(parents=True, exist_ok=True)
    except Exception as e:
        logging.error(f"Error creating upload folder: {upload_folder}: {str(e)}")
        raise
    return upload_folder


# For the info file when we create the file list we preserve the behavior of the
# previous code and filter the list to only include specific media files...
# Why? Not sure... But that is what we're doing here.
def write_info_file(upload_folder, camera_info, file_manifest):
    file_extension = (".ORF", ".jpg", ".JPG", ".mp4", ".MP4", ".MOV", ".mov")  # Set extension of both
    try:
        info_file_path = upload_folder / "info.txt"
        logging.debug(f"Writing info file: {info_file_path}")
        with open(info_file_path, 'w') as f:
            f.write(camera_info.location + "\n")
            f.write(camera_info.camera + "\n")
            f.write(camera_info.date.strftime('%Y-%m-%d') + "\n")
            f.write(camera_info.notes + "\n")
            f.write(camera_info.cameraid + "\n")
            f.write(camera_info.photographer + "\n\n")
            f.write("File_list\n")
            for file in file_manifest.file_list:
                if Path(file.filename).suffix in file_extension:
                    f.write(file.filename + "\n")
    except Exception as e:
        logging.error(f"Error writing info file: {info_file_path}: {str(e)}")
        raise

def write_camera_info_file(upload_folder, camera_info):
    camera_info_path = upload_folder / "camera_info.json"
    logging.debug(f"Writing camera info file: {camera_info_path}")
    try:
        with open(camera_info_path, 'w') as f:
            f.write(camera_info.to_json(indent=2))
    except Exception as e:
        logging.error(f"Error writing camera info file: {camera_info_path}: {str(e)}")


def write_uploaded_marker_file(download_folder, upload_folder):
    marker_file_path = download_folder / "uploaded.txt"
    logging.debug(f"Writing uploaded marker file: {marker_file_path}")
    try:
        with open(marker_file_path, 'w') as f:
            f.write(f"upload_folder={upload_folder}\n")
    except Exception as e:
        logging.error(f"Error writing uploaded marker file: {marker_file_path}: {str(e)}")
        raise


