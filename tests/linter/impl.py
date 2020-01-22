from typing import Any, Optional

from yangify.parser import Parser, ParserData, RootParser
from yangify.translator import RootTranslator, Translator


class InterfaceConfigWarnings(Parser):
    class Yangify(ParserData):
        path = "/openconfig-interfaces:interfaces/interface/config"
        metadata = {"a": 1, "b": 2}

    def description(self) -> Optional[str]:
        return ""

    def enabled(self) -> bool:
        return True

    def name(self) -> str:
        return self.yy.key

    def type(self) -> Optional[str]:
        return ""

    def extra(self) -> None:
        return


class InterfaceConfigCorrect(Parser):
    class Yangify(ParserData):
        path = "/openconfig-interfaces:interfaces/interface/config"
        metadata = {"a": 1, "b": 2}

    def description(self) -> Optional[str]:
        return ""

    def enabled(self) -> bool:
        return True

    def name(self) -> str:
        return self.yy.key

    def type(self) -> Optional[str]:
        return ""

    def mtu(self) -> Optional[int]:
        return 0


class InterfaceConfigMissingImplements(Parser):
    pass


class InterfaceConfigWrongPath(Parser):
    class Yangify(ParserData):
        path = "/openconfig-interfaces:interfaces/interface/conf"

    pass


class InterfaceConfigInvalidPath(Parser):
    class Yangify(ParserData):
        path = "/sdadasd"

    pass


class SwitchedVlan(Parser):
    class Yangify(ParserData):
        path = "/openconfig-vlan:switched-vlan"

    pass


class Ethernet(Parser):
    class Yangify(ParserData):
        path = "/openconfig-interfaces:interfaces/interface/openconfig-if-ethernet:ethernet"

    switched_vlan = SwitchedVlan


class Interface(Parser):
    class Yangify(ParserData):
        path = "/openconfig-interfaces:interfaces/interface"

    config = InterfaceConfigWarnings
    ethernet = Ethernet

    def name(self) -> str:
        return self.yy.key


class Interfaces(Parser):
    class Yangify(ParserData):
        path = "/openconfig-interfaces:interfaces"

    interface = Interface


class Vlan(Parser):
    class Yangify(ParserData):
        path = "/openconfig-vlan:vlans/vlan"


class Vlans(Parser):
    class Yangify(ParserData):
        path = "/openconfig-vlan:vlans"

    vlan = Vlan


class RootP(RootParser):
    interfaces = Interfaces
    vlans = Vlans


class RootT(RootTranslator):
    class interfaces(Translator):
        class Yangify(ParserData):
            path = "/openconfig-interfaces:interfaces"

        class interface(Translator):
            class Yangify(ParserData):
                path = "/openconfig-interfaces:interfaces/interface"

            class config(Translator):
                class Yangify(ParserData):
                    path = "/openconfig-interfaces:interfaces/interface/config"

                def description(self, *args: Any, **kwargs: Any) -> None:
                    return None

                def name(self, *args: Any, **kwargs: Any) -> None:
                    return None

                def type(self, *args: Any, **kwargs: Any) -> None:
                    return None

            class aggregation(Translator):
                class Yangify(ParserData):
                    path = "/openconfig-interfaces:interfaces/interface/aggregation"

                pass

            def name(self, *args: Any, **kwargs: Any) -> None:
                return None

    class vlans(Translator):
        class Yangify(ParserData):
            path = "/openconfig-vlan:vlans"

        class vlan(Translator):
            class Yangify(ParserData):
                path = "/openconfig-vlan:vlans/vlan"


class MissingForwardSlashPath(Parser):
    class Yangify(ParserData):
        path = "openconfig-interfaces:interfaces/interface/conf"

    pass
