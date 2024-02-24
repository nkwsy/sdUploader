'''Write out a Camtrap-DP data package for a given SD card upload'''

from frictionless import Schema, Resource, resources, transform, steps
from dotenv import dotenv_values
import requests

config = dotenv_values()
camtrap_base_url = f'{config["CAMTRAP_DP_BASE_URL"]}{config["CAMTRAP_DP_VERSION"]}'
camtrap_deployment_schema_url = f'{camtrap_base_url}{config["CAMTRAP_DEPLOYMENTS_SCHEMA"]}'
camtrap_media_schema_url = f'{camtrap_base_url}{config["CAMTRAP_MEDIA_SCHEMA"]}'
camtrap_observations_schema_url = f'{camtrap_base_url}{config["CAMTRAP_OBSERVATIONS_SCHEMA"]}'


# Setup Deployment table/csv following Camtrap-DP Deployments schema
# # Referencing Trapper's deployments-related django serializer for a start (minus pandas, Django)
# # https://gitlab.com/trapper-project/trapper/-/blob/master/trapper/trapper-project/trapper/apps/geomap/serializers.py#LC237
deployment_schema = Schema(requests.get(camtrap_deployment_schema_url).json())
print(deployment_schema)

def get_required_fields(schema:Schema=None) -> list:
    '''Gets the required fields in a given schema (dict)'''
    
    new_record = Resource()
    # required_fields = []
    i = 0
    for field in schema.field_names: #  .get_field():
        i += 1
        # field_definition = schema.get_field(field)
        # if field_definition['constraints']['required'] is True:
        #     required_fields.append(field_definition)
        new_record.fields(f"TEST_{i}")
    
    return new_record

new_deployment = get_required_fields(deployment_schema)
print("# # # # # # # # # #")
print(new_deployment)

def get_deployments_table_schema() -> list:
    '''get deployment-table-schema from camtrap-dp repo'''

    # TODO - replace with more dynamic ref to camtrap-dp schema
    deployment_terms = [
        "deploymentID",
        "locationID",
        "locationName",
        "longitude",    # lat/long
        "latitude",     # lat/long
        "coordinateUncertainty", # integer
        "start",  # datetime
        "end",    # datetime
        "setupBy",
        "cameraID",     # from list
        "cameraModel",  # from list
        "cameraInterval", # integer
        "cameraHeight",   # float
        "cameraTilt",     # float
        "cameraHeading",
        "timestampIssues",
        "baitUse",
        "session",
        "array",
        "featureType",
        "habitat",
        "tags",
        "comments",
        "_id",
    ]
    return deployment_terms

def get_media_table_schema() -> list:
    '''get media-table-schema from camtrap-dp repo'''

    # TODO - replace with more dynamic ref to camtrap-dp schema
    media_terms = [
        "mediaID",
        "deploymentID",
        "captureMethod",
        "timestamp",
        "filePath",
        "filePublic",
        "fileName",
        "fileMediatype",
        "exifData",
        "favorite",
        "mediaComments"
    ]

    return media_terms

def get_observations_table_schema():
    '''get observations-table-schema from camtrap-dp repo'''

    # TODO - replace with more dynamic ref to camtrap-dp schema
    observation_terms = [
        "observationID",
        "deploymentID",
        "mediaID",
        "eventID",
        "eventStart",
        "eventEnd",
        "observationLevel",
        "observationType",
        "cameraSetupType",
        "taxonID",
        "scientificName",
        "count",
        "lifeStage",
        "sex",
        "behavior",
        "individualID",
        "individualPositionRadius",
        "individualPositionAngle",
        "individualSpeed",
        "bboxX",
        "bboxY",
        "bboxWidth",
        "bboxHeight",
        "classificationMethod",
        "classifiedBy",
        "classificationTimestamp",
        "classificationProbability",
        "observationTags",
        "observationComments"
    ]

    return observation_terms