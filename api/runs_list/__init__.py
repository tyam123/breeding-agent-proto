import os
import json
import azure.functions as func
from azure.storage.blob import BlobServiceClient

def main(req: func.HttpRequest) -> func.HttpResponse:
    account_name = os.environ["STORAGE_ACCOUNT_NAME"]
    account_key = os.environ["STORAGE_ACCOUNT_KEY"]
    container_name = os.environ["RESULTS_CONTAINER"]

    blob_service = BlobServiceClient(
        f"https://{account_name}.blob.core.windows.net",
        credential=account_key
    )
    container = blob_service.get_container_client(container_name)

    runs = set()
    for blob in container.list_blobs(name_starts_with="runs/"):
        parts = blob.name.split("/")
        if len(parts) >= 2:
            runs.add(parts[1])

    return func.HttpResponse(
        json.dumps(sorted(runs)),
        mimetype="application/json"
    )
