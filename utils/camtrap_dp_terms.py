'''Write out a Camtrap-DP data package for a given SD card upload'''

from datetime import datetime
from dotenv import dotenv_values
from exiftool import ExifToolHelper
from pandas import DataFrame
import json, os, re, requests, uuid, zipfile


config = dotenv_values()
camtrap_base_url = f'{config["CAMTRAP_BASE_URL"]}/{config["CAMTRAP_VERSION"]}'
camtrap_profile_url = f'{camtrap_base_url}{config["CAMTRAP_PROFILE"]}'
camtrap_deployment_schema_url = f'{camtrap_base_url}{config["CAMTRAP_DEPLOYMENTS_SCHEMA"]}'
camtrap_media_schema_url = f'{camtrap_base_url}{config["CAMTRAP_MEDIA_SCHEMA"]}'
camtrap_observations_schema_url = f'{camtrap_base_url}{config["CAMTRAP_OBSERVATIONS_SCHEMA"]}'


def get_camtrap_dp_profile(camtrap_profile_url) -> list:
    '''get profile from camtrap-dp repo'''

    # TODO - SETUP dynamic ref to camtrap profile
    camtrap_profile = requests.get(camtrap_profile_url).json()

    return camtrap_profile

def get_sduploader_input() -> dict:
    '''get input data entered by camera crew when offloading SD cards'''

    # TODO - Determine how/where sdUploader should output that data

    if config['MODE'] == "TEST":
        data_entry_info = {
            'photographer':'test-PHOTOGRAPHER',
            'camera':'test-CAMERA', 
            'date': datetime.strftime(datetime.now(), '%Y-%m-%dT%H:%M:%S-06:00'), 
            'location': 'test-LOCATION', 
            'notes': 'test-NOTES'
            }
    
    return data_entry_info

