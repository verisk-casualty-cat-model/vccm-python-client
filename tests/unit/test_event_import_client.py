import json
import os
import sys
import tempfile
import unittest
from unittest.mock import MagicMock, patch

# Ensure src is in sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../../src')))

from api_call.arium.api.client_event_import import EventImportClient
from api_call.arium.api.exceptions import EventImportException
from api_call.arium.model.event_import import EventImportResponse
from config.constants import EVENT_IMPORT_INLINE_MAX_BYTES, EVENT_IMPORT_SCE_MAX_BYTES


def _response(status_code, body=None, location=None, content=None):
    response = MagicMock()
    response.status_code = status_code
    response.headers = {"Location": location} if location else {}
    response.content = content if content is not None else json.dumps(body or {}).encode("utf-8")
    response.reason = "reason"
    response.text = response.content.decode("utf-8", errors="replace")
    return response


ACCEPTED = _response(202, {"message": "queued", "data": {"activityId": "act-1", "total": 2}})
RESERVED = _response(200, {"data": {
    "importId": "imp-1", "uploadUrl": "https://s3/upload", "contentType": "text/csv",
    "sizeInBytes": 0, "maxBytes": 104857600, "format": "csv",
}})


class TestEventImportClient(unittest.TestCase):
    def setUp(self):
        self.mock_api_client = MagicMock()
        self.client = EventImportClient(self.mock_api_client)
        self.tmp = tempfile.TemporaryDirectory()

    def tearDown(self):
        self.tmp.cleanup()

    def _file(self, name, size):
        path = os.path.join(self.tmp.name, name)
        with open(path, "wb") as f:
            f.write(b"x" * size)
        return path

    def test_small_csv_is_posted_inline(self):
        path = self._file("events.csv", EVENT_IMPORT_INLINE_MAX_BYTES)
        self.mock_api_client.post_request.return_value = ACCEPTED

        result = self.client.import_csv(path, folder_name="My folder")

        self.mock_api_client.post_request.assert_called_once()
        kwargs = self.mock_api_client.post_request.call_args.kwargs
        self.assertEqual(kwargs["endpoint"], "/{tenant}/event-import?folderName=My+folder&fileName=events.csv")
        self.assertEqual(kwargs["headers"], {"Content-Type": "text/csv"})
        self.assertEqual(len(kwargs["data"]), EVENT_IMPORT_INLINE_MAX_BYTES)
        self.assertIsInstance(result, EventImportResponse)
        self.assertEqual(result.activityId, "act-1")
        self.assertEqual(result.total, 2)

    @patch('api_call.arium.api.client_event_import.requests.put')
    def test_large_csv_is_uploaded_then_committed(self, mock_put):
        size = EVENT_IMPORT_INLINE_MAX_BYTES + 1
        path = self._file("big.csv", size)
        self.mock_api_client.post_request.side_effect = [RESERVED, ACCEPTED]
        mock_put.return_value = _response(200)

        self.client.import_csv(path, folder_name="big", file_name="label")

        reserve, commit = self.mock_api_client.post_request.call_args_list
        self.assertEqual(reserve.kwargs, {"endpoint": "/{tenant}/event-import/uploads",
                                          "json": {"sizeInBytes": size, "format": "csv"}})
        put_kwargs = mock_put.call_args.kwargs
        self.assertEqual(put_kwargs["url"], "https://s3/upload")
        self.assertEqual(put_kwargs["headers"], {"Content-Type": "text/csv", "Content-Length": str(size)})
        self.assertNotIn("Authorization", put_kwargs["headers"])
        self.assertEqual(commit.kwargs, {"endpoint": "/{tenant}/event-import?folderName=big&fileName=label",
                                         "json": {"importId": "imp-1", "format": "csv"}})

    @patch('api_call.arium.api.client_event_import.requests.put')
    def test_failed_upload_does_not_commit(self, mock_put):
        path = self._file("big.csv", EVENT_IMPORT_INLINE_MAX_BYTES + 1)
        self.mock_api_client.post_request.side_effect = [RESERVED, ACCEPTED]
        mock_put.return_value = _response(403, content=b"<Error>SignatureDoesNotMatch</Error>")

        with self.assertRaises(EventImportException) as ctx:
            self.client.import_csv(path, folder_name="big")
        self.assertEqual(ctx.exception.status_code, 403)
        self.assertEqual(self.mock_api_client.post_request.call_count, 1)

    def test_too_large_or_empty_file_is_rejected_before_any_request(self):
        with self.assertRaises(ValueError):
            self.client.import_sce(self._file("big.sce", EVENT_IMPORT_SCE_MAX_BYTES + 1))
        with self.assertRaises(ValueError):
            self.client.import_csv(self._file("empty.csv", 0), folder_name="f")
        self.mock_api_client.post_request.assert_not_called()

    @patch('api_call.arium.api.client_event_import.requests.put')
    def test_sce_always_uploads_and_takes_no_folder(self, mock_put):
        path = self._file("library.sce", 10)
        self.mock_api_client.post_request.side_effect = [RESERVED, ACCEPTED]
        mock_put.return_value = _response(200)

        self.client.import_sce(path)

        reserve, commit = self.mock_api_client.post_request.call_args_list
        self.assertEqual(reserve.kwargs["json"], {"sizeInBytes": 10, "format": "sce"})
        self.assertEqual(commit.kwargs, {"endpoint": "/{tenant}/event-import?fileName=library.sce",
                                         "json": {"importId": "imp-1", "format": "sce"}})

    def test_validation_errors_are_raised_with_rows(self):
        path = self._file("events.csv", 10)
        self.mock_api_client.post_request.return_value = _response(400, {
            "message": "Validation failed.",
            "details": {"errors": ["Row 2: unknown currency 'XXX'", "Row 3: missing Event Name"]},
        })

        with self.assertRaises(EventImportException) as ctx:
            self.client.import_csv(path, folder_name="f")
        self.assertEqual(ctx.exception.status_code, 400)
        self.assertEqual(len(ctx.exception.errors), 2)
        self.assertIn("unknown currency", str(ctx.exception))

    def test_wait_delegates_to_activity_client(self):
        path = self._file("events.csv", 10)
        self.mock_api_client.post_request.return_value = ACCEPTED

        result = self.client.import_csv(path, folder_name="f", wait=True, timeout_minutes=5)

        self.mock_api_client.activity.return_value.wait.assert_called_once_with(activity_id="act-1",
                                                                                timeout_minutes=5)
        self.assertIs(result, self.mock_api_client.activity.return_value.wait.return_value)

    def test_export_csv_posts_ids(self):
        # the export route answers without the {message, data} envelope
        self.mock_api_client.post_request.return_value = _response(202, {"activityId": "act-2", "total": 2})

        result = self.client.export_csv(("id-1", "id-2"))

        self.mock_api_client.post_request.assert_called_once_with(endpoint="/{tenant}/event-import/export",
                                                                  json=["id-1", "id-2"])
        self.assertEqual(result.activityId, "act-2")
        self.assertEqual(result.total, 2)

    def test_export_csv_requires_ids(self):
        with self.assertRaises(ValueError):
            self.client.export_csv([])
        self.mock_api_client.post_request.assert_not_called()

    @patch('api_call.arium.api.request.requests.get')
    def test_template_follows_redirect(self, mock_get):
        self.mock_api_client.get_request.return_value = _response(302, location="https://s3/template")
        mock_get.return_value = _response(200, content=b"PK")
        path = os.path.join(self.tmp.name, "template.zip")

        self.assertEqual(self.client.template(path), path)

        self.mock_api_client.get_request.assert_called_once_with(endpoint="/{tenant}/event-import/template",
                                                                 allow_redirects=False)
        with open(path, "rb") as f:
            self.assertEqual(f.read(), b"PK")

    def test_template_missing(self):
        self.mock_api_client.get_request.return_value = _response(404)
        with self.assertRaises(EventImportException):
            self.client.template(os.path.join(self.tmp.name, "template.zip"))


if __name__ == '__main__':
    unittest.main()
