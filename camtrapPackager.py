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

    # Package(resources=[Resource(name='deployments',
    #                             path=camtrap_config_urls['deployments'],
    #                             # format='csv',
    #                             )])
    
    # descriptor = requests.get('https://raw.githubusercontent.com/tdwg/camtrap-dp/1.0-rc.1/example/datapackage.json').json()

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
    
    descriptor = Package('datapackage.json')
    
    descriptor.profile = camtrap_config_urls['profile_url']
    descriptor.name = 'test-project-name-with-location-and-id', # TODO - replace with input
    descriptor.created = data_entry_info['date']
    descriptor.description = ''
    descriptor.keywords = ''
    descriptor.image = ''
    descriptor.homepage = 'https://www.urbanriv.org/'
    descriptor.licenses = [
        {
            "name": "CC0-1.0",  # TODO - confirm w/ UR
            "scope": "data"
        },
        {
            "path": "http://creativecommons.org/licenses/by/4.0/",  # TODO - confirm w/ UR
            "scope": "media"
        }
        ]

    descriptor.contributors = [
        # NOTE - maybe best to split hardcoded parts out to a config file
        {
            'title' : data_entry_info['photographer'],
            'role:' : 'contributor',
            'organization' : data_entry_info['photographer']
        },
        {
            "title": "Nick Wesley",
            "email": "", # TODO - confirm w/ NW
            "path": "",  # TODO - setup/add https://orcid.org w/ NW
            "role": "contact",
            "organization": "Urban Rivers"
        },
        {
            "title": "Urban Rivers",
            "path": "https://www.urbanriv.org",
            "role": "rightsHolder"
        },
        {
            "title": "Urban Rivers",
            "path": "https://www.urbanriv.org", 
            "role": "publisher"
        }
        ]
    
    descriptor.project = {
        'title' : 'Urban Rivers - Camera Trap Project 2024',  # TODO - confirm project-info w/ UR
        'id' : '',
        'acronym' : '',
        'description' : '',
        'path' : 'https://www.urbanriv.org',
        'samplingDesign' : 'opportunistic',
        'captureMethod' : ['activityDetection', 'timeLapse'],
        'individualAnimals' : False,
        'observationLevel' : ['media', 'event']
    }

    descriptor.resources = resources_prepped

    return descriptor


def setup_camtrap_resource(dataset:DataFrame=None, 
                           data_name:str=None, 
                           camtrap_config_urls:dict=camtrap_config_urls) -> Resource:
    '''setup an input table as a resource for a frictionless package'''

    valid_data_name = ['deployments', 'media', 'observations']

    if data_name not in valid_data_name:
        raise ValueError(f'setup_camtrap_resource: data_name must be one of {valid_data_name}')
    
    data_path = f'{data_name}.csv'
    dataset.to_csv(path = data_path, index = False)

    resource = Resource(path = data_path)
    resource.name = data_name
    resource.profile = 'tabular-data-resource',
    resource.schema = camtrap_config_urls[data_name]

    return resource


def setup_datasets(file_path:str=None, input_data:dict=None) -> list:
    '''Get sdUploader + image inputs for deployments, media, observations'''
    
    media_data = None
    image_batch = os.listdir(file_path)

    prepped_datasets_as_resources = []

    # sd.get_image_info('/Volumes/LUMIX/DCIM163_PANA')
    if image_batch is not None:

        camtrap_tags = ['Make', 'Model']
        media_raw_data = []
        image_row = None
        media_row_blank = uc.get_media_table_schema()
        media_row = None

        with ExifToolHelper() as et:
            for image in image_batch:
                print(f'img ==== {image}')

                image_row = {}
                for tags in et.get_tags(f'{file_path}/{image}', tags=camtrap_tags):
                    # for tags in et.get_tags("/Volumes/LUMIX/DCIM/162_PANA/P1620389.JPG", tags=camtrap_tags):
                    for k, v in tags.items():
                        # if v is not None:
                        image_row[k] = v

                
                media_row = {}
                media_row = uc.map_to_camtrap_media(media_table=media_row_blank, input_data=input_data)
                media_raw_data.append(media_row)

        media_data = DataFrame(media_raw_data)
        media_resource = setup_camtrap_resource(dataset = media_data,
                                                data_name = 'media')
        
        print(f'media_data = {media_data}')

        prepped_datasets_as_resources.append(media_resource)

    return prepped_datasets_as_resources
    

# def get_observations_data(file_path:str=None):
#     '''Get inputs [if any] for observations.csv'''
#     # TODO - read & map observation data from input file_path

