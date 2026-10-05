# Download the bulk event import template: a zip with the CSV template, an example and a README.
#
# The CSV must be UTF-8, comma separated, with these 10 columns in this order:
#   Event Name, Currency, Insurable Economic Losses, Insurable Non-economic Losses, Industry Code,
#   Industry Culpability % Share, Industry # Culpable Organizations, Line of Business,
#   Line of Business % Share, Jurisdiction
# One row per industry, line of business and jurisdiction; rows with the same Event Name make one event.
from api_call.client import APIClient
from auth.okta_auth import Auth


def main():
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

    # Perform authentication
    auth = Auth(tenant="workspace1", role="basic", settings=auth_settings)

    # Create the new client - it will execute the required API actions
    client = APIClient(auth=auth)

    file_name = client.event_import().template("Bulk_Event_Import_Template.zip")
    print(f"Template saved to {file_name}")


if __name__ == "__main__":
    main()
