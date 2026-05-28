import json
from urllib.parse import parse_qs

from fastapi import HTTPException, Request


async def read_payload(request: Request) -> dict:
    content_type = request.headers.get("content-type", "")

    if "form" in content_type or "multipart" in content_type:
        form = await request.form()
        return dict(form)

    body = await request.body()
    if not body:
        return {}

    if "json" in content_type or not content_type:
        try:
            data = await request.json()
        except Exception as exc:
            raise HTTPException(status_code=400, detail="Invalid JSON body") from exc

        if isinstance(data, dict):
            return data
        raise HTTPException(status_code=400, detail="Request body must be an object")

    decoded_body = body.decode("utf-8")
    try:
        data = json.loads(decoded_body)
    except json.JSONDecodeError:
        data = None

    if isinstance(data, dict):
        return data

    parsed = parse_qs(decoded_body, keep_blank_values=True)
    if parsed:
        return {key: values[-1] for key, values in parsed.items()}

    raise HTTPException(status_code=400, detail="Unsupported request body")


def pick(payload: dict, *keys: str, default=None):
    for key in keys:
        value = payload.get(key)
        if value is not None:
            return value
    return default
