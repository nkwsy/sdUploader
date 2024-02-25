'''Write out a Camtrap-DP data package for a given SD card upload'''

from datetime import datetime
from dotenv import dotenv_values
import requests

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

    dp_metadata = {
        'resources' : [],
        'profile' : camtrap_profile_url, 
        'name' : None, 
        'id' : None, 
        'created' : str(datetime.strftime(datetime.now(), '%Y-%m-%dT%H:%M:%SZ')), 
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


def get_deployments_table_schema() -> list:
    '''get deployment-table-schema from camtrap-dp repo'''

    # TODO - add validation/tests for dynamic ref to camtrap-dp schema
    deployment_schema = requests.get(camtrap_deployment_schema_url).json()

    deployment_fields_raw = deployment_schema['fields']
    
    deployment_fields = [field['name'] for field in deployment_fields_raw]

    deployment_table = [dict.fromkeys(deployment_fields)]

    # deployment_fields = [
    #     "deploymentID",
    #     "locationID",
    #     "locationName",
    #     "longitude",    # lat/long
    #     "latitude",     # lat/long
    #     "coordinateUncertainty", # integer
    #     "start",  # datetime
    #     "end",    # datetime
    #     "setupBy",
    #     "cameraID",     # from list
    #     "cameraModel",  # from list
    #     "cameraInterval", # integer
    #     "cameraHeight",   # float
    #     "cameraTilt",     # float
    #     "cameraHeading",
    #     "timestampIssues",
    #     "baitUse",
    #     "session",
    #     "array",
    #     "featureType",
    #     "habitat",
    #     "tags",
    #     "comments",
    #     "_id",
    # ]

    return deployment_table

def get_media_table_schema() -> list:
    '''get media-table-schema from camtrap-dp repo'''

    # TODO - add validation/tests for dynamic ref to camtrap-dp schema
    media_schema = requests.get(camtrap_media_schema_url).json()

    media_fields_raw = media_schema['fields']
    
    media_fields = [field['name'] for field in media_fields_raw]
    
    media_table = [dict.fromkeys(media_fields)]

    # media_fields = [
    #     "mediaID",  # Required
    #     "deploymentID",  # Required
    #     "captureMethod",
    #     "timestamp",  # Required (ISO 8601 ~ YYYY-MM-DDThh:mm:ss±hh:mm)
    #     "filePath",  # Required (relative within pkg, or URL)
    #     "filePublic",  # Required (use 'false' if inaccessible/sensitive)
    #     "fileName",
    #     "fileMediatype",  # Required (^(image|video|audio)/.*$)
    #     "exifData",
    #     "favorite",
    #     "mediaComments"
    # ]

    return media_table


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