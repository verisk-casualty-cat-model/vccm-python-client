# Bulk import events from a CSV built on the template (see eg_15_import_template.py).
# The import runs as an activity; files over 4 MB are uploaded to S3 first, up to 100 MB.
#
# Invalid rows are handled by the workspace's import policy:
#   CONTINUE_WHEN_ERROR (default) - valid events are imported, the activity ends completedWithExceptions
#   STOP_WHEN_ERROR               - nothing is imported, the activity ends failed
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

    # REQUIRED ACTION: Set the CSV file and a new folder for the imported events
    csv_file = "path/to/events.csv"
    folder_name = "Imported events"

    activity = client.event_import().import_csv(csv_file, folder_name=folder_name, wait=True)
    print(f"Activity {activity.activityId}: {activity.status.value}")
    print(activity.activityDetails)

    if activity.status == ActivityStatus.COMPLETED_WITH_EXCEPTIONS and activity.errorCsvKey:
        # Rejected rows as written in the CSV, with the reason for each - fix them and import again
        errors = client.activity().error_csv(activity.activityId)
        with open("events_errors.csv", "wb") as f:
            f.write(errors.getbuffer())
        print("Rejected rows saved to events_errors.csv")
    elif activity.status == ActivityStatus.FAILED:
        print(activity.errors)
        print(client.activity().import_log(activity.activityId))


if __name__ == "__main__":
    main()
