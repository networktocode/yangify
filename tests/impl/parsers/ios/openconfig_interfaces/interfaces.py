from typing import Any, Dict, Iterator, Optional, Tuple, cast

from tests.impl.helpers import json_helpers as jh
from tests.impl.parsers.ios.openconfig_if_ethernet import ethernet

from yangify.parser import Parser, ParserData


class SubinterfaceConfig(Parser):
    def description(self) -> Optional[str]:
        return cast(Optional[str], jh.query('description."#text"', self.yy.native))

    def index(self) -> int:
        return int(self.yy.key.split(".")[-1])


class Subinterface(Parser):
    class Yangify(ParserData):
        def extract_elements(self) -> Iterator[Tuple[str, Dict[str, Any]]]:
            parent_key = self.keys["/openconfig-interfaces:interfaces/interface"]
            for k, v in self.root_native["interface"].items():
                if k.startswith(f"{parent_key}."):
                    yield k, v

    config = SubinterfaceConfig

    def index(self) -> int:
        return int(self.yy.key.split(".")[-1])


class Subinterfaces(Parser):
    subinterface = Subinterface


class InterfaceConfig(Parser):
    def description(self) -> Optional[str]:
        return cast(Optional[str], jh.query('description."#text"', self.yy.native))

    def enabled(self) -> bool:
        shutdown = jh.query('shutdown."#standalone"', self.yy.native)
        if shutdown:
            return False
        else:
            return True

    def name(self) -> str:
        return self.yy.key

    def type(self) -> Optional[str]:
        if "Ethernet" in self.yy.key:
            return "iana-if-type:ethernetCsmacd"
        return None


class Interface(Parser):
    class Yangify(ParserData):
        def extract_elements(self) -> Iterator[Tuple[str, Dict[str, Any]]]:
            for k, v in self.native["interface"].items():
                if k == "#text" or "." in k:
                    continue
                yield k, v

    config = InterfaceConfig
    subinterfaces = Subinterfaces
    ethernet = ethernet.Ethernet

    def name(self) -> str:
        return self.yy.key


class Interfaces(Parser):
    interface = Interface
