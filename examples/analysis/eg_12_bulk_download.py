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

# REQUIRED ACTION: Set path to folder where downloaded assets should be stored
output_folder = "data_download/"
analysis = {p["name"]: p["id"] for p in client.analysis().list()}

if not os.path.exists(output_folder):
    os.makedirs(output_folder)

for analysis_name, analysis_id in analysis.items():
    analysis_data = client.analysis().get_data(analysis_id)

    with open(output_folder + analysis_name + ".json", "w", encoding="utf-8") as f:
        print(f"Saving {analysis_name} ({analysis_id})...")
        f.write(analysis_data.decode("utf-8"))

print("Finished bulk download.")
