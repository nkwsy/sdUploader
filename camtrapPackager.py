'''DRAFT - Setup camtrap-dp package'''
''' - from https://gitlab.com/oscf/camtrap-package '''

import io, os, requests
import sdUploader as sd
import utils.camtrap_dp_terms as uc
from camtrap_package import package
from dotenv import dotenv_values
from exiftool import ExifToolHelper
from frictionless import Schema, Resource, Package, validate
from pandas import DataFrame, read_csv


config = dotenv_values()
camtrap_config_urls = {}

camtrap_config_urls['base_url'] = f"{config['CAMTRAP_BASE_URL']}/{config['CAMTRAP_VERSION']}"
camtrap_config_urls['profile_url'] = f"{camtrap_config_urls['base_url']}{config['CAMTRAP_PROFILE']}"
camtrap_config_urls['deployments'] = f"{camtrap_config_urls['base_url']}{config['CAMTRAP_DEPLOYMENTS_SCHEMA']}"
camtrap_config_urls['media'] = f"{camtrap_config_urls['base_url']}{config['CAMTRAP_MEDIA_SCHEMA']}"
camtrap_config_urls['observations'] = f"{camtrap_config_urls['base_url']}{config['CAMTRAP_OBSERVATIONS_SCHEMA']}"


def get_camtrap_dp_metadata(file_path_raw:sd.SdXDevice = None, 
                        sd_data_entry_info:dict = None,
                        camtrap_config_urls:dict = camtrap_config_urls,
                        resources_prepped:list = None
                        ) -> dict:
    '''Get sdUploader inputs for datapackage.json'''

    if config['MODE'] == "TEST":
        file_path = config['TEST_SD_FILE_PATH']
        data_entry_info = {
            'photographer':'test-PHOTOGRAPHER',
            'camera':'test-CAMERA', 
            'date':'test-DATE', 
            'location': 'test-DEPLOYMENT-LOCATION', 
            'notes': 'test-NOTES',
            }
        
    else: 
        file_path = file_path_raw.mountpoint
        data_entry_info = sd_data_entry_info
        
    print(f'file path = = = {file_path}')

    # # TODO - Get profile + sdUploader-inputs for datapackage.json -- e.g.:
    # descriptor = get_camtrap_dp_data(file_path)
    
    descriptor = uc.CamtrapPackage(
        camtrap_config_urls=camtrap_config_urls,
        data_entry_info=data_entry_info,
        resources_prepped=resources_prepped)

    return descriptor


def convert_dataset_to_resource(dataset:DataFrame=None, 
                           data_name:str=None, 
                           camtrap_config_urls:dict=camtrap_config_urls) -> Resource:
    '''setup an input table as a resource for a frictionless package'''

    valid_data_name = ['deployments', 'media', 'observations']

    if data_name not in valid_data_name:
        raise ValueError(f'convert_dataset_to_resource: data_name must be one of {valid_data_name}')
    
    data_path = f'{data_name}.csv'
    dataset.to_csv(data_path, index = False)

    resource = Resource(path = data_path)
    resource.name = data_name
    # resource.scheme = 'file'
    # resource.format = 'csv'
    resource.profile = 'tabular-data-resource',
    resource.schema = camtrap_config_urls[data_name]

    return resource


def generate_deployments_datasets(file_path:str=None, media_table:list=None, input_data:dict=None) -> list:
    '''Get sdUploader + image inputs for deployments'''
    
    deps_data_raw = None
    deps_table_blank = uc.get_deployments_table_schema()
    # image_batch = os.listdir(file_path)

    # sd.get_image_info('/Volumes/LUMIX/DCIM163_PANA')
    if media_table is not None:

        deps_data_raw = uc.map_to_camtrap_deployment(
            deployment_table = deps_table_blank,
            input_data = input_data,
            media_file_path = file_path,
            media_table = media_table
        )

        print(f'deps_data_raw = {deps_data_raw}')
        deps_data = DataFrame([deps_data_raw])
        deps_data.to_csv()
        
        print(f'deployments_data = {deps_data}')

    return deps_data


