from typing import Any, Dict, Iterator, Tuple
from yangify.parser import Parser, ParserData


class InterfaceConfig(Parser):
    """
    Implements openconfig-interfaces:interfaces/interface/config
    """

    def name(self) -> str:
        return self.yy.key

    def enabled(self) -> bool:
        shutdown = self.yy.native.get("shutdown", {}).get("#standalone")
        if shutdown:
            return False
        else:
            return True


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
