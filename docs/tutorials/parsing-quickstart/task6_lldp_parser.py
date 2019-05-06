from typing import Any, Dict, Iterator, Optional, Tuple, cast
from yangify.parser import Parser, ParserData


class InterfaceConfig(Parser):
    """
    Implements openconfig-interfaces:interfaces/interface/config
    """

    def description(self) -> Optional[str]:
        return cast(Optional[str], self.yy.native.get("description", {}).get("#text"))

    def enabled(self) -> bool:
        shutdown = self.yy.native.get("shutdown", {}).get("#standalone")
        if shutdown:
            return False
        else:
            return True

    def name(self) -> str:
        return self.yy.key

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


class LLDPInterfaceInfo(Parser):
    def name(self) -> str:
        return self.yy.key


class LLDPInterface(Parser):
    class Yangify(ParserData):
        # While we have LLDP structured data, that is only active
        # neighbors found from the show lldp neighbors command
        # This LLDP interface is defined as the following within the model
        #      list interface {
        #        key "name";
        #        description
        #          "List of interfaces on which LLDP is enabled / available";
        #
        # Because of this, we're using the show run command to build out
        # the LLDP interfaces accessed in self.native['show run'] again.
        def extract_elements(self) -> Iterator[Tuple[str, Dict[str, Any]]]:
            for interface, data in self.native["show run"]["interface"].items():
                if interface == "#text":
                    continue
                no_lldp_config = (
                    data.get("no", {})
                    .get("lldp", {})
                    .get("enable", {})
                    .get("#standalone")
                )
                if no_lldp_config:
                    continue
                # skip any interfaces you want to...
                if interface.startswith("Loop"):
                    continue
                # `interface` is the interface name like GigabitEthernet1
                # `data` is the value of the dictionary from the text tree
                yield interface, data

    config = LLDPInterfaceInfo

    def name(self) -> str:
        # self.yy.key is equal to the key being returned
        # from the tuple in extract_elements
        return self.yy.key


class LLDPInterfaces(Parser):

    interface = LLDPInterface


class LldpConfigState(Parser):
    def system_name(self):
        return self.yy.native["show run"]["hostname"]["#text"]


class LLdp(Parser):
    config = LldpConfigState
    interfaces = LLDPInterfaces
