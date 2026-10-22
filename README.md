# README VCCM 1.2.0 #

### What is this repository for? ###

The project provides an example of how the VCCM API can be used to create reusable scripts
for running analytics. The project contains functions that can be used to make requests to the API.
In particular, the functions allow the user to run analysis on a portfolio.

Detailed documentation is available through VCCM UI under API documentation.

### Managing the project with `uv` ###

`uv` is an extremely fast Python package manager and resolver. We recommend using it for managing this project's dependencies and environment.

#### 1. Install `uv` ####

*   **macOS / Linux:**
    ```shell
    curl -LsSf https://astral.sh/uv/install.sh | sh
    ```
*   **Windows:**
    ```powershell
    powershell -ExecutionPolicy ByPass -c "irm https://astral.sh/uv/install.ps1 | iex"
    ```

#### 2. Project Setup ####

Once `uv` is installed, you can synchronize the project's dependencies and create a virtual environment:

```shell
uv sync
```
This will create a `.venv` directory and install all required dependencies specified in `pyproject.toml`.

#### 3. Running Scripts and Tests ####

You can run scripts and tests within the `uv` environment without manually activating it:

*   **Run an example:**
    ```shell
    uv run examples/activity/eg_01_activity_list.py
    ```
    *Note: `uv run` automatically sets up the environment and includes `src` in the `PYTHONPATH` if correctly configured, or you can use `uv run python examples/...`*

*   **Run unit tests:**
    ```shell
    uv run python -m unittest discover tests/unit
    ```

#### 4. Building the Project ####

To build the project into a distributable wheel and source distribution:

```shell
uv build
```
The built artifacts will be located in the `dist/` directory.

#### 5. Regenerating `requirements.txt` ####

To maintain compatibility for users who do not use `uv`, you can update `requirements.txt` whenever you change dependencies:

```shell
uv export --format requirements.txt --no-dev --no-emit-project --no-hashes -o requirements.txt
```

### Basic setup (Alternative using pip) ###

If you prefer not to use `uv`, you can still set up the project using `pip`. Note that we maintain a `requirements.txt` file for this purpose, which is generated from the `uv` lockfile.

1.  **Install Python 3.12.**
2.  **Get the source from Git.**
3.  **Create and activate a virtual environment (recommended):**
    ```shell
    python -m venv .venv
    # macOS / Linux:
    source .venv/bin/activate
    # Windows:
    .venv\Scripts\activate
    ```
4.  **Install dependencies:**
    ```shell
    pip install -r requirements.txt
    ```
5.  **Set `PYTHONPATH` (required for running examples):**
    You must include the `src` folder in your `PYTHONPATH` so that the scripts can find the `api_call`, `auth`, and `config` packages.
    See the [How to run the script from the command line](#how-to-run-the-script-from-the-command-line) section for platform-specific commands.

6.  **Create the authorization settings dictionary** in your script (see [Examples](#examples)).

### Examples ####

#### 1. Example script with authorization in the web browser (authorization code flow): ####

To get the authentication settings, please contact the support team.

```python
from api_call.client import APIClient
from auth.okta_auth import Auth

auth_settings = {
    "authorization_url": "",
    "token_url": "",
    "base_uri": "",
    "client_id": "",
    "client_secret": ""
}

auth = Auth(tenant="workspace1", role="basic", settings=auth_settings)
client = APIClient(auth=auth)

client.activity().list()
``` 

Here the Okta authentication on browser should kick off and then the script should run.

#### How to run the script from the command line. ####

##### Example command to run the eg_01_activity_list script on Windows (cmd.exe, PowerShell): #####

Note: the PYTHONPATH is needed to run the examples: the /src folder contains the necessary functions.

cmd.exe:

```shell
set "PYTHONPATH=%CD%\src;%CD%"
python examples\activity\eg_01_activity_list.py
```

PowerShell:

```shell
$env:PYTHONPATH = "$PWD\src;$PWD"
python .\examples\activity\eg_01_activity_list.py
```

##### Example command to run the eg_01_activity_list script on MacOS: #####

Note: the PYTHONPATH is needed to run the examples: the /src folder is needed to import the functions.

```shell
% PYTHONPATH="$(pwd)/src:$(pwd)" python examples/activity/eg_01_activity_list.py
```

##### 2. Example script with machine-to-machine authentication #####

To get machine-to-machine authentication settings, please contact the support team.

```python
from api_call.client import APIClient
from auth.okta_auth import Auth

auth_settings = {
    "authorization_url": "",
    "token_url": "",
    "base_uri": "",
    "client_id": "",
    "client_secret": ""
}

auth = Auth(tenant="workspace1", role="basic", settings=auth_settings, authorization_code=False)
client = APIClient(auth=auth)

client.activity().list()
```

### Bulk event import and export ###

Events can be imported in bulk from a CSV built on the template, or from an event library export (`.sce`),
and exported back to the same CSV format. Each import or export runs as an activity: the call returns
its id, and `client.activity()` follows it and downloads its files.

```python
activity = client.event_import().import_csv("events.csv", folder_name="Imported events", wait=True)
print(activity.status, activity.activityDetails)

if activity.errorCsvKey:
    errors = client.activity().error_csv(activity.activityId)  # rejected rows with the reasons
```

* CSV files up to 4 MB are posted directly, larger ones (up to 100 MB) are uploaded to S3 first.
  `.sce` files (up to 40 MB) are always uploaded.
* An import ends `completed`, `completedWithExceptions` (some events were rejected) or `failed`.
* Invalid rows are handled by the workspace's import policy: with `CONTINUE_WHEN_ERROR` (default) the valid events
  are imported, with `STOP_WHEN_ERROR` nothing is. The policy is set per workspace by the support team.
* Import and export activities cannot be resubmitted - start a new one instead.

Examples in `examples/events/`:

| Example | Description |
|---|---|
| `eg_13_bulk_import_csv.py` | import a CSV into a new folder, save the rejected rows |
| `eg_14_import_sce.py` | import an event library export (`.sce`) |
| `eg_15_import_template.py` | download the CSV template |
| `eg_16_import_errors.py` | download the error CSV and import log of an import |
| `eg_17_bulk_export_csv.py` | export a folder of events to CSV |
