import os, json, time, hashlib
import azure.functions as func
from ..shared.storage import get_json, put_json, list_blobs, get_blob_bytes
from ..shared.preprocess import preprocess_image_bytes
from ..shared.openai_vision import call_openai_vision

SYSTEM_SEEDCOUNT = """あなたは大豆の子実数カウンターです。
各画像について、{"traits":[{"name":"count","score":<整数>,"confidence":<0..1>}]}
のJSONを必ず1回だけ出力してください（説明禁止）。"""
USER_SEEDCOUNT = "この画像について大豆子実の総数を推定し、指定JSONのみ返してください。"

def _hash_prompt(system_text: str, user_text: str) -> str:
    h = hashlib.sha256((system_text + "\n" + user_text).encode("utf-8")).hexdigest()
    return h

def main(msg: func.QueueMessage) -> None:
    payload = json.loads(msg.get_body().decode("utf-8"))
    run_id = payload["run_id"]

    runs_container = os.environ.get("BREEDING_RUNS_CONTAINER", "breeding-runs")
    images_container = os.environ.get("BREEDING_IMAGES_CONTAINER", "breeding-images")

    meta = get_json(runs_container, f"runs/{run_id}/meta.json")
    if not meta:
        return

    # status更新
    status = get_json(runs_container, f"runs/{run_id}/status.json") or {"run_id": run_id, "processed": 0, "failed": 0}
    status["status"] = "running"
    put_json(runs_container, f"runs/{run_id}/status.json", status)

    # preprocess defaults
    pp = meta.get("preprocess", {})
    orientation_policy = pp.get("orientation_policy", os.environ.get("DEFAULT_ORIENTATION_POLICY", "force_portrait"))
    max_side = int(pp.get("max_side", os.environ.get("DEFAULT_MAX_SIDE", "1024")))
    jpeg_quality = int(pp.get("jpeg_quality", os.environ.get("DEFAULT_JPEG_QUALITY", "85")))

    # 対象画像列挙
    blob_names = [b for b in list_blobs(images_container, meta["prefix"]) if b.lower().endswith((".jpg",".jpeg",".png",".webp",".bmp"))]
    blob_names = blob_names[: int(meta.get("max_images", 100))]

    items = []
    errors = []

    # 今回は試行用プロンプトで動かす（後で template_id により切替）
    system_text = SYSTEM_SEEDCOUNT
    user_text = USER_SEEDCOUNT
    prompt_hash = _hash_prompt(system_text, user_text)

    # metaにもhash保存（再現性用）
    meta["prompt_hash"] = prompt_hash
    put_json(runs_container, f"runs/{run_id}/meta.json", meta)

    for i, bn in enumerate(blob_names, start=1):
        image_id = bn.split("/")[-1]
        try:
            raw = get_blob_bytes(images_container, bn)
            img = preprocess_image_bytes(raw, orientation_policy=orientation_policy, max_side=max_side, jpeg_quality=jpeg_quality)

            txt = call_openai_vision(system_text, user_text, img)

            # JSONのみにする（壊れていたら例外に）
            obj = json.loads(txt)

            # image_idが無い場合は補完
            if isinstance(obj, dict):
                # 期待： {"traits":[...]}
                rec = {"image_id": image_id, "traits": obj.get("traits", [])}
            else:
                raise ValueError("model output is not dict")

            items.append(rec)
            status["processed"] = i
            put_json(runs_container, f"runs/{run_id}/status.json", status)

        except Exception as e:
            errors.append({"image_id": image_id, "reason": str(e)})
            status["failed"] = status.get("failed", 0) + 1
            put_json(runs_container, f"runs/{run_id}/status.json", status)

    result = {
        "run_id": run_id,
        "prompt_template_id": meta.get("prompt_template_id"),
        "prompt_version": meta.get("prompt_version"),
        "prompt_hash": meta.get("prompt_hash"),
        "items": items,
        "errors": errors
    }
    put_json(runs_container, f"runs/{run_id}/result.json", result)

    status["status"] = "succeeded" if len(errors) == 0 else "completed_with_errors"
    put_json(runs_container, f"runs/{run_id}/status.json", status)
