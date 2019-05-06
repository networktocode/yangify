from typing import Optional

from yangify.translator import Translator, TranslatorData, unneeded


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
            self.result = self.root_result.new_section(f"vlan {self.key}")

        def post_process(self) -> None:
            self.result.add_command("   exit\n!")

    vlan_id = unneeded

    config = VlanConfig


class Vlans(Translator):
    vlan = Vlan
