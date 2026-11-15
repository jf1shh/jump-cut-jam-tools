"""Tripo (tripo3d.ai) cloud text/image-to-model adapter for scripts/gen_asset.py. stdlib only.

Flow (docs read 2026-11-10, https://developers.tripo3d.ai/en/docs/quick-start, .../generation-image-to-model/standard,
.../files, .../billing):
  POST https://openapi.tripo3d.ai/v3/files   multipart field "file" -> {"code": 0, "data": {"file_token"}}
  POST /v3/generation/image-to-model  {"input": file_token, "model", "texture", "pbr"} -> {"code": 0, "data": {"task_id"}}
  POST /v3/generation/text-to-model   {"prompt", "model", "texture", "pbr"}           -> same
  GET  /v3/tasks/<id> -> {"data": {"status", "progress", "output": {"model_url"}}}; status "success" is done,
       failed / cancelled / banned / expired are terminal. model_url expires after 5 minutes: downloaded at once,
       without the key. Failed and cancelled tasks are not charged (billing page).
Key: TRIPO_API_KEY (API platform key, not the web app). Gate: TRIPO_TERMS_REVIEWED.
"""
from pathlib import Path

from .cloud import MAX_GLB, THREED_TIMEOUT, CloudProvider, multipart

API_HOST = "openapi.tripo3d.ai"
API_BASE = f"https://{API_HOST}/v3"
KEY_ENV = "TRIPO_API_KEY"
TERMS_ENV = "TRIPO_TERMS_REVIEWED"
TRIPO_MODEL = "v3.1-20260211"  # "recommended" on the image-to-model page, 2026-11-10
FAILED = {"failed", "cancelled", "canceled", "banned", "expired"}


class TripoProvider(CloudProvider):
    name = "tripo"
    API_HOST = API_HOST
    KEY_ENV = KEY_ENV
    TERMS_ENV = TERMS_ENV
    MODEL = TRIPO_MODEL

    @staticmethod
    def _data(reply, what):
        if reply.get("code") != 0:
            raise RuntimeError(f"{what} refused: code {reply.get('code')} {reply.get('message') or ''}".strip())
        return reply.get("data") or {}

    def _run(self, out_path, timeout, prompt=None, image_path=None):
        key = self._key()
        Path(out_path).unlink(missing_ok=True)
        deadline = self.clock() + timeout
        task_id = None
        try:
            body = {"model": TRIPO_MODEL, "texture": True, "pbr": True}
            if image_path is not None:
                _, mime, data = self.check_image(image_path)
                if mime == "image/webp":
                    raise ValueError("Tripo file upload takes PNG or JPEG only")
                form, ctype = multipart([], [("file", f"concept.{mime.split('/')[1]}", mime, data)])
                token = self._data(self._api(f"{API_BASE}/files", deadline, key, form, ctype), "upload").get("file_token")
                if not token:
                    raise RuntimeError("upload returned no file_token")
                body["input"] = token
                url = f"{API_BASE}/generation/image-to-model"
            else:
                body["prompt"] = prompt
                url = f"{API_BASE}/generation/text-to-model"
            task_id = self._data(self._post_json(url, body, deadline, key), "create").get("task_id")
            if not task_id:
                raise RuntimeError("create returned no task_id")
            while True:
                task = self._data(self._api(f"{API_BASE}/tasks/{task_id}", deadline, key), "task query")
                status = str(task.get("status", "")).lower()
                if status == "success":
                    break
                if status in FAILED:
                    raise RuntimeError(f"task {task_id} {status}")
                self._wait(deadline, f"task {task_id}")
            model_url = (task.get("output") or {}).get("model_url")
            if not model_url:
                raise RuntimeError(f"task {task_id} succeeded but has no model_url")
            raw = self._download(model_url, deadline, MAX_GLB)
            return self._finish_glb(raw, out_path, task_id, ["POST", url])
        except Exception as exc:
            raise self._fail(exc, key, task_id)

    def generate_3d(self, image_path, out_path, timeout=THREED_TIMEOUT):
        """Image-to-model. Returns {"model","task_id","command","licence_gate"} or raises ProviderError."""
        return self._run(out_path, timeout, image_path=image_path)

    def generate_3d_from_text(self, prompt, out_path, timeout=THREED_TIMEOUT):
        """Text-to-model. Same return shape."""
        return self._run(out_path, timeout, prompt=prompt)
