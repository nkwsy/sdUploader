'''Tools to help handle files from SD card uploads and transfers across servers/platforms'''

import os, re, sys
from dotenv import dotenv_values

config = dotenv_values()
camtrap_base_url = f'{config["CAMTRAP_BASE_URL"]}/{config["CAMTRAP_VERSION"]}'
camtrap_profile_url = f'{camtrap_base_url}{config["CAMTRAP_PROFILE"]}'
camtrap_deployment_schema_url = f'{camtrap_base_url}{config["CAMTRAP_DEPLOYMENTS_SCHEMA"]}'
camtrap_media_schema_url = f'{camtrap_base_url}{config["CAMTRAP_MEDIA_SCHEMA"]}'
camtrap_observations_schema_url = f'{camtrap_base_url}{config["CAMTRAP_OBSERVATIONS_SCHEMA"]}'


# def get_deployment_dir(work_folder:str=None):
#     '''
#     Combine the work-folder and deployment id to form / match the server's deployment directory path.
#     NOTE - When using sdUploader, sd.create_temp_folder() should be used in place of this function
#     '''

#     # # TODO - Allow / check for CLI input 
#     # print(config['INPUT_DEPLOY_ID'])
#     # print(f"{config['WORK_FOLDER']}/{config['INPUT_DEPLOY_ID']}")
#     # print(os.path.exists(f"{config['WORK_FOLDER']}/{config['INPUT_DEPLOY_ID']}"))

#     if work_folder is None:
#         if 'WORK_FOLDER' in config:
#             work_folder = config['WORK_FOLDER']

#     if config['INPUT_DEPLOY_ID'] is not None and os.path.exists(f"{work_folder}/{config['INPUT_DEPLOY_ID']}"):
#         deploy_dir = f"{work_folder}/{config['INPUT_DEPLOY_ID']}"
#     else:
#         deploy_dir = f"{work_folder}/{sys.argv[1]}"

#     return deploy_dir


def get_image_dirs(deploy_dir):
    '''check for subdirectories under 'DCIM' from a given SD card upload folder (~ deployment ID)'''

    # NOTE: Most camera-formatted SD card image subdirectories under 'DCIM' seem to start with "100".
    #  If this turns out not to be the case, a list of image subdirs is started here:
    # # A list of image-folder names under the DCIM folder
    # # If a new camera model formats SD cards with another naming convention, add to this list
    # sd_card_folder_names = [
    #     '100DSCIM'  # Spypoint,
    #     '100EK113',  # Bushnell
    #     '100MEDIA',  # Reveal
    #     '100SYCAM',  # Reveal
    # ]

    image_subdirs = os.listdir(f'{deploy_dir}/DCIM')

    if len(image_subdirs) > 0:
        image_subdir = [subdir for subdir in image_subdirs if len(re.findall(r'^100', subdir)) > 0]

    print(f'image subdirs = {image_subdir}')
    if len(image_subdir) > 0:
        print('WARNING -- Extra image subdirectories found, but only the first will be processed')

    return f"{deploy_dir}/DCIM/{image_subdir[0]}"
