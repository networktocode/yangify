from typing import Any, Dict, List

from yangson import instance
from yangson.datamodel import DataModel


def obj_from_raw(
    library: str, paths: List[str], raw: Dict[str, Any]
) -> instance.RootNode:
    dm = DataModel.from_file(library, paths)
    return dm.from_raw(raw)


__all__ = ("obj_from_raw",)
