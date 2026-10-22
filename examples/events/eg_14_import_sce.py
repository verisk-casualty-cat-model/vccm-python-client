# Import an event library export (.sce, up to 40 MB).
# Events are saved at the paths recorded in the export; an event whose path already exists is rejected.
from api_call.client import APIClient
from auth.okta_auth import Auth


def main():
    # Option 1: Fill in your credentials directly
    auth_settings = {}

    # Option 2: Load credentials from a .env file (see .env.example)
    # from dotenv import load_dotenv
    # import os
    # load_dotenv()
    # auth_settings = {
    #     "client_id": os.getenv("CLIENT_ID"),
    #     "client_secret": os.getenv("CLIENT_SECRET"),
    #     "authorization_url": os.getenv("AUTHORIZATION_URL"),
    #     "token_url": os.getenv("TOKEN_URL"),
    #     "base_uri": os.getenv("BASE_URI"),
    # }

    # Perform authentication
    auth = Auth(tenant="workspace1", role="basic", settings=auth_settings)

    # Create the new client - it will execute the required API actions
    client = APIClient(auth=auth)

    # REQUIRED ACTION: Set the .sce file
    sce_file = "path/to/events.sce"

    activity = client.event_import().import_sce(sce_file, wait=True)
    print(f"Activity {activity.activityId}: {activity.status.value}")
    print(activity.activityDetails)

    # .sce imports produce no error CSV - rejected events are listed in the import log
    log = client.activity().import_log(activity.activityId)
    if log:
        print(log)


if __name__ == "__main__":
    main()
