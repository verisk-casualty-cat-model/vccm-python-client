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

# REQUIRED ACTION: Set ref ids
# Select portfolio id
portfolio_id = "example-portfolio-reference"

# Get version of portfolio
portfolio_versions_list = client.portfolios().versions(portfolio_id)
print(f"versions: {len(portfolio_versions_list)}")
for portfolio in portfolio_versions_list:
    print(f"portfolio: {json.dumps(portfolio, sort_keys=True, indent=4)}")
