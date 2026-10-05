# Export events as a bulk import CSV. The file can be edited and imported back with eg_13_bulk_import_csv.py.
from api_call.arium.model.activity import ActivityStatus
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

    # REQUIRED ACTION: Set the folder to export
    folder_name = "Imported events"
    asset_ids = [e["id"] for e in client.events().list() if e["name"].startswith(folder_name + "/")]

    activity = client.event_import().export_csv(asset_ids, wait=True)
    print(f"Activity {activity.activityId}: {activity.status.value}")

    if activity.status in (ActivityStatus.COMPLETED, ActivityStatus.COMPLETED_WITH_EXCEPTIONS):
        # completedWithExceptions: the file is missing some events, the reasons are in activity.errors
        client.activity().export_file(activity.activityId, file_name="events.csv")
        print("Exported to events.csv")
    if activity.errors:
        print(activity.errors)


if __name__ == "__main__":
    main()
