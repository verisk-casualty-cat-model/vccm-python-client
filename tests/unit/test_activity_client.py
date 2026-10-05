import unittest
from unittest.mock import MagicMock, patch
import sys
import os
import tempfile

# Ensure src is in sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../../src')))

from api_call.arium.api.client_activity import ActivityClient
from api_call.arium.model.activity import Activity, ActivityStatus, ActivitySubmitRequest


def _response(status_code, location=None, content=b""):
    response = MagicMock()
    response.status_code = status_code
    response.headers = {"Location": location} if location else {}
    response.content = content
    return response


class TestActivityClient(unittest.TestCase):
    def setUp(self):
        self.mock_api_client = MagicMock()
        self.client = ActivityClient(self.mock_api_client)

    def test_get_activity(self):
        activity_id = "test-id"
        mock_response_data = {
            "activityId": activity_id,
            "workspace": "test-workspace",
            "name": "test-activity",
            "status": "completed"
        }
        mock_response = MagicMock()
        mock_response.status_code = 200
        self.mock_api_client.get_request.return_value = mock_response
        
        with patch('api_call.arium.api.client_activity.get_content', return_value=mock_response_data):
            activity = self.client.get(activity_id)
            
        self.mock_api_client.get_request.assert_called_once_with(
            endpoint=f"/{{tenant}}/activity/{activity_id}",
            retry=1
        )
        self.assertIsInstance(activity, Activity)
        self.assertEqual(activity.activityId, activity_id)
        self.assertEqual(activity.status, ActivityStatus.COMPLETED)

    def test_submit_activity(self):
        request = MagicMock(spec=ActivitySubmitRequest)
        request.to_dict.return_value = {"payload": "data"}
        
        mock_submit_response = {"data": {"activityId": "new-id"}}
        mock_activity_data = {
            "activityId": "new-id", 
            "status": "queued",
            "workspace": "test-workspace",
            "name": "test-activity"
        }
        
        mock_response = MagicMock()
        self.mock_api_client.post_request.return_value = mock_response
        
        # We need to patch get_content because it's used inside submit
        with patch('api_call.arium.api.client_activity.get_content', return_value=mock_submit_response):
            # Also need to mock self.get() which is called at the end of submit
            with patch.object(ActivityClient, 'get') as mock_get:
                mock_get.return_value = Activity.from_dict(mock_activity_data)
                activity = self.client.submit(request)
                
                self.mock_api_client.post_request.assert_called_once()
                mock_get.assert_called_once_with(activity_id="new-id")
                self.assertEqual(activity.activityId, "new-id")

    def test_cancel_activity(self):
        activity_id = "test-id"
        mock_response = MagicMock()
        mock_response.status_code = 200
        self.mock_api_client.post_request.return_value = mock_response
        
        self.client.cancel(activity_id)
        
        self.mock_api_client.post_request.assert_called_once_with(
            endpoint=f"/{{tenant}}/activity/{activity_id}/cancel"
        )

    def test_wait_stops_on_completed_with_exceptions(self):
        activity = Activity.from_dict({"activityId": "a", "workspace": "w", "name": "n",
                                       "status": "completedWithExceptions"})
        with patch.object(ActivityClient, 'get', return_value=activity) as mock_get, \
                patch('api_call.arium.api.client_activity.time.sleep') as mock_sleep:
            result = self.client.wait("a")
        self.assertIs(result, activity)
        mock_get.assert_called_once()
        mock_sleep.assert_not_called()

    @patch('api_call.arium.api.request.requests.get')
    def test_error_csv_follows_redirect_without_auth(self, mock_requests_get):
        self.mock_api_client.get_request.return_value = _response(302, location="https://s3/presigned")
        mock_requests_get.return_value = _response(200, content=b"Event Name,Error Reason\n")

        result = self.client.error_csv("act-1", errors_only=True)

        self.mock_api_client.get_request.assert_called_once_with(
            endpoint="/{tenant}/activity/act-1/error-csv?variant=errors-only", allow_redirects=False
        )
        mock_requests_get.assert_called_once_with(url="https://s3/presigned", verify=self.mock_api_client.verify)
        self.assertEqual(result.getvalue(), b"Event Name,Error Reason\n")

    def test_error_csv_and_import_log_return_none_on_404(self):
        self.mock_api_client.get_request.return_value = _response(404)
        self.assertIsNone(self.client.error_csv("act-1"))
        self.assertIsNone(self.client.import_log("act-1"))
        self.assertIsNone(self.client.export_file("act-1"))

    @patch('api_call.arium.api.request.requests.get')
    def test_import_log_decodes_text(self, mock_requests_get):
        self.mock_api_client.get_request.return_value = _response(302, location="https://s3/log")
        mock_requests_get.return_value = _response(200, content="Created: Event Ł".encode("utf-8"))
        self.assertEqual(self.client.import_log("act-1"), "Created: Event Ł")
        self.mock_api_client.get_request.assert_called_once_with(
            endpoint="/{tenant}/activity/act-1/import-log", allow_redirects=False
        )

    @patch('api_call.arium.api.request.requests.get')
    def test_export_file_saves_file(self, mock_requests_get):
        self.mock_api_client.get_request.return_value = _response(302, location="https://s3/export")
        mock_requests_get.return_value = _response(200, content=b"csv")
        with tempfile.TemporaryDirectory() as tmp:
            path = os.path.join(tmp, "events.csv")
            result = self.client.export_file("act-1", file_name=path)
            with open(path, "rb") as f:
                self.assertEqual(f.read(), b"csv")
        self.assertEqual(result.getvalue(), b"csv")

    def test_resubmit_rejects_event_import(self):
        activity = Activity.from_dict({"activityId": "a", "workspace": "w", "name": "n",
                                       "activityType": "eventImport", "status": "failed"})
        with patch.object(ActivityClient, 'get', return_value=activity):
            with self.assertRaises(ValueError):
                self.client.resubmit("a")
        self.mock_api_client.post_request.assert_not_called()


if __name__ == '__main__':
    unittest.main()
