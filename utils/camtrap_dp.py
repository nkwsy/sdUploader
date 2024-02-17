'''DRAFT - Setup camtrap-dp package'''
''' - from https://gitlab.com/oscf/camtrap-package '''

import requests
from camtrap_package import package
from dotenv import dotenv_values

def get_camtrap_schema():
    '''Get URLs for Camtrap-DP Schema files'''

    config = dotenv_values()
    camtrap_config = {}

    camtrap_config['base_url'] = f"{config["CAMTRAP_DP_BASE_URL"]}{config["CAMTRAP_DP_VERSION"]}"
    camtrap_config['deployment_schema_url'] = f"{camtrap_config['base_url']}{config["CAMTRAP_DEPLOYMENTS_SCHEMA"]}"
    camtrap_config['media_schema_url'] = f"{camtrap_config['base_url']}{config["CAMTRAP_MEDIA_SCHEMA"]}"
    camtrap_config['observations_schema_url'] = f"{camtrap_config['base_url']}{config["CAMTRAP_OBSERVATIONS_SCHEMA"]}"

    return camtrap_config


def main():
    # TODO - setup separate "get_camtrap_data()"
    # Prep Data
    # TODO - prep profile + sdUploader-inputs for datapackage.json
    # TODO - prep sdUploader + camera data for deployments.csv
    # TODO - prep camera image + exif data for media.csv
    # TODO - prep placeholder table for observations.csv

    camtrap_config = get_camtrap_schema()

    # # # EXAMPLE DATA: # # # # #

    CAMTRAP_DESCRIPTOR_URL = (
    f"{camtrap_config['base_url']}/example/datapackage.json"
    )
    CAMTRAP_DEPLOYMENTS_URL = (
    f"{camtrap_config['base_url']}/example/deployments.csv"
    )
    CAMTRAP_MEDIA_URL = f"{camtrap_config['base_url']}/example/media.csv"

    CAMTRAP_OBSERVATIONS_URL = (
    f"{camtrap_config['base_url']}/example/observations.csv"
    )

    # download example metadata and CSV resources
    descriptor = requests.get(CAMTRAP_DESCRIPTOR_URL).json()

    # drop coverages from descriptor for further tests
    cov_spatial = descriptor.pop("spatial")
    cov_temporal = descriptor.pop("temporal")
    cov_taxonomic = descriptor.pop("taxonomic")

    # # # # # # # # # # # # # # #


    # Setup output datapackage
    # TODO - replace EXAMPLES with real-data inputs

    dpack = package.CamTrapPackage(
    metadata=descriptor,
    deployments=CAMTRAP_DEPLOYMENTS_URL,
    media=CAMTRAP_MEDIA_URL,
    observations=CAMTRAP_OBSERVATIONS_URL,
    )

    # Validate Camtrap-DP
    # TODO - output validation log
    valid = dpack.validate_package()

    # Output Camtrap-DP
    # TODO - write out to appropriate place
    dpack.save()


if __name__ == "__main__":
    main()