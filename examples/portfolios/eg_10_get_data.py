import io

import pandas as pd

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

s = str(client.portfolios().get_data(portfolio_id), "utf-8")
data = io.StringIO(s)
df = pd.read_csv(data)
print(df)
