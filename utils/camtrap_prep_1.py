'''Setup Camtrap-DP Media and Deployments tables, with ref to media files on AWS S3'''

import os, re
import utils.camtrap_dp_terms as uc
import utils.file_tools as uf
from dotenv import dotenv_values
from frictionless import validate
from pandas import DataFrame


config = dotenv_values()
camtrap_config_urls = {}

camtrap_config_urls['base_url'] = f"{config['CAMTRAP_BASE_URL']}/{config['CAMTRAP_VERSION']}"
camtrap_config_urls['profile_url'] = f"{camtrap_config_urls['base_url']}{config['CAMTRAP_PROFILE']}"
camtrap_config_urls['deployments'] = f"{camtrap_config_urls['base_url']}{config['CAMTRAP_DEPLOYMENTS_SCHEMA']}"
camtrap_config_urls['media'] = f"{camtrap_config_urls['base_url']}{config['CAMTRAP_MEDIA_SCHEMA']}"
# camtrap_config_urls['observations'] = f"{camtrap_config_urls['base_url']}{config['CAMTRAP_OBSERVATIONS_SCHEMA']}"
# camtrap_config_urls['output'] = config['CAMTRAP_OUTPUT_DIR']

def setup_dataset_as_resource(
        data_name:str=None, 
        camtrap_config_urls:dict=camtrap_config_urls
        ) -> dict:
    '''setup an input table as a resource for a frictionless package'''

    valid_data_name = ['deployments', 'media', 'observations']

    if data_name not in valid_data_name:
        raise ValueError(f'setup_dataset_as_resource: data_name must be one of {valid_data_name}')
    
    data_path = f'{data_name}.csv'
    # dataset.to_csv(data_path, index = False)
    print(f' # # #   -  convert-to-rsc "data_name" = {data_name}')

    resource = {
        'path' : data_path,
        'name' : data_name,
        'scheme' : 'file',
        'format' : 'csv',
        'profile' : 'tabular-data-resource',
        'schema' : camtrap_config_urls[data_name]
    }

    return resource

# 1. DEPLOYMENTS:

    ## 1A. Import user-entered DEPLOYMENTS data
    # #     - what
    # #     - where
    # #     - when
    # #     - who

    ## 1B. Output DEPLOYMENTS.CSV
    #       - File loc: Inside image folder

def generate_deployments_datasets(
        file_path:str=None,
        media_table:list=None,
        input_data:dict=None,
        output_path:str=None,
        ) -> list:
    '''Get sdUploader + image inputs for deployments'''

    # TODO 
    # - update this to use new folder-name-convention 
    # - switch media-file-ref to pull from AWS S3 (`utils_s3` functions)
    
    deps_data_raw = None
    deps_table_blank = uc.get_deployments_table_schema()

    if media_table is not None:

        deps_data_raw = uc.map_to_camtrap_deployment(
            deployment_table = deps_table_blank,
            input_data = input_data,
            media_file_path = file_path,
            media_table = media_table
        )

        deps_data = DataFrame([deps_data_raw])

        dep_data_filename = f"{output_path}/deployments.csv"

        deps_data.to_csv(dep_data_filename, 
                         index=False,
                         )
        
        print(f'deployments_data preview:')
        print(deps_data[:5])

        deps_data_valid = validate(dep_data_filename)
        print(f'deps data validations:  {deps_data_valid}')

    return deps_data


# 2. MEDIA:

    # # 2A. Import image MEDIA data
    # #     - PIL - image metadata
    # #     - DATES -- validate against Deployment dates 
    # #         - if outside Deployment range, set start to deployment start?
    # #     - File loc = "presume" AWS URI from base URL + input folder

    # # 2B. Output MEDIA.csv
    #       - File loc: Inside image folder

