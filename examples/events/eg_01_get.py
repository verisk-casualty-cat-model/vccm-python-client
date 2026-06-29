import json

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

# REQUIRED ACTION: Set event ref id
# Select event id
event_id = "example-event-reference"

# Get individual event content
event_full = client.events().get(event_id)
print(f"event: {json.dumps(event_full, sort_keys=True, indent=4)}")

# Get list of latest versions of events assets
latest_events_list = client.events().list()

for event in latest_events_list:
    # Get individual event content
    event_full = client.events().get(event["id"])
    print(f"event: {json.dumps(event_full, sort_keys=True, indent=4)}")
