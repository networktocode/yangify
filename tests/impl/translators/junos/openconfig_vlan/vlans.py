from typing import Optional

from lxml import etree

from yangify.translator import Translator, TranslatorData, unneeded


class VlanConfig(Translator):
    vlan_id = unneeded

    def name(self, value: Optional[str]) -> None:
        if value:
            etree.SubElement(self.yy.result, "name").text = value
        else:
            etree.SubElement(self.yy.result, "name", delete="delete")

    def status(self, value: Optional[str]) -> None:
        if value == "ACTIVE":
            etree.SubElement(self.yy.result, "disable", delete="delete")
        else:
            etree.SubElement(self.yy.result, "disable")


class Vlan(Translator):
    class Yangify(TranslatorData):
        def pre_process_list(self) -> None:
            if self.to_remove and not self.replace:
                for element in self.to_remove:
                    iface = etree.SubElement(self.result, "vlan", delete="delete")
                    etree.SubElement(iface, "vlan-id").text = str(
                        element.value["vlan-id"]
                    )

        def pre_process(self) -> None:
            self.result = etree.SubElement(self.result, "vlan")
            etree.SubElement(self.result, "vlan-id").text = str(self.key)

    vlan_id = unneeded

    config = VlanConfig


class Vlans(Translator):
    class Yangify(TranslatorData):
        def pre_process(self) -> None:
            self.result = etree.SubElement(self.root_result, "vlans")
            if self.replace:
                self.result.attrib["replace"] = "replace"

    vlan = Vlan