def generate_media_datasets(
        file_path:str=None, 
        input_data:dict=None,
        output_path:str=None,
        ) -> DataFrame:
    '''Get sdUploader + image inputs for media. Returns media_table dataframe'''
    
    media_data = None
    image_batch = os.listdir(file_path)
    image_batch.sort()

    if image_batch is not None:

        media_raw_data = []
        media_row_blank = uc.get_media_table_schema()
        media_row = None

        # with ExifToolHelper() as et:
        for image in image_batch:

            if os.path.isfile(f'{file_path}/{image}') == True: # and re.find(r'\.[jpg|cr2|rw2|]', image.lower()) is not None:

                # Skip hidden .DS_Store files if present
                if len(re.findall(r".*(DS_Store|\._).*", f'{file_path}/{image}')) > 0:
                    pass
                else:

                    media_row = uc.map_to_camtrap_media(
                        media_table = media_row_blank, 
                        input_data = input_data,
                        media_file_path = f"{file_path}/{image}",
                        temp_folder = output_path,
                        )
                    if media_row is not None:
                        media_raw_data.append(media_row)

        media_data_filename = f"{output_path}/media.csv"

        media_data = DataFrame(media_raw_data)
        media_data.to_csv(media_data_filename, 
                          index=False,
                          )
        
        media_data_valid = validate(media_data_filename)
        print(f'media data validations:  {media_data_valid}')

    return media_data


def generate_gsheets_observations_datasets(media_data: DataFrame, output_path: str):
    ''' Uses the media table to map a gsheet observation csv '''
    
    image_obs_raw_data = []
    video_obs_raw_data = []

    for _, row in media_data.iterrows():
        # Because media_data already extracts all necessary data, let's just map it up!
        if 'image' in row['fileMediatype']:
            image_obs_raw_data.append(uc.map_media_to_gsheets_observations(row))
        elif 'video' in row['fileMediatype']:
            video_obs_raw_data.append(uc.map_media_to_gsheets_observations(row))


    # Save image observations for gsheets
    img_obs_data_filename = f"{output_path}/gsheets_image_observations.csv"
    image_observations_data = DataFrame(image_obs_raw_data)
    image_observations_data.to_csv(img_obs_data_filename,
                                index=False)

    # Save video observations for gsheets
    video_obs_data_filename = f"{output_path}/gsheets_video_observations.csv"
    video_observations_data = DataFrame(video_obs_raw_data)
    video_observations_data.to_csv(video_obs_data_filename,
                                index=False)
    
    return

  
# 3. SD Upload + rsync
    # Those tables get uploaded to AWS with image files


def prep_camtrap_dp(file_path_raw:str=None, data_input:dict=None):  # sd.SdXDevice=None):
    '''
    Prep Data from SDuploader media and output it as a camtrap-dp dataset

    :param str file_path_raw: File path to a batch of images/media from a camera trap
    :param dict data_input: Data entered by a user for a given sdUpload media batch

    '''

    if file_path_raw is not None:
        deploy_dir = file_path_raw
    else:
        deploy_dir = uf.get_deployment_dir()
    
    print(f"deployment_id directory = {deploy_dir}")

    # if config['MODE'] == "TEST":
    file_path = uf.get_image_dirs(deploy_dir = deploy_dir)

    print(f"file path = {file_path}")
        
    # else: 
    #     # TODO - check if mountpoint sd.SdXDevice is interchangeable with str
    #     file_path = file_path_raw.mountpoint

    data_entry_info = uc.get_sduploader_input(
        sd_temp=file_path_raw, 
        sd_data_entry=data_input
        )

    # # TODO - Get profile + sdUploader-inputs for datapackage.json -- e.g.:
    # descriptor = get_camtrap_dp_data(file_path)

    # Setup output datapackage
    # TODO - replace metadata/descriptor example with real-data inputs
    # TODO - replace deployments example with real-data inputs
    media_data = generate_media_datasets(
        file_path = file_path, 
        input_data = data_entry_info,
        output_path = deploy_dir,
        )
    
    # Generate deployments.CSV
    generate_deployments_datasets(
        file_path = file_path, 
        media_table = media_data,
        input_data = data_entry_info,
        output_path = deploy_dir,
        )


    # Generate gsheets observations.CSV
    generate_gsheets_observations_datasets(
        media_data = media_data,
        output_path = deploy_dir
       )

    # # Generate observations.CSV
    # obs_data = generate_observations_datasets(
    #     media_table = media_data
    #    )
    
    deployments_resource = setup_dataset_as_resource(
        # dataset = deployments_data,
        data_name = 'deployments'
        )

    media_resource = setup_dataset_as_resource(
        # dataset = media_data,
        data_name = 'media'
        )


def main(file_path_raw:str=None, data_input:dict=None):
    '''
    '''
    if 'CAMTRAP_RUN' in config and config['CAMTRAP_RUN'] == "TRUE":
        prep_camtrap_dp(file_path_raw, data_input)
    else:
        print("Skipping Camtrap-DP setup -- Set .env 'CAMTRAP_RUN' variable to 'TRUE' to not skip.")


if __name__ == "__main__":
    main()