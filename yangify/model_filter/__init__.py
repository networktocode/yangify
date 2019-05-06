from typing import List


class ModelFilter:
    """
    This class helps filtering YANG paths

    Attributes:
        include: Paths starting with strings in this list will be included
        exclude: Paths matching exactly strings in this list will be excluded
    """

    def __init__(self, include: List[str], exclude: List[str]) -> None:
        self.include = include or [""]
        self.exclude = exclude

    def _check_inc(self, path: str, inc: str) -> bool:
        return inc.startswith(path) or path.startswith(inc)

    def check(self, path: str) -> bool:
        """
        ``True`` if the path matches the criteria to be included
        """
        return (
            any([self._check_inc(path, i) for i in self.include])
            and path not in self.exclude
        )
