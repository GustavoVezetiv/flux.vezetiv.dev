from __future__ import annotations
import json
from models import ImobiPackage


def load_package_bytes(data: bytes) -> ImobiPackage:
    raw = json.loads(data.decode("utf-8"))
    return ImobiPackage.model_validate(raw)


def package_to_json(pkg: ImobiPackage) -> str:
    return pkg.model_dump_json(indent=2, exclude_none=True)
