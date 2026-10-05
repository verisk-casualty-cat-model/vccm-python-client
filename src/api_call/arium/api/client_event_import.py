import json
import os
from http import HTTPStatus
from typing import List, Optional, Union, TYPE_CHECKING
from urllib.parse import urlencode

import requests

from api_call.arium.api.exceptions import EventImportException
from api_call.arium.api.request import get_redirect_content
from api_call.arium.model.activity import Activity
from api_call.arium.model.event_import import EventImportResponse, ImportFormat
from config.constants import (
    ENDPOINT_EVENT_IMPORT,
    ENDPOINT_EVENT_IMPORT_UPLOADS,
    ENDPOINT_EVENT_IMPORT_TEMPLATE,
    ENDPOINT_EVENT_EXPORT,
    EVENT_IMPORT_INLINE_MAX_BYTES,
    EVENT_IMPORT_CSV_MAX_BYTES,
    EVENT_IMPORT_SCE_MAX_BYTES,
)
from config.get_logger import get_logger

if TYPE_CHECKING:
    from api_call.client import APIClient

logger = get_logger(__name__)


class EventImportClient:
    """
    Bulk event import and export.

    Every call here starts an activity on the server (type eventImport or eventExport) and returns its id.
    Follow it with client.activity(): get / wait / cancel, and download its files with
    error_csv / import_log (import) or export_file (export).

    What happens to invalid CSV rows is set per workspace, not per request: with CONTINUE_WHEN_ERROR
    (the default) the valid events are imported and the activity ends completedWithExceptions; with
    STOP_WHEN_ERROR nothing is imported and the activity ends failed.
    """

    def __init__(self, client: "APIClient"):
        self._client = client

    def import_csv(
            self,
            path: str,
            folder_name: str,
            file_name: Optional[str] = None,
            wait: bool = False,
            timeout_minutes: int = 60,
    ) -> Union[EventImportResponse, Activity]:
        """
        Imports events from a bulk-import CSV (see template()) into a new folder.
        Files up to 4 MB are posted directly, larger ones (up to 100 MB) go through a presigned upload.

        :param path: CSV file
        :param folder_name: folder to create for the imported events; it must not exist yet
        :param file_name: label shown on the activity, defaults to the file's name
        :param wait: wait for the activity to finish and return it
        :return: the queued import, or the finished activity when wait=True
        """
        size = _file_size(path, EVENT_IMPORT_CSV_MAX_BYTES)
        query = urlencode({"folderName": folder_name, "fileName": file_name or os.path.basename(path)})
        endpoint = f"/{{tenant}}/{ENDPOINT_EVENT_IMPORT}?{query}"

        if size <= EVENT_IMPORT_INLINE_MAX_BYTES:
            with open(path, "rb") as file:
                response = self._client.post_request(
                    endpoint=endpoint, data=file.read(), headers={"Content-Type": "text/csv"}
                )
        else:
            import_id = self._upload(path, size, ImportFormat.CSV)
            response = self._client.post_request(
                endpoint=endpoint, json={"importId": import_id, "format": ImportFormat.CSV.value}
            )
        return self._queued(response, wait, timeout_minutes)

    def import_sce(
            self,
            path: str,
            file_name: Optional[str] = None,
            wait: bool = False,
            timeout_minutes: int = 60,
    ) -> Union[EventImportResponse, Activity]:
        """
        Imports an event library export (.sce, up to 40 MB). Events are saved at the paths recorded
        in the export, so no folder is created.

        :return: the queued import, or the finished activity when wait=True
        """
        size = _file_size(path, EVENT_IMPORT_SCE_MAX_BYTES)
        import_id = self._upload(path, size, ImportFormat.SCE)
        query = urlencode({"fileName": file_name or os.path.basename(path)})
        response = self._client.post_request(
            endpoint=f"/{{tenant}}/{ENDPOINT_EVENT_IMPORT}?{query}",
            json={"importId": import_id, "format": ImportFormat.SCE.value},
        )
        return self._queued(response, wait, timeout_minutes)

    def export_csv(
            self, asset_ids: List[str], wait: bool = False, timeout_minutes: int = 60
    ) -> Union[EventImportResponse, Activity]:
        """
        Exports events as a bulk-import CSV, which import_csv() accepts back.
        Download the file with client.activity().export_file(activity_id) once the activity is
        completed; completedWithExceptions means the file is missing some of the events.

        :param asset_ids: event asset ids
        :return: the queued export, or the finished activity when wait=True
        """
        if not asset_ids:
            raise ValueError("At least one event asset id is required.")
        response = self._client.post_request(
            endpoint=f"/{{tenant}}/{ENDPOINT_EVENT_EXPORT}", json=list(asset_ids)
        )
        return self._queued(response, wait, timeout_minutes)

    def template(self, file_name: str = "Bulk_Event_Import_Template.zip") -> str:
        """
        Downloads the bulk-import template: a zip with the CSV template, an example and a README.
        :return: path of the saved file
        """
        content = get_redirect_content(self._client, f"/{{tenant}}/{ENDPOINT_EVENT_IMPORT_TEMPLATE}")
        if content is None:
            raise EventImportException(HTTPStatus.NOT_FOUND, "No bulk import template in this workspace.")
        with open(file_name, "wb") as file:
            file.write(content)
        logger.info(f"Template saved to {file_name}.")
        return file_name

    def _upload(self, path: str, size: int, import_format: ImportFormat) -> str:
        response = self._client.post_request(
            endpoint=f"/{{tenant}}/{ENDPOINT_EVENT_IMPORT_UPLOADS}",
            json={"sizeInBytes": size, "format": import_format.value},
        )
        reservation = _content(response, accept=(HTTPStatus.OK,))["data"]

        # Content-Type and Content-Length are part of the presigned URL's signature
        with open(path, "rb") as file:
            upload = requests.put(
                url=reservation["uploadUrl"],
                data=file,
                headers={"Content-Type": reservation["contentType"], "Content-Length": str(size)},
                verify=self._client.verify,
            )
        if upload.status_code != HTTPStatus.OK:
            raise EventImportException.from_response(upload)
        logger.info(f"Uploaded {path} ({size} bytes).")
        return reservation["importId"]

    def _queued(self, response, wait: bool, timeout_minutes: int) -> Union[EventImportResponse, Activity]:
        result = EventImportResponse.from_dict(_content(response, accept=(HTTPStatus.ACCEPTED,))["data"])
        for warning in result.warnings:
            logger.warning(warning)
        if result.rejected:
            logger.warning(f"{len(result.rejected)} event(s) rejected before import.")
        logger.info(f"Activity {result.activityId} queued for {result.total} event(s).")

        if wait:
            return self._client.activity().wait(activity_id=result.activityId, timeout_minutes=timeout_minutes)
        return result


def _file_size(path: str, max_bytes: int) -> int:
    size = os.path.getsize(path)
    if size == 0:
        raise ValueError(f"{path} is empty.")
    if size > max_bytes:
        raise ValueError(f"{path} is {size} bytes, the limit for one import is {max_bytes} bytes.")
    return size


def _content(response, accept) -> dict:
    if response.status_code not in accept:
        raise EventImportException.from_response(response)
    return json.loads(response.content)
