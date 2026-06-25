import os

from api_call.client import APIClient
from auth.okta_auth import Auth

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


# Create new client
auth = Auth(tenant="workspace1", role="basic", settings=auth_settings)
client = APIClient(auth=auth)

# REQUIRED ACTION: Set output folder path
output_folder = "data_download/"
events = {p["name"]: p["id"] for p in client.events().list()}

for event_name, event_id in events.items():
    event_data = client.events().get_data(event_id)
    try:
        filepath = output_folder + event_name
        filepath = filepath.strip()
        if not os.path.exists(os.path.dirname(filepath)):
            os.makedirs(os.path.dirname(filepath), exist_ok=True)

        with open(filepath + ".json", "w", encoding="utf-8") as f:
            print(f"Saving {event_name} ({event_id})...")
            f.write(event_data.decode("utf-8"))
    except Exception as e:
        print()

print("Finished bulk download.")
