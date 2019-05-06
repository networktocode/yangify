from typing import List, Optional

from tests.impl.helpers import xml_helpers as xh

from lxml import etree

from yangify.translator import Translator, TranslatorData

from yangson.instance import NonexistentInstance


class SwitchedVlanConfig(Translator):
    class Yangify(TranslatorData):
        def post_process(self) -> None:
            # it is tricky as junos reuses the container vlan
            # for both access and trunked vlans. What we do is
            # check after the post-process if non is set and
            # remove them
            try:
                data = self.candidate.goto(self.path).value
            except NonexistentInstance:
                data = {}
            if (
                not data.get("access-vlan")
                and not data.get("trunk-vlans")
                and not self.replace
            ):
                etree.SubElement(self.result, "vlan", delete="delete")

    def interface_mode(self, value: Optional[str]) -> None:
        if value:
            etree.SubElement(self.yy.result, "interface-mode").text = value.lower()
        else:
            etree.SubElement(self.yy.result, "interface-mode", delete="delete")

    def access_vlan(self, value: Optional[str]) -> None:
        mode = self.yy.candidate.goto(self.yy.path).value.get("interface-mode")
        if value and mode == "ACCESS":
            vlan = etree.SubElement(self.yy.result, "vlan")
            etree.SubElement(vlan, "members").text = str(value)

    def trunk_vlans(self, value: Optional[List[str]]) -> None:
        try:
            mode = self.yy.candidate.goto(self.yy.path).value.get("interface-mode")
        except NonexistentInstance:
            return
        if value and mode == "TRUNK":
            vlan = etree.SubElement(self.yy.result, "vlan")
            for v in value:
                etree.SubElement(vlan, "members").text = str(v)


class SwitchedVlan(Translator):
    config = SwitchedVlanConfig

    class Yangify(TranslatorData):
        def pre_process(self) -> None:
            self.result = etree.Element("ethernet-switching")

        def post_process(self) -> None:
            if len(self.result):
                path = f"/configuration/interfaces/interface[name='{self.key}']/unit[name=0]/family"
                family = xh.find_or_create(self.root_result, path)
                family.append(self.result)
