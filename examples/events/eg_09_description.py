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

# REQUIRED ACTION: Set ref ids
# Select event id
event_id = "example-event-reference"

# Update event description
client.events().set_description(event_id, "new description")

# Get event description
updated_description = client.events().get_description(event_id)
print(f"event description: {updated_description}")

# Update event specific file description
client.events().set_payload_description(event_id, "new payload description")

# Get event specific file description
updated_payload_description = client.events().get_payload_description(event_id)
print(f"event payload description: {updated_payload_description}")
