from typing import Any, Dict, Optional

from yangify.translator import Translator, TranslatorData, unneeded

from yangson.instance import NonexistentInstance


class SubinterfaceConfig(Translator):
    """
    Implements openconfig-interfaces:interfaces/interface/subinterfaces/subinterface/config
    """

    index = unneeded

    def description(self, value: Optional[str]) -> None:
        if value:
            self.yy.result.add_command(f"   description {value}")
        else:
            self.yy.result.add_command(f"   no description")


class Subinterface(Translator):
    """
    Implements openconfig-interfaces:interfaces/interface/subinterfaces/subinterface
    """

    class Yangify(TranslatorData):
        def pre_process_list(self) -> None:
            """
            If we need to remove itnerfaces we do it here. However, will need to
            get the key of the parent interface first as we will need it
            to remove the subinterfaces. Remember that subinterfaces in openconfig
            are referenced by their index and don't have a fully qualified name
            """
            parent_key = self.keys["/openconfig-interfaces:interfaces/interface"]
            for element in self.to_remove:
                iface_name = f"{parent_key}.{element['index']}"
                self.root_result.add_command(f"no interface {iface_name}")

        def pre_process(self) -> None:
            """
            We create a placeholder for our configuration in self.result, we attach it to
            self.root_result and also default the subinterface if we are in replace mode
            """
            parent_key = self.keys["/openconfig-interfaces:interfaces/interface"]
            self.keys["subinterface_key"] = f"{parent_key}.{self.key}"
            path = f"interface {self.keys['subinterface_key']}"
            if self.replace:
                self.root_result.add_command(
                    f"no interface {self.keys['subinterface_key']}"
                )
            self.result = self.root_result.new_section(path)

        def post_process(self) -> None:
            """
            After we are doing processing the interface we can either
            remove entirely the interface from the configuration if it's empty
            or add_command exit\n! to the commands
            """
            path = f"interface {self.keys['subinterface_key']}"
            if not self.result:
                self.root_result.pop_section(path)
            else:
                self.result.add_command("   exit\n!")

    index = unneeded
    config = SubinterfaceConfig


class Subinterfaces(Translator):
    """
    Implements openconfig-interfaces:interfaces/interface/subinterfaces
    """

    subinterface = Subinterface


class InterfaceConfig(Translator):
    """
    Implements openconfig-interfaces:interfaces/interface/config
    """

    name = unneeded
    type = unneeded

    def description(self, value: Optional[str]) -> None:
        if value:
            self.yy.result.add_command(f"   description {value}")
        else:
            self.yy.result.add_command(f"   no description")

    def enabled(self, value: Optional[bool]) -> None:
        if value:
            self.yy.result.add_command(f"   no shutdown")
        else:
            self.yy.result.add_command(f"   shutdown")


class Interface(Translator):
    """
    Implements openconfig-interfaces:interfaces/interface
    """

    class Yangify(TranslatorData):
        def _remove_subinterfaces(self, interface: Dict[str, Any]) -> None:
            """
            A helper function to remove subinterfaces.
            """
            subifaces = interface.get("subinterfaces", {}).get("subinterface", [])
            for subiface in subifaces:
                self.root_result.add_command(
                    f"no interface {self.key}.{subiface['index']}"
                )

        def pre_process_list(self) -> None:
            """
            If we have interfaces to remove we do so before processing the list of interfaces.
            """
            for element in self.to_remove:
                self.result.add_command(f"default interface {element['name']}")
                self._remove_subinterfaces(element)

        def pre_process(self) -> None:
            """
            Before processing a given interface we are going to do a couple of things:

            1. if we are replacing the configuration we default the interface and its
               subinterfaces
            2. We create a placeholder for the interface configuration and we set it
               in self.result
            """
            if self.replace:
                self.root_result.add_command(f"default interface {self.key}")
                if self.running is not None:
                    # self.running.goto(self.path).value is going to return the running
                    # value of the current interface
                    try:
                        self._remove_subinterfaces(self.running.goto(self.path).value)
                    except NonexistentInstance:
                        # if it's a candidate interface self.running.goto(self.path) will
                        # raise this exception
                        pass
            path = f"interface {self.key}"
            # we insert it as soon as possible to maintain order
            self.result = self.root_result.new_section(path)

        def post_process(self) -> None:
            """
            After we are doing processing the interface we can either
            remove entirely the interface from the configuration if it's empty
            or add_command exit\n! to the commands
            """
            path = f"interface {self.key}"
            if not self.result:
                self.root_result.pop_section(path)
            else:
                self.result.add_command("   exit\n!")

    name = unneeded

    subinterfaces = Subinterfaces
    config = InterfaceConfig


class Interfaces(Translator):
    """
    Implements openconfig-interfaces:interfaces

    Using a :obj:`yangify.translator.config_tree.ConfigTree` object for the result
    """

    interface = Interface


class VlanConfig(Translator):
    vlan_id = unneeded

    def name(self, value: Optional[str]) -> None:
        if value:
            self.yy.result.add_command(f"   name {value}")
        else:
            self.yy.result.add_command(f"   no name")

    def status(self, value: Optional[str]) -> None:
        if value == "SUSPENDED":
            self.yy.result.add_command(f"   shutdown")
        else:
            self.yy.result.add_command(f"   no shutdown")


class Vlan(Translator):
    class Yangify(TranslatorData):
        def pre_process_list(self) -> None:
            if self.to_remove:
                for element in self.to_remove:
                    self.result.add_command(f"no vlan {element['vlan-id']}")

        def pre_process(self) -> None:
            if self.replace:
                self.root_result.add_command(f"no vlan {self.key}")
            self.result = self.result.new_section(f"vlan {self.key}")

        def post_process(self) -> None:
            self.result.add_command("   exit\n!")

    vlan_id = unneeded

    config = VlanConfig


class Vlans(Translator):
    vlan = Vlan
