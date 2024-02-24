'''DRAFT - Setup camtrap-dp package'''
''' - from https://gitlab.com/oscf/camtrap-package '''

import io, os, requests
import sdUploader as sd
from camtrap_package import package
from dotenv import dotenv_values
from exiftool import ExifToolHelper
from frictionless import Schema, Resource, Package
from pandas import DataFrame, read_csv


config = dotenv_values()
camtrap_config = {}

camtrap_config['base_url'] = f"{config['CAMTRAP_BASE_URL']}/{config['CAMTRAP_VERSION']}"
camtrap_config['deployment_schema_url'] = f"{camtrap_config['base_url']}{config['CAMTRAP_DEPLOYMENTS_SCHEMA']}"
camtrap_config['media_schema_url'] = f"{camtrap_config['base_url']}{config['CAMTRAP_MEDIA_SCHEMA']}"
camtrap_config['observations_schema_url'] = f"{camtrap_config['base_url']}{config['CAMTRAP_OBSERVATIONS_SCHEMA']}"



def get_camtrap_dp_data(sd_input:dict=None, camtrap_config:dict=None) -> dict:
    '''Get sdUploader inputs for datapackage.json'''

    # Package(resources=[Resource(name='deployments',
    #                             path=camtrap_config['deployment_schema_url'],
    #                             # format='csv',
    #                             )])
    
    descriptor = requests.get('https://raw.githubusercontent.com/tdwg/camtrap-dp/1.0-rc.1/example/datapackage.json').json()

    return descriptor


def get_deployments_data(file_path:str=None):
    '''Get sdUploader inputs for deployments.csv'''
    # Setup Deployment table/csv following Camtrap-DP Deployments schema
    # # Referencing Trapper's deployments-related django serializer for a start (minus pandas, Django)
    # # https://gitlab.com/trapper-project/trapper/-/blob/master/trapper/trapper-project/trapper/apps/geomap/serializers.py#LC237
    
    deployment_template = Schema(requests.get(camtrap_config['deployment_schema_url']).json())
    print(f'# # # # # # # #  deployment_template = {deployment_template}')
    
    source = Package(resources=[Resource(name='deployments', 
                                         path=camtrap_config['deployment_schema_url'],
                                         # format='csv',
                                         )])
    
    media_data = None
    image_batch = os.listdir(file_path)

    # sd.get_image_info('/Volumes/LUMIX/DCIM163_PANA')
    if image_batch is not None:

        camtrap_tags = ['Make', 'Model']
        media_raw_data = []
        image_row = None

        with ExifToolHelper() as et:
            for image in image_batch:
                print(f'img ==== {image}')
                image_row = {}
                for tags in et.get_tags(f'{file_path}/{image}', tags=camtrap_tags):
                    # for tags in et.get_tags("/Volumes/LUMIX/DCIM/162_PANA/P1620389.JPG", tags=camtrap_tags):
                    for k, v in tags.items():
                        # if v is not None:
                        image_row[k] = v
                media_raw_data.append(image_row)

        media_data = DataFrame(media_raw_data)
        print(f'media_data = {media_data}')

    # return media_data
    
    
    # target = transform(
    #     source,
    #     steps=[
    #         steps.resource_add(name='extra', descriptor={'path': 'transform.csv'}),
    #         ],
    #         )
    # print(f'# # # # # # # # source = {source}')
    # print(f'target = :...')
    # print(target.get_resource('extra').to_view())


def get_media_data(file_path:str=None):
    '''Get sdUploader + image inputs for media.csv'''
    
    media_data = None
    image_batch = os.listdir(file_path)

    # sd.get_image_info('/Volumes/LUMIX/DCIM163_PANA')
    if image_batch is not None:

        camtrap_tags = ['Make', 'Model']
        media_raw_data = []
        image_row = None

        with ExifToolHelper() as et:
            for image in image_batch:
                print(f'img ==== {image}')
                image_row = {}
                for tags in et.get_tags(f'{file_path}/{image}', tags=camtrap_tags):
                    # for tags in et.get_tags("/Volumes/LUMIX/DCIM/162_PANA/P1620389.JPG", tags=camtrap_tags):
                    for k, v in tags.items():
                        # if v is not None:
                        image_row[k] = v
                media_raw_data.append(image_row)

        media_data = DataFrame(media_raw_data)
        print(f'media_data = {media_data}')

    return media_data
    

def get_observations_data(file_path:str=None):
    '''Get inputs [if any] for observations.csv'''
    # TODO
    obs_raw_data = []

    obs_table = DataFrame(obs_raw_data)

    return obs_table


def prep_camtrap_dp(file_path_raw:sd.SdXDevice=None):
    '''Prep Data from SDuploader media and output it a camtrap-dp dataset'''

    if config['MODE'] == "TEST":
        file_path = config['TEST_SD_FILE_PATH']
    else: file_path = file_path_raw.mountpoint
    print(f'file path = = = {file_path}')

    # # TODO - Get profile + sdUploader-inputs for datapackage.json -- e.g.:
    # descriptor = get_camtrap_dp_data(file_path)
    
    # # TODO - Get sdUploader + camera data for deployments.csv -- e.g.:
    # deployments_table = get_deployments_data(file_path)
    
    # Get camera image + exif data for media.csv
    media_table = get_media_data(file_path)
    print(media_table)

    # Get placeholder table for observations.csv
    observations_table = get_observations_data(file_path)



    # # # EXAMPLE DATA based on gitlab camtrap-package 'Quickstart' : # # # # #
    # # #   https://gitlab.com/oscf/camtrap-package/-/blob/master/README.rst

    EXAMPLE_DESCRIPTOR_URL = (
    f"{camtrap_config['base_url']}/example/datapackage.json"
    )
    EXAMPLE_DEPLOYMENTS_URL = (
    f"{camtrap_config['base_url']}/example/deployments.csv"
    )
    print(f'deploys url = = = {EXAMPLE_DEPLOYMENTS_URL}')
    EXAMPLE_MEDIA_URL = f"{camtrap_config['base_url']}/example/media.csv"

    EXAMPLE_OBSERVATIONS_URL = (
    f"{camtrap_config['base_url']}/example/observations.csv"
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

    output_camtrap = package.CamTrapPackage(
    metadata = descriptor,
    deployments = deps, # CAMTRAP_DEPLOYMENTS_URL,  # deployments_table,  # 
    media = media_table, 
    observations = observations_table, #  obs, # CAMTRAP_OBSERVATIONS_URL,
    schema_version = config['CAMTRAP_VERSION']
    )

    # Validate Camtrap-DP
    # TODO - output validation log
    valid = output_camtrap.validate_package()
    print(f'# # # VALID Camtrap-dp? {valid}')

    # Output Camtrap-DP
    # TODO - write out to appropriate place
    output_result = output_camtrap.save(output_path="test_camtrap_output")
    print(f'# # # OUTPUT Camtrap-dp? {output_result}')


if __name__ == "__main__":
    prep_camtrap_dp()