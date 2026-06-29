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
print(client)

# REQUIRED ACTION: Set path to event file
# Create event
print("CREATE EVENT")
with open("path/to/event.json") as file:
    data = json.load(file)
new_event = client.events().create("test-event-2", data)
print(f"event: {json.dumps(new_event, sort_keys=True, indent=4)}")

# REQUIRED ACTION: Set path to portfolio file
# Create portfolio
print("CREATE PORTFOLIO")
with open("path/to/portfolio.csv") as file:
    data = file.read()
portfolio = client.portfolios().create(f"test-portfolio-2", data)
print(f"portfolio: {json.dumps(portfolio, sort_keys=True, indent=4)}")
