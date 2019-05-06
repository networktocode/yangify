from typing import Any, Dict, Iterator, Optional, Tuple, cast
from yangify.parser import Parser, ParserData


class InterfaceConfig(Parser):
    """
    Implements openconfig-interfaces:interfaces/interface/config
    """

    def description(self) -> Optional[str]:
        return cast(Optional[str], self.yy.native.get("description", {}).get("#text"))

    def name(self) -> str:
        return self.yy.key

    def enabled(self) -> bool:
        shutdown = self.yy.native.get("shutdown", {}).get("#standalone")
        if shutdown:
            return False
        else:
            return True

    def type(self) -> str:
        if "Ethernet" in self.yy.key:
            return "iana-if-type:ethernetCsmacd"
        elif "Loopback" in self.yy.key:
            return "iana-if-type:softwareLoopback"
        else:
            raise ValueError(f"don't know type for interface {self.yy.key}")

    def loopback_mode(self) -> bool:

        if "Loopback" in self.yy.key:
            return True
        return False


class Interface(Parser):
    """
    Implements openconfig-interfaces:interfaces/interface
    """

    class Yangify(ParserData):
        def extract_elements(self) -> Iterator[Tuple[str, Dict[str, Any]]]:
            for interface, data in self.native["show run"]["interface"].items():
                if interface == "#text" or "." in interface:
                    continue
                yield interface, data

    config = InterfaceConfig

    def name(self) -> str:
        return self.yy.key


class Interfaces(Parser):
    """
    Implements openconfig-interfaces:interfaces
    """

    interface = Interface


class LldpConfigState(Parser):
    def system_name(self):
        return self.yy.native["show run"]["hostname"]["#text"]


class LLdp(Parser):
    config = LldpConfigState
