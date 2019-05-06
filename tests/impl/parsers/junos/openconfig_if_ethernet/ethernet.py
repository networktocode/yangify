from tests.impl.parsers.junos.openconfig_vlan import switched_vlan

from yangify.parser import Parser


class Ethernet(Parser):
    switched_vlan = switched_vlan.SwitchedVlan
