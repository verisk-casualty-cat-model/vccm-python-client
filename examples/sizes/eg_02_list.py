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

# Get list of latest versions of events assets
latest_sizes_list = client.sizes().list()
for sizes in latest_sizes_list:
    print(f"sizes (latest): {json.dumps(sizes, sort_keys=True, indent=4)}")

# Get list of all versions of events assets
all_sizes_list = client.sizes().list(latest=False)
for sizes in all_sizes_list:
    print(f"sizes: {json.dumps(sizes, sort_keys=True, indent=4)}")
