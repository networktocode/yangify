from tests.impl.translators.junos.openconfig_vlan import switched_vlan

from yangify.translator import Translator


class Ethernet(Translator):
    switched_vlan = switched_vlan.SwitchedVlan
