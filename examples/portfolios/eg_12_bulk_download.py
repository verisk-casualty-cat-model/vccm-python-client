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
portfolios = {p["name"]: p["id"] for p in client.portfolios().list()}

if not os.path.exists(output_folder):
    os.makedirs(output_folder)

succeeded = []
failed = []

for portfolio_name, portfolio_id in portfolios.items():
    try:
        portfolio_data = client.portfolios().get_data(portfolio_id)

        with open(
            output_folder + portfolio_name + ".csv", "w", encoding="utf-8", newline=""
        ) as f:
            print(f"Saving {portfolio_name} ({portfolio_id})...")
            f.write(portfolio_data.decode("utf-8"))
        succeeded.append(portfolio_name)
    except Exception as e:
        failed.append(portfolio_name)
        print(
            f"Failed to download portfolio {portfolio_name} ({portfolio_id}). Reason: '{e}'. Skipping."
        )

print("Finished bulk download.")
print(f"Succeeded: {succeeded}")
print(f"Failed: {failed}")