#     observation_terms = uc.get_observations_table_schema()
#     obs_raw_data = [dict.fromkeys(observation_terms)]
#     obs_table = DataFrame(obs_raw_data)

#     return obs_table


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
        file_path = file_path_raw.mountpoint
        data_entry_info = sd_data_entry_info
        
    print(f'file path = = = {file_path}')

    # # TODO - Get profile + sdUploader-inputs for datapackage.json -- e.g.:
    # descriptor = get_camtrap_dp_data(file_path)

    
    # TODO - Get sdUploader + camera data for deployments.csv -- e.g.:
    deployments_table = uc.get_deployments_table_schema()  # get_deployments_data(file_path)
    
    # Get camera image + exif data for media.csv
    # media_table = setup_media_dataset(file_path)
    media_table = uc.get_media_table_schema()
    print(media_table)

    # Get placeholder table for observations.csv
    # observations_table = get_observations_data(file_path)
    observations_table = uc.get_observations_table_schema()



    # # # EXAMPLE DATA based on gitlab camtrap-package 'Quickstart' : # # # # #
    # # #   https://gitlab.com/oscf/camtrap-package/-/blob/master/README.rst

    EXAMPLE_DESCRIPTOR_URL = (
    f"{camtrap_config_urls['base_url']}/example/datapackage.json"
    )
    EXAMPLE_DEPLOYMENTS_URL = (
    f"{camtrap_config_urls['base_url']}/example/deployments.csv"
    )
    print(f'deploys url = = = {EXAMPLE_DEPLOYMENTS_URL}')
    EXAMPLE_MEDIA_URL = f"{camtrap_config_urls['base_url']}/example/media.csv"

    EXAMPLE_OBSERVATIONS_URL = (
    f"{camtrap_config_urls['base_url']}/example/observations.csv"
    )

    # download example metadata and CSV resources
    descriptor = requests.get(EXAMPLE_DESCRIPTOR_URL).json()

    deps_raw=requests.get(EXAMPLE_DEPLOYMENTS_URL).content
    print(f'deployments_raw = = = {deps_raw}')
    deps = read_csv(io.StringIO(deps_raw.decode('utf-8')))
    print(f'deps = = = {deps}')

    # media_raw=requests.get(EXAMPLE_MEDIA_URL).content
    # meds = pd.read_csv(io.StringIO(media_raw.decode('utf-8')))

    obs_raw=requests.get(EXAMPLE_OBSERVATIONS_URL).content
    obs = read_csv(io.StringIO(obs_raw.decode('utf-8')))

    # drop coverages from descriptor for further tests
    cov_spatial = descriptor.pop("spatial")
    cov_temporal = descriptor.pop("temporal")
    cov_taxonomic = descriptor.pop("taxonomic")

    # # # # # # # # # # # # # # #


    # Setup output datapackage
    # TODO - replace metadata/descriptor example with real-data inputs
    # TODO - replace deployments example with real-data inputs

    # output_camtrap = package.CamTrapPackage(
    #     metadata = descriptor,
    #     deployments = deployments_table, # CAMTRAP_DEPLOYMENTS_URL,  #  deps
    #     media = media_table, 
    #     observations = observations_table, #  obs, # CAMTRAP_OBSERVATIONS_URL,
    #     schema_version = config['CAMTRAP_VERSION']
    # )


    # output_camtrap = Package(
    #     descriptor = 
    #     resources = [
    #         Resource(name = 'deployments',
    #                  path = '',
    #                  profile = 'tabular-data-resource',
    #                  schema = camtrap_config_urls['deployments']
    #                  )])

    data_resources = setup_datasets(file_path, data_entry_info)
        
    output_camtrap = get_camtrap_dp_metadata(
        file_path_raw = file_path_raw, 
        sd_data_entry_info = data_entry_info,
        camtrap_config_urls = camtrap_config_urls,
        resources_prepped = data_resources
        )

    # Validate Camtrap-DP
    # TODO - output validation log
    valid = output_camtrap.validate_package()
    print(f'# # # VALID Camtrap-dp? {valid}')

    # Alternatively, validate using frictionless
    valid_frictionless = validate(output_camtrap)
    print(f'# # # VALID Camtrap-dp? {valid}')

    # Output Camtrap-DP
    # TODO - write out to appropriate place
    output_result = output_camtrap.save(output_path="test_camtrap_output")
    print(f'# # # OUTPUT Camtrap-dp? {output_result}')


if __name__ == "__main__":
    prep_camtrap_dp()