def generate_media_datasets(file_path:str=None, input_data:dict=None) -> list:
    '''Get sdUploader + image inputs for media'''
    
    media_data = None
    image_batch = os.listdir(file_path)

    # print(f'image_batch = {image_batch}')

    # sd.get_image_info('/Volumes/LUMIX/DCIM163_PANA')
    if image_batch is not None:

        # camtrap_tags = ['Make', 'Model']
        media_raw_data = []
        media_row_blank = uc.get_media_table_schema()
        media_row = None

        with ExifToolHelper() as et:
            for image in image_batch:
                # print(f'img ==== {file_path}/{image} - {os.path.isfile(f"{file_path}/{image}")}')

                if os.path.isfile(f'{file_path}/{image}') == True: # and re.find(r'\.[jpg|cr2|rw2|]', image.lower()) is not None:

                    # try:

                    # image_row = {}
                    # for tags in et.get_tags(f'{file_path}/{image}', tags=camtrap_tags):
                    #     # for tags in et.get_tags("/Volumes/LUMIX/DCIM/162_PANA/P1620389.JPG", tags=camtrap_tags):
                    #     for k, v in tags.items():
                    #         # if v is not None:
                    #         image_row[k] = v
                    
                    media_row = uc.map_to_camtrap_media(
                        media_table=media_row_blank, input_data=input_data,
                        media_file_path=f"{file_path}/{image}")
                    # print(f'media_row = {media_row}')
                    media_raw_data.append(media_row)
                    
                    # except:
                    #     print('skipping non-file input')
                        
        media_data = DataFrame(media_raw_data)
        media_data.to_csv()

    return media_data


def generate_observations_datasets(
        # file_path:str=None, 
        media_table:list=None, 
        input_data:dict=None) -> list:
    '''Get sdUploader + image inputs for observations'''
    
    obs_data_raw = None
    obs_table_blank = uc.get_observations_table_schema()
    # image_batch = os.listdir(file_path)

    # sd.get_image_info('/Volumes/LUMIX/DCIM163_PANA')
    if media_table is not None:

        obs_data_raw = uc.map_to_camtrap_observations(
            observations_table = obs_table_blank,
            input_data = input_data,
            # media_file_path = file_path,
            media_table = media_table
        )
        obs_data = DataFrame([obs_data_raw])
        obs_data.to_csv()
        
        print(f'observations_data = {obs_data}')
    
    return obs_data


def prep_camtrap_dp(file_path_raw:sd.SdXDevice=None, sd_data_entry_info:dict=None):
    '''Prep Data from SDuploader media and output it a camtrap-dp dataset'''
    '''
    TODO - reference these functions in main.SDCardUploaderGUI.data_entry_info? 
    or split out data_entry_info functions from main.SDCardUploaderGUI ? 
    '''

    if config['MODE'] == "TEST":
        file_path = config['TEST_SD_FILE_PATH']
        data_entry_info = {
            'photographer':'test-PHOTOGRAPHER',
            'camera':'test-CAMERA', 
            'date':'test-DATE', 
            'location': 'test-LOCATION', 
            'notes': 'test-NOTES',
            }
        
    else: 
        # TODO - check if mountpoint sd.SdXDevice is interchangeable with str
        file_path = file_path_raw.mountpoint
        data_entry_info = sd_data_entry_info
        
    print(f'file path = = = {file_path}')

    # # TODO - Get profile + sdUploader-inputs for datapackage.json -- e.g.:
    # descriptor = get_camtrap_dp_data(file_path)


    # Get camera image + exif data for media.csv
    # media_table = setup_media_dataset(file_path)
    # media_table = uc.get_media_table_schema()
    # print(media_table)


    # Setup output datapackage
    # TODO - replace metadata/descriptor example with real-data inputs
    # TODO - replace deployments example with real-data inputs
    media_data = generate_media_datasets(
        file_path, 
        data_entry_info
        )

    deployments_data = generate_deployments_datasets(
        file_path=file_path, 
        media_table=media_data,
        input_data=data_entry_info
        )

    observations_data = generate_observations_datasets(
        media_table=media_data, 
        input_data=data_entry_info
        )
    
    deployments_resource = convert_dataset_to_resource(dataset = deployments_data,
                                                       data_name = 'deployments')

    media_resource = convert_dataset_to_resource(dataset = media_data,
                                                 data_name = 'media')

    observations_resource = convert_dataset_to_resource(dataset = observations_data,
                                                        data_name = 'observations')

    data_resources = [deployments_resource, media_resource, observations_resource]
        
    output_camtrap = get_camtrap_dp_metadata(
        file_path_raw = file_path_raw, 
        sd_data_entry_info = data_entry_info,
        camtrap_config_urls = camtrap_config_urls,
        resources_prepped = data_resources
        )

    # Validate Camtrap-DP
    # TODO - output validation log
    # valid = output_camtrap.validate_package()
    # print(f'# # # VALID Camtrap-dp? {valid}')

    # Alternatively, validate using frictionless
    valid_frictionless = validate(output_camtrap)
    print(f'# # # VALID Camtrap-dp? {valid_frictionless}')

    # Output Camtrap-DP
    # TODO - write out to appropriate place

    output_result = uc.save(package_metadata = output_camtrap, 
                            output_path="test_camtrap_output")
    print(f'# # # OUTPUT Camtrap-dp? {output_result}')


if __name__ == "__main__":
    prep_camtrap_dp()