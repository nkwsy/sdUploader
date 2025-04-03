from loguru import logger
import os
import sys

import requests
from dotenv import load_dotenv
from datetime import datetime
import jsonpickle



load_dotenv()
WILDMILE_API_URL = os.getenv("WILDMILE_API_URL")
DEPLOYMENT_API = f"{WILDMILE_API_URL}/api/cameratrap/deployments"


# sd_uploader to wildmile schema decoder ring:
# cameraid = cameraId.name
# location = location.locationName
# date = deploymentEnd
class Deployment:
    def __init__(self, *, cameraid, location, deployment_start, deployment_end):
        self.cameraid = cameraid
        self.location = location
        self.deployment_start = deployment_start
        self.deployment_end = deployment_end


def fetch_camera_deployments():
    try:
        resp = requests.get(url=DEPLOYMENT_API)
        data = resp.json()

        deployment_list = []
        for deployment in data:
            logger.debug(f"Deployment: {deployment}")
            deployment_list.append(
                Deployment(
                    cameraid=deployment["cameraId"]["name"],
                    location=deployment["locationId"]["locationName"] if "locationId" in deployment else None,
                    deployment_start=datetime.fromisoformat(deployment["deploymentStart"]),
                    deployment_end=datetime.fromisoformat(deployment["deploymentEnd"]) if "deploymentEnd" in deployment else None
                )
            )
        sorted_deployments = sorted(deployment_list, key=lambda x: x.deployment_start)

        deployment_map = {}
        for deployment in sorted_deployments:
            deployment_map[deployment.cameraid] = deployment

        return deployment_map


    except Exception as e:
        msg = f"Error fetching camera ids: {str(e)}"
        logger.error(msg)
        raise Exception(msg) from e






if __name__ == "__main__":
    logger.configure(handlers=[{"sink": sys.stdout, "level": "DEBUG"}])
    deployment_map = fetch_camera_deployments()

    jsonpickle.set_encoder_options('json', sort_keys=True, indent=2)
    print(jsonpickle.encode(deployment_map, unpicklable=False))