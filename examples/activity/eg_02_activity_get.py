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
    auth = Auth(tenant="test", role="basic", settings=auth_settings)

    # Create the new client - it will execute the required API actions
    client = APIClient(auth=auth)

    # TODO - provide activity id
    # activity = client.activity().get('<your_activity_id>')
    # print(activity.to_json(indent=4))


if __name__ == "__main__":
    main()
