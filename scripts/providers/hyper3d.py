"""Hyper3D Rodin (hyper3d.ai) cloud text/image-to-3D adapter for scripts/gen_asset.py. stdlib only.

Flow (docs read 2026-11-10, https://docs.hyper3d.ai/en/get-started/quick-start and the
api-specification pages rodin-gen2-5, check-status, download-results):
  POST https://api.hyper3d.com/api/v2/rodin   multipart: images (file) or prompt, tier, geometry_file_format, ...
       -> {"uuid", "jobs": {"uuids", "subscription_key"}, "consumed"}
  POST /api/v2/status   {"subscription_key"} -> {"jobs": [{"uuid", "status": Waiting|Generating|Done|Failed}]}
  POST /api/v2/download {"task_uuid": uuid}  -> {"list": [{"name", "url"}]}
The GLB url is fetched without the key. Key: RODIN_API_KEY (the vendor's own name). Gate: HYPER3D_TERMS_REVIEWED.
API access needs a Business or Enterprise plan (https://hyper3d.ai/features/api).
"""
from pathlib import Path

from .cloud import MAX_GLB, THREED_TIMEOUT, CloudProvider, multipart

API_HOST = "api.hyper3d.com"
API_BASE = f"https://{API_HOST}/api/v2"
KEY_ENV = "RODIN_API_KEY"
TERMS_ENV = "HYPER3D_TERMS_REVIEWED"
# Always send the tier: omitted, the endpoint falls back to "Regular" (Gen-1/1.5). Base cost 0.5 credit for every
# Gen-2.5 tier except Extreme-High (+0.5). Medium needs "Full" API access; Basic access allows Low / Extreme-Low.
RODIN_TIER = "Gen-2.5-Medium"


class Hyper3DProvider(CloudProvider):
    name = "hyper3d"
    API_HOST = API_HOST
    KEY_ENV = KEY_ENV
    TERMS_ENV = TERMS_ENV
    MODEL = f"rodin {RODIN_TIER}"

    def _form(self, prompt=None, image=None):
        fields = [("tier", RODIN_TIER), ("geometry_file_format", "glb"), ("material", "PBR"),
                  ("mesh_mode", "Raw"), ("quality", "medium")]
        if prompt:
            fields.append(("prompt", prompt))
        files = [("images", f"concept.{image[1].split('/')[1]}", image[1], image[2])] if image else []
        return multipart(fields, files)

    def _run(self, out_path, timeout, prompt=None, image_path=None):
        key = self._key()
        Path(out_path).unlink(missing_ok=True)
        deadline = self.clock() + timeout
        task_id = None
        try:
            image = self.check_image(image_path) if image_path is not None else None
            body, ctype = self._form(prompt, image)
            created = self._api(f"{API_BASE}/rodin", deadline, key, body, ctype)
            if created.get("error") or not created.get("uuid"):
                raise RuntimeError(f"submit refused: {created.get('error') or created.get('message') or 'no uuid'}")
            task_id = created["uuid"]
            sub = (created.get("jobs") or {}).get("subscription_key")
            if not sub:
                raise RuntimeError(f"task {task_id} has no subscription_key")
            while True:
                jobs = self._post_json(f"{API_BASE}/status", {"subscription_key": sub}, deadline, key).get("jobs") or []
                states = [j.get("status") for j in jobs]
                if "Failed" in states:
                    raise RuntimeError(f"task {task_id} Failed")
                if states and all(s == "Done" for s in states):
                    break
                self._wait(deadline, f"task {task_id}")
            files = self._post_json(f"{API_BASE}/download", {"task_uuid": task_id}, deadline, key).get("list") or []
            glbs = [f for f in files if str(f.get("name", "")).lower().endswith(".glb")]
            if not glbs:
                raise RuntimeError(f"task {task_id} done but has no .glb in the download list")
            raw = self._download(glbs[0]["url"], deadline, MAX_GLB)
            return self._finish_glb(raw, out_path, task_id, ["POST", f"{API_BASE}/rodin"])
        except Exception as exc:
            raise self._fail(exc, key, task_id)

    def generate_3d(self, image_path, out_path, timeout=THREED_TIMEOUT):
        """Image-to-3D. Returns {"model","task_id","command","licence_gate"} or raises ProviderError."""
        return self._run(out_path, timeout, image_path=image_path)

    def generate_3d_from_text(self, prompt, out_path, timeout=THREED_TIMEOUT):
        """Text-to-3D (no image). Same return shape."""
        return self._run(out_path, timeout, prompt=prompt)
