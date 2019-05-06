from typing import Any, Dict, Iterator, Tuple
from yangify.parser import Parser, ParserData


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

    def name(self) -> str:
        return self.yy.key


class Interfaces(Parser):
    """
    Implements openconfig-interfaces:interfaces
    """

    interface = Interface
