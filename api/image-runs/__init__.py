# /api/image-runs/__init__.py
import os, json, time, uuid
import azure.functions as func
from ..shared.storage import put_json, enqueue_run

def main(req: func.HttpRequest) -> func.HttpResponse:
    body = req.get_json()

    run_id = f"run_{time.strftime('%Y%m%d_%H%M%S')}_{uuid.uuid4().hex[:8]}"

    meta = {
        "run_id": run_id,
        "container": body["container"],
        "prefix": body["prefix"],
        "mode": body.get("mode", "per_image"),
        "max_images": int(body.get("max_images", 100)),
        "budget_cap": body.get("budget_cap"),
        "prompt_template_id": body.get("prompt_template_id", "proto"),
        "prompt_version": body.get("prompt_version", "0.0.1"),
        "prompt_override_text": body.get("prompt_override_text", ""),
        "preprocess": body.get("preprocess", {}),
        "created_at": time.time(),
        "status": "queued",
    }

    runs_container = os.environ.get("BREEDING_RUNS_CONTAINER", "breeding-runs")
    put_json(runs_container, f"runs/{run_id}/meta.json", meta)
    put_json(runs_container, f"runs/{run_id}/status.json", {
        "run_id": run_id, "status": "queued", "processed": 0, "failed": 0
    })

    enqueue_run({"run_id": run_id})
    return func.HttpResponse(json.dumps({"run_id": run_id, "status": "queued"}), mimetype="application/json")
