from typing import Any, Iterator, Optional, Tuple, cast

from tests.impl.parsers.junos.openconfig_if_ethernet import ethernet

from yangify.parser import Parser, ParserData


class SubinterfaceConfig(Parser):
    def description(self) -> Optional[str]:
        return cast(Optional[str], self.yy.native.findtext("description"))

    def index(self) -> int:
        return int(self.yy.key)


class Subinterface(Parser):
    class Yangify(ParserData):
        def extract_elements(self) -> Iterator[Tuple[str, Any]]:
            for i in self.native.xpath("unit"):
                yield i.findtext("name"), i

    config = SubinterfaceConfig

    def index(self) -> int:
        return int(self.yy.key)


class Subinterfaces(Parser):
    subinterface = Subinterface


class InterfaceConfig(Parser):
    def description(self) -> Optional[str]:
        # configuration really is under units/subifaces
        pass

    def enabled(self) -> bool:
        return self.yy.native.find("disable") is None

    def name(self) -> str:
        return self.yy.key

    def type(self) -> Optional[str]:
        if any([self.yy.key.startswith(prefix) for prefix in ["ge", "xe"]]):
            return "iana-if-type:ethernetCsmacd"
        elif self.yy.key.startswith("lo"):
            return "iana-if-type:softwareLoopback"
        else:
            raise Exception(f"don't know the type for {self.yy.key}")


class Interface(Parser):
    class Yangify(ParserData):
        def extract_elements(self) -> Iterator[Tuple[str, Any]]:
            for i in self.native.xpath("/configuration/interfaces/interface"):
                yield i.findtext("name"), i

    config = InterfaceConfig
    subinterfaces = Subinterfaces
    ethernet = ethernet.Ethernet

    def name(self) -> str:
        return self.yy.key


class Interfaces(Parser):
    interface = Interface
