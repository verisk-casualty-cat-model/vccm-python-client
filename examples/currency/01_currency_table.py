import json

from api_call.arium.util.currency_table import Currency, CurrencyTable
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

# Create dictionaries representing currencies
currency_1 = Currency(code="USD", rate=1)
currency_2 = Currency(code="EUR", rate=1.2)
currency_3 = Currency(code="GBP", rate=0.98)

# Create dictionary representing currency table
currency_list = [currency_1, currency_2, currency_3]
currency_table_name = "My currency"
currency_table = CurrencyTable(name=currency_table_name, currencies=currency_list)

# Create currency table resource
asset_data = client.currency_tables().create(
    asset_name=currency_table_name, data=currency_table.get()
)
print(f"currency table: {json.dumps(asset_data, indent=4)}")
