from typing import List, Tuple

import pytest

from yangify.model_filter import ModelFilter


tests: List[Tuple[List[str], List[str], str, bool]] = [
    (["/openconfig-interfaces:interfaces/interface/config"], [], "", True),
    (
        ["/openconfig-interfaces:interfaces/interface/config"],
        [],
        "/openconfig-interfaces:interfaces/interface",
        True,
    ),
    (
        ["/openconfig-interfaces:interfaces/interface/config"],
        [],
        "/openconfig-interfaces:interfaces/interface/config",
        True,
    ),
    (
        ["/openconfig-interfaces:interfaces/interface/config"],
        [],
        "/openconfig-vlan:vlans",
        False,
    ),
    (
        ["/openconfig-interfaces:interfaces/interface/config"],
        ["/openconfig-vlan:vlans"],
        "/openconfig-interfaces:interfaces/interface/config",
        True,
    ),
    (
        ["/openconfig-interfaces:interfaces/interface/config"],
        ["/openconfig-vlan:vlans"],
        "/openconfig-vlan:vlans",
        False,
    ),
]


class Test:
    @pytest.mark.parametrize("include,exclude,path,result", tests)  # type: ignore
    def test_model_filter(
        self, include: List[str], exclude: List[str], path: str, result: bool
    ) -> None:
        mf = ModelFilter(include, exclude)
        assert mf.check(path) == result
