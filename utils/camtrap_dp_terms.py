'''Write out a Camtrap-DP data package for a given SD card upload'''

from datetime import datetime
from dotenv import dotenv_values
from exiftool import ExifToolHelper
from pandas import DataFrame
import os, re, requests


config = dotenv_values()
camtrap_base_url = f'{config["CAMTRAP_BASE_URL"]}/{config["CAMTRAP_VERSION"]}'
camtrap_profile_url = f'{camtrap_base_url}{config["CAMTRAP_PROFILE"]}'
camtrap_deployment_schema_url = f'{camtrap_base_url}{config["CAMTRAP_DEPLOYMENTS_SCHEMA"]}'
camtrap_media_schema_url = f'{camtrap_base_url}{config["CAMTRAP_MEDIA_SCHEMA"]}'
camtrap_observations_schema_url = f'{camtrap_base_url}{config["CAMTRAP_OBSERVATIONS_SCHEMA"]}'


# Setup Deployment table/csv following Camtrap-DP Deployments schema
# # Referencing Trapper's deployments-related django serializer for a start (minus pandas, Django)
# # https://gitlab.com/trapper-project/trapper/-/blob/master/trapper/trapper-project/trapper/apps/geomap/serializers.py#LC237

# deployment_schema = Schema(requests.get(camtrap_deployment_schema_url).json())
# print(deployment_schema)

# def get_required_fields(schema:Schema=None) -> list:
#     '''Gets the required fields in a given schema (dict)'''
    
#     new_record = Resource()
#     # required_fields = []
#     i = 0
#     for field in schema.field_names: #  .get_field():
#         i += 1
#         # field_definition = schema.get_field(field)
#         # if field_definition['constraints']['required'] is True:
#         #     required_fields.append(field_definition)
#         new_record.fields(f"TEST_{i}")
    
#     return new_record

# new_deployment = get_required_fields(deployment_schema)
# print(new_deployment)


def get_camtrap_dp_profile() -> list:
    '''get profile from camtrap-dp repo'''

    # TODO - SETUP dynamic ref to camtrap profile
    camtrap_profile = requests.get(camtrap_profile_url).json()

    return camtrap_profile


def map_camtrap_dp_profile(camtrap_profile:str=None) -> list:

    dp_metadata = {
        'resources' : [],
        'profile' : camtrap_profile_url, 
        'name' : None, 
        'id' : None, 
        'created' : str(datetime.strftime(datetime.now(), '%Y-%m-%dT%H:%M:%SZ')), # TODO - input data
        'title' : None, 
        'contributors' : [],
        'description': None,
        'version' : config["CAMTRAP_VERSION"],
        'keywords' : [],
        'image' : None,
        'homepage' : None,
        'sources' : [],
        'bibliographicCitation': None,
        'project' : None,
        'spatial' : {},
        'temporal' : {
            'start' : None,
            'end' : None
        },
        'taxonomic' : []
        }
    
    return dp_metadata


def get_image_data(media_file_path:str=None) -> list:
    '''get a list of EXIF data for directory of images'''

    image_batch = os.listdir(media_file_path)

    image_info_list = []
    image_info = {}

    if len(image_batch) > 0:

        if re.findall('', image_batch[0].lower()) is not None:

            with ExifToolHelper() as et:
                # image = image_batch[0]
                for image in image_batch:
                    print(f'img ==== {image_batch[0]}')
                    image_info = et.get_tags(f'{media_file_path}/{image}', tags = None)
                    image_info_list.append(image_info)
    
    return image_info_list


def get_deployments_table_schema() -> list:
    '''get deployment-table-schema from camtrap-dp repo'''

    # TODO - add validation/tests for dynamic ref to camtrap-dp schema
    deployment_schema = requests.get(camtrap_deployment_schema_url).json()
    
    deployment_fields_raw = deployment_schema['fields']
    deployment_fields = [field['name'] for field in deployment_fields_raw]
    deployment_table = [dict.fromkeys(deployment_fields)]

    return deployment_table