def map_camtrap_dp_ur_profile(
        camtrap_profile:str=camtrap_profile_url,
        generate_uuid4:bool=True
        ) -> dict:
    '''map camera crew's input data to camtrap-dp metadata'''

    dp_metadata_dict = get_camtrap_dp_profile(camtrap_profile_url)

    data_entry_info = get_sduploader_input()

    if generate_uuid4 == True:
        dp_id = str(uuid.uuid4())
        print(f'# # # # # # DP_ID = {dp_id}')
    
    dp_name_raw = f"{data_entry_info['location']}-{data_entry_info['camera']}-{data_entry_info['date']}".lower()
    dp_name_prepped = re.sub(r'[^a-z0-9\-._/]', '-', dp_name_raw)
    dp_title = f"Urban Rivers - {data_entry_info['camera']} at {data_entry_info['location']} on {data_entry_info['date']}"

    dp_metadata_mapped = {
        'resources' : [],
        'profile' : camtrap_profile,
        'name' : dp_name_prepped,
        'id' : dp_id,
        'created' : datetime.strftime(datetime.now(), '%Y-%m-%dT%H:%M:%SZ'),
        'title' : dp_title,
        'contributors' : [
            {
                'title' : data_entry_info['photographer'],
                'role:' : 'contributor',
                'organization' : data_entry_info['photographer']
            },
            {
                "title": "Nick Wesley",
                "email": "team@urbanriv.org",
                "path": "https://orcid.org/0000-0000",  # TODO - replace
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
            ],
        'description': str(),
        'version' : config["CAMTRAP_VERSION"],
        'keywords' : ['Urban Rivers', 'urban wildlife', 'camera traps'],
        'image' : str(),
        'homepage' : 'https://www.urbanriv.org',
        'sources' : [],
        'bibliographicCitation': str(),
        'licenses': [
            # TODO - confirm w/ UR
            {
                "name": "CC0-1.0",
                "scope": "data"
            },
            {
                "path": "http://creativecommons.org/licenses/by/4.0/",
                "scope": "media"
            }
            ],
        'project' : {
            'title' : 'Urban Rivers - Camera Trap Project 2024',
            'id' : dp_id,
            'acronym' : '',
            'description' : '',
            'path' : 'https://www.urbanriv.org',
            'samplingDesign' : 'opportunistic',
            'captureMethod' : ['activityDetection', 'timeLapse'],
            'individualAnimals' : False,
            'observationLevel' : ['media', 'event']
        },
        'spatial' : {
            'type' : "Point",
            'coordinates' : [
                41.907144,  # TODO - check for camera metadata?
                -87.652254
            ]
        },
        'temporal' : {
            'start' : "",
            'end' : ""
        },
        'taxonomic' : []
        }
    
    # validate static deployment mapping against current camtrap DP schema
    # TODO - split out mapping to config file to make this easier to maintain
    for key in dp_metadata_mapped.keys():
        if key not in dp_metadata_dict['allOf'][1]['properties']:
            raise ValueError(f"map_camtrap_dp_ur_profile needs updated mapping with these fields: {dp_metadata_dict['allOf'][1]['required']}")

    
    return dp_metadata_mapped


def get_image_data(media_file_path:str=None) -> list:
    '''get a list of EXIF data for directory of images'''

    image_info_list = []
    image_info = {}

    with ExifToolHelper() as et:
        # image = image_batch[0]
            image_info = et.get_tags(f'{media_file_path}', tags = None)
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

    first_image_info = get_image_data(media_file_path)[0][0]
    print(f'map-to-camtraps first_image_info = = {first_image_info}')

    deploy_id = f"{input_data['location']}-{input_data['date']}-{input_data['camera']}"

    deployment_map = {
        "deploymentID" : deploy_id,
        "locationID" : '',  # TODO
        "locationName" : input_data['location'],
        "longitude" : None,    # lat/long
        "latitude" : None,     # lat/long
        "coordinateUncertainty" : None, # integer
        "deploymentStart" : media_table['timestamp'].min(),
        "deploymentEnd" : media_table['timestamp'].max(),
        "deploymentGroups" : None,
        "deploymentTags" : None,
        "deploymentComments" : None,
        "setupBy" : None,
        "cameraID" : None,  # from list
        "cameraModel" : f"{first_image_info['EXIF:Make']}-{first_image_info['EXIF:Model']}",   # concatenate {EXIF:Make}-{EXIF:Model}
        "cameraDelay" : None, # integer
        "cameraDepth" : None,   # float
        # "cameraInterval" : None, # integer
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
    for key in deployment_map.keys():
        if key not in deployment_table[0]:
            raise ValueError(f'map_to_camtrap_deployment needs updated mapping: fields must be one of {deployment_table[0].keys()}')

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

    image_info = get_image_data(media_file_path)[0]

    for image in image_info:

        image_create_date_raw = datetime.strptime(image['EXIF:CreateDate'], '%Y:%m:%d %H:%M:%S')
        image_create_date_iso = datetime.strftime(image_create_date_raw, '%Y-%m-%dT%H:%M:%S-0600')

        deploy_id = f"{input_data['location']}-{input_data['date']}-{input_data['camera']}"
        media_id = re.sub(r'\..+$', '', image['File:FileName'])

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

        print(f'row summary -- mediaID: {media_map["mediaID"]} | timestamp: {media_map["timestamp"]}')
        # print(image)

    # TODO - split out mapping to config file to make this easier to maintain

    for key in media_map.keys():
        if key not in media_table[0]:
            raise ValueError(f'map_to_camtrap_deployment needs updated mapping: fields must be one of {media_table[0].keys()}')

    return media_map


def get_observations_table_schema() -> list:
    '''get observations-table-schema from camtrap-dp repo'''

    # TODO - add validation/tests for dynamic ref to camtrap-dp schema
    obs_schema = requests.get(camtrap_observations_schema_url).json()

    obs_fields_raw = obs_schema['fields']
    obs_fields = [field['name'] for field in obs_fields_raw]
    obs_table = [dict.fromkeys(obs_fields)]

    return obs_table


def map_to_camtrap_observations(observations_table:list=None, 
                                input_data:list=None, 
                                # media_file_path:str=None,
                                media_table:DataFrame=None) -> list:
    '''map input fields & files to camtrap-dp observations table fields'''

    # first_image_info = get_image_data(media_file_path)[0]

    deploy_id = f"{input_data['location']}-{input_data['date']}-{input_data['camera']}"

    obs_map = {
        "observationID" : None,
        "deploymentID" : deploy_id,
        "mediaID" : None,  #  media_table['mediaID'], # TODO - fix
        "eventID" : None,
        "eventStart" : None,
        "eventEnd" : None,
        "observationLevel" : None,
        "observationType" : None,
        "cameraSetupType" : None,
        # "taxonID" : None,
        "scientificName" : None,
        "count" : None,
        "lifeStage" : None,
        "sex" : None,
        "behavior" : None,
        "individualID" : None,
        "individualPositionRadius" : None,
        "individualPositionAngle" : None,
        "individualSpeed" : None,
        "bboxX" : None,
        "bboxY" : None,
        "bboxWidth" : None,
        "bboxHeight" : None,
        "classificationMethod" : None,
        "classifiedBy" : None,
        "classificationTimestamp" : None,
        "classificationProbability" : None,
        "observationTags" : None,
        "observationComments" : None
        }
    
    # validate static deployment mapping against current camtrap DP schema
    # TODO - split out mapping to config file to make this easier to maintain
    for key in obs_map:
        if key not in observations_table[0].keys():
            raise ValueError(f'map_to_camtrap_observations needs updated mapping: fields must be one of {observations_table[0].keys()}')
    
    return obs_map

class CamtrapPackage():
    '''
    Sets up a frictionless data package following the camtrap-dp exchange format. [Hopefully.]
    - https://tdwg.github.io/camtrap-dp
    - https://specs.frictionlessdata.io/data-package
    '''

    def __init__(
            self, 
            # camtrap_config_urls:dict=None, 
            data_entry_info:dict=None,
            profile_dict:dict=None,
            resources_prepped:list=None,
            media_table:list=None
            ) -> None:
        
        if profile_dict is None:
            profile_dict = map_camtrap_dp_ur_profile()

        self.id = profile_dict['id']
        self.profile = profile_dict['profile']  # camtrap_config_urls['profile_url']
        
        self.name = profile_dict['name'] # TODO - replace with input
        self.title = profile_dict['title'] # TODO - replace with input
        self.created = profile_dict['created'] 
        self.description = profile_dict['description']
        self.version = profile_dict['version']
        self.keywords = profile_dict['keywords']
        self.image = profile_dict['image']
        self.homepage = profile_dict['homepage']
        self.sources = profile_dict['sources']
        self.bibliographicCitation = profile_dict['bibliographicCitation']
        self.licenses = profile_dict['licenses']

        self.contributors = profile_dict['contributors']
        self.project = profile_dict['project']

        self.spatial = profile_dict['spatial']
        self.temporal = get_temporal_data(media_table)
        self.taxonomic = profile_dict['taxonomic']

        self.resources = resources_prepped

def get_temporal_data(media_table):

    start = media_table['timestamp'].min()
    end = media_table['timestamp'].max()

    temporal_data = {
        'start' : start,
        'end' : end
    }

    return temporal_data

def __str__():
    pass

def save(
        package_metadata=None,
        output_path=None,
        sort_keys=False,
        make_archive=True,
    ):
    '''
    Output a camtrap-dp package as a zipped directory
    Based on camtrap-package's 'save' function
    - https://gitlab.com/oscf/camtrap-package/-/blame/master/src/camtrap_package/package.py?ref_type=heads#L301
    '''

    # mkdir if output_path does not exist
    if output_path:
        os.makedirs(output_path, exist_ok=True)
        # os.chdir(output_path)
    else:
        output_path = ''

    descriptor = package_metadata

    # write descriptor
    with open(f"{output_path}/datapackage.json", "w") as _file:
        json.dump(descriptor.__dict__, _file, indent=4, sort_keys=sort_keys)

    # create zipfile (if requested)
    zip_name = f"{output_path}/camtrap-dp-{descriptor.id}.zip"
    if make_archive:
        with zipfile.ZipFile(zip_name, "w") as zipf:
            zipf.write(
                f"{output_path}/deployments.csv",
                arcname="deployments.csv",
            )
            zipf.write(
                f"{output_path}/media.csv", 
                arcname="media.csv"
            )
            zipf.write(
                f"{output_path}/observations.csv",
                arcname="observations.csv",
            )
            zipf.write(
                f"{output_path}/datapackage.json",
                arcname="datapackage.json"
                )
    return True
