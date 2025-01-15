from typing import Any
from functools import reduce


def extract_nested_fields(data: dict[str, Any], paths: dict[str, Any]) -> dict[str, Any]:
    """
    This method is used to map one nested dict to another linear dict
    """

    def get_field(d, key):
        if isinstance(d, list) and len(d) > 0:
            return d[0].get(key) if d[0] else None
        return d.get(key) if d else None

    return {key: reduce(get_field, p.split('.'), data) for key, p in paths.items()}
