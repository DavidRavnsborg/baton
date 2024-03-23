from flask import Flask, request, jsonify
import os
import uuid
import yaml
from operations.http.azure import get_secrets, AzureStorage
from operations.http.azure_helper import print_table_diff, upload_entities_to_table
from operations.local.config import load_config
from operations.local.logging import baton_log


class LemrAutomationApp:
    def __init__(self, config, secrets):
        self.app = Flask(__name__)
        self.config = config
        self.secrets = secrets
        self.storage_client = AzureStorage(
            connection_str=self.secrets["azure-storage-connect-str"]
        )
        self.configure_routes()

    def add_submission(self, branch_name: str, cleaner_name: str, max_attempts: int):
        submission = [
            {
                "PartitionKey": "test",  # storage_table['partition']
                "RowKey": str(uuid.uuid4()),
                "branch_name": branch_name,
                "cleaner_name": cleaner_name,
                "max_attempts": max_attempts,
                "current_attempts": 0,
                "rows_geocoded": 0,
                "addresses_geocoded": 0,
                "status": "active",
            }
        ]
        upload_entities_to_table(
            entities=submission,
            table="geocoderunner",  # storage_table['runner_table']
            storage_client=self.storage_client,
            error_partition="testerror",
        )

    def register_run(self):
        data = request.json
        branch_name = data.get("branch_name")
        cleaner_name = data.get("cleaner_name")
        max_attempts = data.get("max_attempts", 1)

        if "cleaner_" in cleaner_name:
            baton_log.warning(
                f"cleaner_name contains string {'cleaner_'}. Cancelling submission upload."
            )
            return (
                jsonify(
                    {
                        "status": "Invalid request",
                        "message": "Please remove 'cleaner_' string from cleaner_name, and re-submit your request.",
                    }
                ),
                422,
            )

        self.add_submission(branch_name, cleaner_name, max_attempts)
        return (
            jsonify(
                {
                    "status": "accepted",
                    "message": "Request accepted and run registered. Will run it when the runner is available.",
                }
            ),
            200,
        )

    def health_check(self):
        return "OK"

    def configure_routes(self):
        self.app.add_url_rule(
            rule="/register_run",
            endpoint="register_run",
            view_func=self.register_run,
            methods=["POST"],
        )
        self.app.add_url_rule(
            rule="/health",
            endpoint="health",
            view_func=self.health_check,
            methods=["GET"],
        )


if __name__ == "__main__":
    # TODO: Change to relative path after moving directories up (so it's the same between Linux deployment and Windows development)
    config = load_config()
    secrets = get_secrets(
        vault_url=config["key_vault"], secret_names=["azure-storage-connect-str"]
    )
    lemr_automation_app = LemrAutomationApp(config=config, secrets=secrets)
    lemr_automation_app.app.run(host="0.0.0.0", port=5000)
