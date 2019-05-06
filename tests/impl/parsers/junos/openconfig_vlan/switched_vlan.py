from typing import List, Optional, cast

from yangify.parser import Parser


class SwitchedVlanConfig(Parser):
    def interface_mode(self) -> Optional[str]:
        mode = self.yy.native.xpath(
            "unit[name=0]/family/ethernet-switching/interface-mode"
        )
        if mode:
            return cast(str, mode[0].text.upper())
        return None

    def access_vlan(self) -> Optional[int]:
        vlan = self.yy.native.xpath(
            "unit[name=0]/family/ethernet-switching/vlan/members"
        )
        if vlan:
            return int(vlan[0].text)
        return None

    def trunk_vlans(self) -> Optional[List[str]]:
        vlans = self.yy.native.xpath(
            "unit[name=0]/family/ethernet-switching/vlan/members"
        )
        if vlans:
            return [v.text for v in vlans]
        return None


class SwitchedVlan(Parser):
    config = SwitchedVlanConfig
