from typing import List, Optional, cast

from tests.impl.helpers import json_helpers as jh

from yangify.parser import Parser


class SwitchedVlanConfig(Parser):
    def interface_mode(self) -> Optional[str]:
        v = jh.query('switchport.mode."#text"', self.yy.native)
        if v is not None:
            return cast(str, v.upper())
        else:
            return None

    def access_vlan(self) -> Optional[int]:
        v = jh.query('switchport.access.vlan."#text"', self.yy.native)
        if v is not None:
            return int(v)
        return None

    def trunk_vlans(self) -> Optional[List[str]]:
        v = jh.query('switchport.trunk.allowed.vlan."#text"', self.yy.native)
        if v is not None:
            return cast(List[str], v.split(","))
        return None


class SwitchedVlan(Parser):
    config = SwitchedVlanConfig
