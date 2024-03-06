'''DRAFT - Setup camtrap-dp package'''
''' - from https://gitlab.com/oscf/camtrap-package '''

import json, os, re
import sdUploader as sd
import utils.camtrap_dp_terms as uc
from dotenv import dotenv_values
from exiftool import ExifToolHelper
from frictionless import validate
from pandas import DataFrame


config = dotenv_values()
camtrap_config_urls = {}

camtrap_config_urls['base_url'] = f"{config['CAMTRAP_BASE_URL']}/{config['CAMTRAP_VERSION']}"
camtrap_config_urls['profile_url'] = f"{camtrap_config_urls['base_url']}{config['CAMTRAP_PROFILE']}"
camtrap_config_urls['deployments'] = f"{camtrap_config_urls['base_url']}{config['CAMTRAP_DEPLOYMENTS_SCHEMA']}"
camtrap_config_urls['media'] = f"{camtrap_config_urls['base_url']}{config['CAMTRAP_MEDIA_SCHEMA']}"
camtrap_config_urls['observations'] = f"{camtrap_config_urls['base_url']}{config['CAMTRAP_OBSERVATIONS_SCHEMA']}"
camtrap_config_urls['output'] = config['CAMTRAP_OUTPUT_DIR']

def get_camtrap_dp_metadata(
        file_path_raw:sd.SdXDevice = None, 
        # sd_data_entry_info:dict = None,
        resources_prepped:list = None,
        media_table:list = None
        ) -> uc.CamtrapPackage:
    '''Setup metadata + resources datapackage.json as a camtrap package'''
    
    descriptor = uc.CamtrapPackage(
        profile_dict = None,
        resources_prepped = resources_prepped,
        media_table = media_table)

    return descriptor


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


def generate_deployments_datasets(
        file_path:str=None,
        media_table:list=None,
        input_data:dict=None
        ) -> list:
    '''Get sdUploader + image inputs for deployments'''
    
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

        dep_data_filename = f"{camtrap_config_urls['output']}/deployments.csv"

        deps_data.to_csv(dep_data_filename, 
                         index=False,
                         )
        
        print(f'deployments_data preview:')
        print(deps_data[:5])

        deps_data_valid = validate(dep_data_filename)
        print(f'deps data validations:  {deps_data_valid}')

    return deps_data


def generate_media_datasets(file_path:str=None, input_data:dict=None) -> list:
    '''Get sdUploader + image inputs for media'''
    
    media_data = None
    image_batch = os.listdir(file_path)

    if image_batch is not None:

        media_raw_data = []
        media_row_blank = uc.get_media_table_schema()
        media_row = None

        with ExifToolHelper() as et:
            for image in image_batch:

                if os.path.isfile(f'{file_path}/{image}') == True: # and re.find(r'\.[jpg|cr2|rw2|]', image.lower()) is not None:

                    # Skip hidden .DS_Store files if present
                    if len(re.findall(r".*DS_Store.*", f'{file_path}/{image}')) > 0:
                        pass
                    else:

                        media_row = uc.map_to_camtrap_media(
                            media_table=media_row_blank, input_data=input_data,
                            media_file_path=f"{file_path}/{image}")
                        media_raw_data.append(media_row)

        media_data_filename = f"{camtrap_config_urls['output']}/media.csv"

        media_data = DataFrame(media_raw_data)
        media_data.to_csv(media_data_filename, 
                          index=False,
                          )
        
        media_data_valid = validate(media_data_filename)
        print(f'media data validations:  {media_data_valid}')

    return media_data


def generate_observations_datasets(
        media_table:list=None) -> list:
    '''Get sdUploader + image inputs for observations'''
    
    obs_data_raw = None
    obs_table_blank = uc.get_observations_table_schema()

    if media_table is not None:

        obs_data_raw = uc.map_to_camtrap_observations(
            observations_table = obs_table_blank,
            media_table = media_table
        )

        obs_data_filename = f"{camtrap_config_urls['output']}/observations.csv"

        obs_data = DataFrame(obs_data_raw)
        obs_data.to_csv(obs_data_filename, 
                        index=False,
                        )
        
        print(f'observations_data preview: ')
        print(obs_data[:5])

        obs_data_valid = validate(obs_data_filename)
        print(f'obs data validations:  {obs_data_valid}')
    
    return obs_data


def prep_camtrap_dp(file_path_raw:sd.SdXDevice=None):
    '''Prep Data from SDuploader media and output it a camtrap-dp dataset'''
    '''
    TODO - reference these functions in main.SDCardUploaderGUI.data_entry_info? 
    or split out data_entry_info functions from main.SDCardUploaderGUI ? 
    '''

    if config['MODE'] == "TEST":
        file_path = config['INPUT_IMAGE_DIR']
        
    else: 
        # TODO - check if mountpoint sd.SdXDevice is interchangeable with str
        file_path = file_path_raw.mountpoint

    data_entry_info = uc.get_sduploader_input()

    # # TODO - Get profile + sdUploader-inputs for datapackage.json -- e.g.:
    # descriptor = get_camtrap_dp_data(file_path)

    # Setup output datapackage
    # TODO - replace metadata/descriptor example with real-data inputs
    # TODO - replace deployments example with real-data inputs
    media_data = generate_media_datasets(
        file_path = file_path, 
        input_data = data_entry_info
        )

    deployments_data = generate_deployments_datasets(
        file_path = file_path, 
        media_table = media_data,
        input_data = data_entry_info
        )

    observations_data = generate_observations_datasets(
        media_table = media_data
        )
    
    deployments_resource = setup_dataset_as_resource(dataset = deployments_data,
                                                       data_name = 'deployments')

    media_resource = setup_dataset_as_resource(dataset = media_data,
                                                 data_name = 'media')

    observations_resource = setup_dataset_as_resource(dataset = observations_data,
                                                        data_name = 'observations')

    data_resources = [
        deployments_resource,
        media_resource,
        observations_resource
        ]
        
    output_camtrap = get_camtrap_dp_metadata(
        file_path_raw = file_path_raw, 
        # sd_data_entry_info = data_entry_info,
        resources_prepped = data_resources,
        media_table = media_data
        )
    
    # print(f'# # # # # # camtrap data START # # # #')
    # print(output_camtrap.__dict__)
    # print(f'# # # # # # camtrap data FINISH # # # #')


    # Output Camtrap-DP
    output_path = camtrap_config_urls['output']
    output_camtrap_file = f"{output_path}/camtrap-dp-{output_camtrap.id}.zip"

    output_result = uc.save(package_metadata = output_camtrap, 
                            output_path = output_path)
    print(f'# # # OUTPUT Camtrap-dp? {output_result}')


    # Validate output ZIP file using frictionless
    if output_result == True:
        if os.path.exists(output_camtrap_file):
            print(f'Validating output...May take a minute...')

            valid_frictionless = validate(output_camtrap_file)

            print(f"...outputing validation details to 'validation-{output_camtrap.id}.json'")

            with open(f"{output_path}/validation-{output_camtrap.id}.json", "w", encoding='utf-8') as file:
                json.dump(valid_frictionless.to_dict(), file, indent=4, sort_keys=False)

    # Cleanup
    for file in ['datapackage.json', 'deployments.csv', 'media.csv', 'observations.csv']:
        out_file = f'{output_path}/{file}'
        if os.path.exists(out_file):
            print(f'cleanup -- removing {out_file}')
            os.remove(out_file)

if __name__ == "__main__":
    prep_camtrap_dp()