def map_to_camtrap_deployment(deployment_table:list=None, 
                              input_data:list=None, 
                              media_file_path:str=None,
                              media_table:DataFrame=None) -> list:
    '''map input fields & files to camtrap-dp deployments table fields'''

    camera_info = get_image_data(media_file_path)[0]

    deploy_id = f"{input_data['location']}-{input_data['date']}-{input_data['camera']}"

    deployment_map = {
        "deploymentID" : deploy_id,
        "locationID" : '',  # TODO
        "locationName" : input_data['location'],
        "longitude" : None,    # lat/long
        "latitude" : None,     # lat/long
        "coordinateUncertainty" : None, # integer
        "deploymentStart" : media_table['timestamp'].min(),  # datetime - get min from media_table
        "deploymentEnd" : media_table['timestamp'].max(),    # datetime - get max from media_table
        "deploymentGroups" : None,
        "deploymentTags" : None,
        "deploymentComments" : None,
        "setupBy" : None,
        "cameraID" : None,  # from list
        "cameraModel" : f"{camera_info['Make']}-{camera_info['Model']}",   # concatenate {EXIF:Make}-{EXIF:Model}
        "cameraDelay" : None, # integer
        "cameraDepth" : None,   # float
        "cameraInterval" : None, # integer
        "cameraHeight" : None,   # float
        "cameraTilt" : None,     # float
        "cameraHeading" : None,
        "detectionDistance" : None,
        "timestampIssues" : None,
        "baitUse" : None,
        "featureType" : None,
        "habitat" : None
        }
    
    # validate static deployment mapping against current camtrap DP schema
    # TODO - split out mapping to config file to make this easier to maintain
    for key in deployment_map:
        if key not in deployment_table:
            raise ValueError(f'map_to_camtrap_deployment needs updated mapping: fields must be one of {deployment_table}')
    
    return deployment_map


def get_media_table_schema() -> list:
    '''get media-table-schema from camtrap-dp repo'''

    # TODO - add validation/tests for dynamic ref to camtrap-dp schema
    media_schema = requests.get(camtrap_media_schema_url).json()

    media_fields_raw = media_schema['fields']
    media_fields = [field['name'] for field in media_fields_raw]
    media_table = [dict.fromkeys(media_fields)]

    return media_table


def map_to_camtrap_media(media_table:list=None,
                         input_data:list=None, 
                         media_file_path:str=None) -> list:
    '''map input fields & files to camtrap-dp media table fields'''

    image_info = get_image_data(media_file_path)

    for image in image_info:

        image_create_date_raw = datetime.strptime(image_info[0]['EXIF:CreateDate'], '%Y:%m:%d %H:%M:%S')
        image_create_date_iso = datetime.strftime(image_create_date_raw, '%Y-%m-%dT%H:%M:%S-0600')

        deploy_id = f"{input_data['location']}-{input_data['date']}-{input_data['camera']}"
        media_id = re.sub(r'\\..+$', image['File:FileName'])

        media_map = {
            "mediaID" : media_id,  # Required
            "deploymentID" : deploy_id,  # Required
            "captureMethod" : 'activityDetection', # TODO - add to / pull from input_data
            "timestamp" : image_create_date_iso,  # Required (ISO 8601 ~ YYYY-MM-DDThh:mm:ss±hh:mm)
            "filePath" : image['File:Directory'],  # Required (relative within pkg, or URL)
            "filePublic" : True,  # Required (use 'false' if inaccessible/sensitive)
            "fileName" : image['File:FileName'],
            "fileMediatype" : image['File:MIMEType'],  # Required (^(image|video|audio)/.*$)
            "exifData" : image,
            "favorite" : None,
            "mediaComments" : None
        }

    # TODO - split out mapping to config file to make this easier to maintain
    for key in media_map:
        if key not in media_table:
            raise ValueError(f'map_to_camtrap_deployment needs updated mapping: fields must be one of {media_table}')

    return media_map


def get_observations_table_schema() -> list:
    '''get observations-table-schema from camtrap-dp repo'''

    # TODO - add validation/tests for dynamic ref to camtrap-dp schema
    obs_schema = requests.get(camtrap_observations_schema_url).json()

    obs_fields_raw = obs_schema['fields']
    
    obs_fields = [field['name'] for field in obs_fields_raw]

    obs_table = [dict.fromkeys(obs_fields)]

    # observation_fields = [
    #     "observationID",
    #     "deploymentID",
    #     "mediaID",
    #     "eventID",
    #     "eventStart",
    #     "eventEnd",
    #     "observationLevel",
    #     "observationType",
    #     "cameraSetupType",
    #     "taxonID",
    #     "scientificName",
    #     "count",
    #     "lifeStage",
    #     "sex",
    #     "behavior",
    #     "individualID",
    #     "individualPositionRadius",
    #     "individualPositionAngle",
    #     "individualSpeed",
    #     "bboxX",
    #     "bboxY",
    #     "bboxWidth",
    #     "bboxHeight",
    #     "classificationMethod",
    #     "classifiedBy",
    #     "classificationTimestamp",
    #     "classificationProbability",
    #     "observationTags",
    #     "observationComments"
    # ]

    return obs_table