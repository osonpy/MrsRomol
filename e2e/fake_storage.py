"""
Minimal stand-in for Supabase Storage, for the local demo shop only.
Implements just what the API uses: upload, delete, public read and signed
URLs. Files live in .demo/storage/<bucket>/<path>.

    uv run python e2e/fake_storage.py      # listens on :54330
"""
import json
from pathlib import Path

import uvicorn
from starlette.applications import Starlette
from starlette.requests import Request
from starlette.responses import FileResponse, JSONResponse, Response
from starlette.routing import Route

ROOT = (Path(__file__).resolve().parent.parent / ".demo" / "storage").resolve()


def _file(bucket: str, path: str) -> Path:
    p = (ROOT / bucket / path).resolve()
    if ROOT not in p.parents:
        raise ValueError("bad path")
    return p


async def upload(request: Request) -> Response:
    bucket, path = request.path_params["bucket"], request.path_params["path"]
    form = await request.form()
    upload = form["file"]
    target = _file(bucket, path)
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_bytes(await upload.read())
    return JSONResponse({"Key": f"{bucket}/{path}", "Id": path})


async def remove(request: Request) -> Response:
    bucket = request.path_params["bucket"]
    body = json.loads(await request.body() or b"{}")
    for path in body.get("prefixes", []):
        _file(bucket, path).unlink(missing_ok=True)
    return JSONResponse([])


async def sign(request: Request) -> Response:
    bucket, path = request.path_params["bucket"], request.path_params["path"]
    return JSONResponse({"signedURL": f"/object/sign/{bucket}/{path}?token=demo"})


async def read(request: Request) -> Response:
    target = _file(request.path_params["bucket"], request.path_params["path"])
    if not target.is_file():
        return Response(status_code=404)
    return FileResponse(target, headers={"Access-Control-Allow-Origin": "*", "Cache-Control": "no-cache"})


app = Starlette(routes=[
    Route("/storage/v1/object/public/{bucket}/{path:path}", read, methods=["GET"]),
    Route("/storage/v1/object/sign/{bucket}/{path:path}", sign, methods=["POST"]),
    Route("/storage/v1/object/sign/{bucket}/{path:path}", read, methods=["GET"]),
    Route("/storage/v1/object/{bucket}/{path:path}", upload, methods=["POST", "PUT"]),
    Route("/storage/v1/object/{bucket}", remove, methods=["DELETE"]),
])

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=54330, log_level="warning")
