import unittest
import sys
import os

# Ensure src is in sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../../src')))

from api_call.arium.model.activity import (
    Activity, ActivityStatus, ActivityType, ActivityMode, 
    ActivitySubmitRequest, ActivityPayloadModel, OutputItem,
    OutputItemParameters, OutputExportType, OutputProjection, OutputPerspective
)
from api_call.arium.model.simulation import SimulationModel, LossAllocation

class TestActivityModels(unittest.TestCase):
    def test_activity_from_dict(self):
        data = {
            "activityId": "act-123",
            "workspace": "ws-1",
            "name": "Test Activity",
            "status": "running",
            "activityType": "calculation"
        }
        activity = Activity.from_dict(data)
        self.assertEqual(activity.activityId, "act-123")
        self.assertEqual(activity.status, ActivityStatus.RUNNING)
        self.assertEqual(activity.activityType, ActivityType.CALCULATION)

    def test_event_import_activity_from_dict(self):
        data = {
            "activityId": "act-456",
            "workspace": "ws-1",
            "name": "events.csv",
            "status": "completedWithExceptions",
            "activityType": "eventImport",
            "mode": "bulkImport",
            "progress": 100,
            "progressDetails": {"imported": "38/40"},
            "activityDetails": {"Imported": 38, "Rejected": 2},
            "errorCsvKey": "event-import/act-456/errors.csv",
            "importLogKey": "event-import/act-456/import.log",
        }
        activity = Activity.from_dict(data)
        self.assertEqual(activity.status, ActivityStatus.COMPLETED_WITH_EXCEPTIONS)
        self.assertEqual(activity.activityType, ActivityType.EVENT_IMPORT)
        self.assertEqual(activity.mode, ActivityMode.BULK_IMPORT)
        self.assertEqual(activity.activityDetails["Rejected"], 2)
        self.assertEqual(activity.progressDetails["imported"], "38/40")
        self.assertEqual(activity.errorCsvKey, "event-import/act-456/errors.csv")

    def test_legacy_and_export_activities_from_dict(self):
        legacy = Activity.from_dict({"activityId": "a", "workspace": "w", "name": "n",
                                     "activityType": "csvImport", "status": "failed"})
        export = Activity.from_dict({"activityId": "b", "workspace": "w", "name": "n",
                                     "activityType": "eventExport", "mode": "bulkExport",
                                     "status": "noClaimsGenerated"})
        self.assertEqual(legacy.activityType, ActivityType.CSV_IMPORT)
        self.assertEqual(export.activityType, ActivityType.EVENT_EXPORT)
        self.assertEqual(export.mode, ActivityMode.BULK_EXPORT)
        self.assertEqual(export.status, ActivityStatus.NO_CLAIMS_GENERATED)

    def test_event_import_cannot_be_submitted(self):
        with self.assertRaises(ValueError):
            ActivitySubmitRequest(payload=ActivityPayloadModel(), activityType=ActivityType.EVENT_IMPORT)

    def test_activity_to_dict(self):
        activity = Activity(
            activityId="act-123",
            workspace="ws-1",
            name="Test Activity",
            status=ActivityStatus.COMPLETED
        )
        data = activity.to_dict()
        self.assertEqual(data["activityId"], "act-123")
        self.assertEqual(data["status"], "completed")

    def test_activity_submit_request_serialization(self):
        request = ActivitySubmitRequest(
            activityType=ActivityType.CALCULATION,
            mode=ActivityMode.STOCHASTIC,
            name="My Calc",
            payload=ActivityPayloadModel(
                output=[
                    OutputItem(
                        exportType=OutputExportType.AAL,
                        parameters=OutputItemParameters(
                            projections=[OutputProjection.PORTFOLIO],
                            perspectives=[OutputPerspective.GROSS_LOSS]
                        )
                    )
                ],
                simulation=SimulationModel(
                    lossAllocation=LossAllocation(ref="asset-ref")
                )
            )
        )
        data = request.to_dict()
        self.assertEqual(data["activityType"], "calculation")
        self.assertEqual(data["payload"]["output"][0]["exportType"], "aal")
        self.assertEqual(data["payload"]["output"][0]["parameters"]["projections"], ["portfolio"])
        self.assertEqual(data["payload"]["simulation"]["lossAllocation"]["ref"], "asset-ref")

    def test_activity_submit_request_deserialization(self):
        data = {
            "activityType": "calculation",
            "mode": "stochastic",
            "name": "My Calc",
            "payload": {
                "output": [
                    {
                        "exportType": "aal",
                        "parameters": {
                            "projections": ["portfolio"],
                            "perspectives": ["grossLoss"]
                        }
                    }
                ],
                "simulation": {
                    "lossAllocation": {"ref": "asset-ref"}
                }
            }
        }
        request = ActivitySubmitRequest.from_dict(data)
        self.assertEqual(request.activityType, ActivityType.CALCULATION)
        self.assertEqual(request.payload.output[0].exportType, OutputExportType.AAL)
        self.assertEqual(request.payload.output[0].parameters.projections[0], OutputProjection.PORTFOLIO)
        self.assertEqual(request.payload.simulation.lossAllocation.ref, "asset-ref")

if __name__ == '__main__':
    unittest.main()
