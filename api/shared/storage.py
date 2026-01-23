# /api/shared/storage.py
import os, json
from azure.storage.blob import BlobServiceClient
from azure.storage.queue import QueueClient

def blob_service() -> BlobServiceClient:
    return BlobServiceClient.from_connection_string(os.environ["AzureWebJobsStorage"])

def get_container(name: str):
    return blob_service().get_container_client(name)

def put_json(container: str, blob_name: str, obj: dict):
    cc = get_container(container)
    data = json.dumps(obj, ensure_ascii=False).encode("utf-8")
    cc.upload_blob(name=blob_name, data=data, overwrite=True, content_type="application/json")

def get_json(container: str, blob_name: str) -> dict | None:
    cc = get_container(container)
    try:
        b = cc.get_blob_client(blob_name).download_blob().readall()
        return json.loads(b.decode("utf-8"))
    except Exception:
        return None

def list_blobs(container: str, prefix: str):
    cc = get_container(container)
    return [b.name for b in cc.list_blobs(name_starts_with=prefix)]

def get_blob_bytes(container: str, blob_name: str) -> bytes:
    cc = get_container(container)
    return cc.get_blob_client(blob_name).download_blob().readall()

def enqueue_run(message: dict):
    qname = os.environ.get("BREEDING_RUN_QUEUE", "breeding-run-queue")
    qc = QueueClient.from_connection_string(os.environ["AzureWebJobsStorage"], qname)
    qc.send_message(json.dumps(message, ensure_ascii=False))
