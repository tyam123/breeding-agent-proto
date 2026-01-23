import os, json
import azure.functions as func
from ..shared.storage import get_json

def main(req: func.HttpRequest) -> func.HttpResponse:
    run_id = req.route_params.get("run_id")
    runs_container = os.environ.get("BREEDING_RUNS_CONTAINER", "breeding-runs")
    result = get_json(runs_container, f"runs/{run_id}/result.json")
    if not result:
        return func.HttpResponse(json.dumps({"error": "result not ready"}), status_code=404, mimetype="application/json")
    return func.HttpResponse(json.dumps(result, ensure_ascii=False), mimetype="application/json")
