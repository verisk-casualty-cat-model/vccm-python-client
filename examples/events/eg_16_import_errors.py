# Download the results of a finished bulk event import.
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

    # TODO - provide activity id of a bulk event import
    activity_id = "<your_activity_id>"
    activity = client.activity().get(activity_id)
    print(f"{activity.name}: {activity.status.value}")
    print(activity.activityDetails)

    # Rejected rows as written in the source CSV, with Source Row, Event, Status, Field, Invalid Value
    # and Error Reason appended. None when nothing was rejected.
    errors = client.activity().error_csv(activity_id)
    if errors:
        with open("errors.csv", "wb") as f:
            f.write(errors.getbuffer())

    # Only the appended columns
    errors_only = client.activity().error_csv(activity_id, errors_only=True)
    if errors_only:
        print(errors_only.getvalue().decode("utf-8"))

    # Plain text log: rejected events with the reasons and the created events
    log = client.activity().import_log(activity_id)
    if log:
        print(log)


if __name__ == "__main__":
    main()
