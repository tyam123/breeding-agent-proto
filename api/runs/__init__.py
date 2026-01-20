import os
import json
import datetime
import azure.functions as func
from azure.storage.blob import (
    BlobServiceClient,
    generate_blob_sas,
    BlobSasPermissions
)

def main(req: func.HttpRequest) -> func.HttpResponse:
    run_id = req.params.get("run_id")
    if not run_id:
        return func.HttpResponse(
            json.dumps({"error": "run_id is required"}),
            status_code=400,
            mimetype="application/json"
        )

    # 固定ルール：runs/{run_id}/summary.csv
    container_name = os.environ["RESULTS_CONTAINER"]
    account_name = os.environ["STORAGE_ACCOUNT_NAME"]
    account_key = os.environ["STORAGE_ACCOUNT_KEY"]

    blob_name = f"runs/{run_id}/summary.csv"

    # SAS（読み取り専用、短命）
    expiry_minutes = int(os.environ.get("SAS_EXPIRY_MINUTES", "30"))
    expiry = datetime.datetime.utcnow() + datetime.timedelta(minutes=expiry_minutes)

    sas = generate_blob_sas(
        account_name=account_name,
        container_name=container_name,
        blob_name=blob_name,
        account_key=account_key,
        permission=BlobSasPermissions(read=True),
        expiry=expiry,
        protocol="https"
    )

    url = f"https://{account_name}.blob.core.windows.net/{container_name}/{blob_name}?{sas}"

    return func.HttpResponse(
        json.dumps({
            "run_id": run_id,
            "blob_name": blob_name,
            "summary_csv_sas_url": url,
            "expires_in_minutes": expiry_minutes
        }),
        status_code=200,
        mimetype="application/json"
    )
