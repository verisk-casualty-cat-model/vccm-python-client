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

# Get list of latest versions of portfolio assets
latest_portfolios_list = client.portfolios().list()
for portfolio in latest_portfolios_list:
    print(f"portfolio (latest): {json.dumps(portfolio, sort_keys=True, indent=4)}")

# Get list of ALL portfolio assets
all_portfolios_list = client.portfolios().list(latest=False)
for portfolio in all_portfolios_list:
    print(f"portfolio: {json.dumps(portfolio, sort_keys=True, indent=4)}")
