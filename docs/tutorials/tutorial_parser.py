from typing import Any, Dict, Iterator, Optional, Tuple, cast

from yangify.parser import Parser, ParserData


class SubinterfaceConfig(Parser):
    """
    Implements openconfig-interfaces:interfaces/interface/subinterfaces/subinterface/config
    """

    def description(self) -> Optional[str]:
        return cast(Optional[str], self.yy.native.get("description", {}).get("#text"))

    def index(self) -> int:
        return int(self.yy.key.split(".")[-1])


class Subinterface(Parser):
    """
    Implements openconfig-interfaces:interfaces/interface/subinterfaces/subinterface
    """

    class Yangify(ParserData):
        def extract_elements(self) -> Iterator[Tuple[str, Dict[str, Any]]]:
            """
            IOS subinterfaces are in the root of the configuration and named following
            the format ``$parent_interface.$index``. The model specifies the key is
            the $index, which is just a number. These means we will need to:

            1. Iterate over all the interfaces
            2. Filter the ones that don't start by `$parent_interface.`
            3. Extract the $index and return it
            """
            # self.keys keeps a record of all the keys found so far in the current
            # object. To access them you can use the full YANG path
            parent_key = self.keys["/openconfig-interfaces:interfaces/interface"]
            for k, v in self.root_native["interface"].items():
                if k.startswith(f"{parent_key}."):
                    yield k, v

    config = SubinterfaceConfig

    def index(self) -> int:
        return int(self.yy.key.split(".")[-1])


class Subinterfaces(Parser):
    """
    Implements openconfig-interfaces:interfaces/interface/subinterfaces
    """

    subinterface = Subinterface


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


class Interface(Parser):
    """
    Implements openconfig-interfaces:interfaces/interface
    """

    class Yangify(ParserData):
        def extract_elements(self) -> Iterator[Tuple[str, Dict[str, Any]]]:
            """
            IOS interfaces are in the root of the configuration. However,
            subinterfaces are also in the root of the configuration. For
            that reason we will have to make sure that we filter the
            subinterfaces as we iterate over all the interfaces in the root
            of the configuration. That's should be as easy as checking that
            the interface name has not dot in it.
            """
            for k, v in self.native["interface"].items():
                # k == "#text" is due to a harmless artifact in the
                # parse_indented_config function that needs to be addressed
                if k == "#text" or "." in k:
                    continue
                yield k, v

    config = InterfaceConfig
    subinterfaces = Subinterfaces

    def name(self) -> str:
        return self.yy.key


class Interfaces(Parser):
    """
    Implements openconfig-interfaces:interfaces
    """

    interface = Interface


class VlanConfig(Parser):
    def vlan_id(self) -> int:
        return int(self.yy.key)

    def name(self) -> Optional[str]:
        v = self.yy.native.get("name", {}).get("#text")
        if v is not None:
            return str(v)
        else:
            return None

    def status(self) -> str:
        if self.yy.native.get("shutdown", {}).get("#standalone"):
            return "SUSPENDED"
        else:
            return "ACTIVE"


class Vlan(Parser):
    class Yangify(ParserData):
        def extract_elements(self) -> Iterator[Tuple[str, Dict[str, Any]]]:
            for k, v in self.native["vlan"].items():
                if k == "#text":
                    continue
                yield k, cast(Dict[str, Any], v)

    config = VlanConfig

    def vlan_id(self) -> int:
        return int(self.yy.key)


class Vlans(Parser):
    vlan = Vlan
