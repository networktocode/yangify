from typing import Any, Dict, Iterator, Optional, Tuple, cast

from tests.impl.helpers import json_helpers as jh

from yangify.parser import Parser, ParserData


class VlanConfig(Parser):
    def vlan_id(self) -> int:
        return int(self.yy.key)

    def name(self) -> Optional[str]:
        v = jh.query('name."#text"', self.yy.native)
        if v is not None:
            return str(v)
        else:
            return None

    def status(self) -> str:
        if jh.query('shutdown."#standalone"', self.yy.native):
            return "SUSPENDED"
        else:
            return "ACTIVE"


class Vlan(Parser):
    class Yangify(ParserData):
        def extract_elements(self) -> Iterator[Tuple[str, Dict[str, Any]]]:
            for k, v in self.native["vlan"].items():
                if k == "#text":
                    continue
                yield k, cast(Dict[str, Any], v)

    config = VlanConfig

    def vlan_id(self) -> int:
        return int(self.yy.key)


class Vlans(Parser):
    vlan = Vlan
