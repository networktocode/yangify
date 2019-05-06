from typing import Any, Dict

import jmespath


def query(query: str, data: Dict[str, Any], force_list: bool = False) -> Any:
    res = jmespath.search(query, data)
    if res is None and force_list:
        return []
    if not isinstance(res, list) and force_list:
        return [res]
    return res
