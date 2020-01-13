import json
import logging
import pathlib
from typing import Any, Dict, List, Tuple, Type

# ./tests/integration is in PYTHONPATH
from tests.impl.parsers.ios.openconfig_interfaces import interfaces as ios_if_parser
from tests.impl.parsers.ios.openconfig_vlan import vlans as ios_vlans_parser
from tests.impl.parsers.junos.openconfig_interfaces import interfaces as junos_if_parser
from tests.impl.parsers.junos.openconfig_vlan import vlans as junos_vlans_parser
from tests.impl.translators.ios.openconfig_interfaces import (
    interfaces as ios_if_translator,
)
from tests.impl.translators.ios.openconfig_vlan import vlans as ios_vlans_translator
from tests.impl.translators.junos.openconfig_interfaces import (
    interfaces as junos_if_translator,
)
from tests.impl.translators.junos.openconfig_vlan import vlans as junos_vlans_translator

from lxml import etree

import pytest

from yangify import parser, translator
from yangify.parser.text_tree import parse_indented_config
from yangify.translator.config_tree import ConfigTree

from yangson.datamodel import DataModel


logging_format = (
    "%(asctime)s - %(name)30s - %(levelname)8s - %(funcName)20s() - %(message)s"
)
logging.basicConfig(format=logging_format, level=logging.ERROR)

BASE = pathlib.Path(__file__).parent
dm = DataModel.from_file(
    f"{BASE}/../impl/yang-library-data.json", [f"{BASE}/../impl/yang-modules"]
)


class IOSParser(parser.RootParser):
    class Yangify(parser.ParserData):
        def init(self) -> None:
            self.root_native = parse_indented_config(self.root_native.splitlines())
            self.native = self.root_native

    interfaces = ios_if_parser.Interfaces
    vlans = ios_vlans_parser.Vlans


class JunosParser(parser.RootParser):
    class Yangify(parser.ParserData):
        def init(self) -> None:
            #  self.root_native = xml_to_dict(self.root_native)
            self.root_native = etree.fromstring(self.root_native)
            self.native = self.root_native

    interfaces = junos_if_parser.Interfaces
    vlans = junos_vlans_parser.Vlans


class IOSTranslator(translator.RootTranslator):
    class Yangify(translator.TranslatorData):
        def init(self) -> None:
            self.root_result = ConfigTree()
            self.result = self.root_result

        def post(self) -> None:
            self.root_result = self.root_result.to_string()

    interfaces = ios_if_translator.Interfaces
    vlans = ios_vlans_translator.Vlans


class JunoTranslator(translator.RootTranslator):
    class Yangify(translator.TranslatorData):
        def init(self) -> None:
            self.root_result = etree.Element("configuration")
            self.result = self.root_result

        def post(self) -> None:
            self.root_result = etree.tostring(
                self.root_result, pretty_print=True
            ).decode()

    interfaces = junos_if_translator.Interfaces
    vlans = junos_vlans_translator.Vlans


def get_test_cases(test: str) -> Dict[str, Any]:
    base = pathlib.Path(__file__).parent

    test_cases: List[Tuple[str, str, pathlib.Path]] = []
    ids: List[str] = []
    for platform_path in base.joinpath(f"data/{test}").iterdir():
        platform = platform_path.name
        for test_case_path in sorted(platform_path.iterdir()):
            test_case = test_case_path.name
            ids.append(f"{platform}_{test_case}")
            test_cases.append((platform, test_case, test_case_path))
    return {
        "argnames": "platform,test_case,test_case_path",
        "argvalues": test_cases,
        "ids": ids,
    }


def get_root_objects(
    platform: str,
) -> Tuple[Type[parser.RootParser], Type[translator.RootTranslator]]:
    if platform == "ios":
        return IOSParser, IOSTranslator
    elif platform == "junos":
        return JunosParser, JunoTranslator
    else:
        raise Exception(f"I have no idea what {platform} is")


class Test:
    @pytest.mark.parametrize(**get_test_cases("parse"))  # type: ignore
    def test_parser(
        self, platform: str, test_case: str, test_case_path: pathlib.Path
    ) -> None:
        with open(test_case_path.joinpath("config"), "r") as f:
            config = f.read()
        with open(test_case_path.joinpath("structured.json"), "r") as f:
            structured = json.load(f)

        parser_class, _ = get_root_objects(platform)
        parser = parser_class(dm, config)
        parsed_obj = parser.process()
        #  print(json.dumps(parsed_obj.raw_value()))
        assert parsed_obj.raw_value() == structured

    @pytest.mark.parametrize(**get_test_cases("translate"))  # type: ignore
    def test_translator(
        self, platform: str, test_case: str, test_case_path: pathlib.Path
    ) -> None:
        with open(test_case_path.joinpath("config"), "r") as f:
            config = f.read()
        with open(test_case_path.joinpath("structured.json"), "r") as f:
            structured = json.load(f)

        _, translator_class = get_root_objects(platform)
        translator = translator_class(dm, candidate=structured)
        translated_obj = translator.process()
        #  print(translated_obj)
        assert translated_obj == config

    @pytest.mark.parametrize(**get_test_cases("merge"))  # type: ignore
    def test_merge(
        self, platform: str, test_case: str, test_case_path: pathlib.Path
    ) -> None:
        with open(test_case_path.joinpath("data_candidate.json"), "r") as f:
            candidate = json.load(f)
        with open(test_case_path.joinpath("data_running.json"), "r") as f:
            running = json.load(f)
        with open(test_case_path.joinpath("res_merge"), "r") as f:
            expected = f.read()

        _, translator_class = get_root_objects(platform)
        translator = translator_class(
            dm, candidate=candidate, running=running, replace=False
        )
        translated_obj = translator.process()
        assert translated_obj == expected

    @pytest.mark.parametrize(**get_test_cases("merge"))  # type: ignore
    def test_replace(
        self, platform: str, test_case: str, test_case_path: pathlib.Path
    ) -> None:
        with open(test_case_path.joinpath("data_candidate.json"), "r") as f:
            candidate = json.load(f)
        with open(test_case_path.joinpath("data_running.json"), "r") as f:
            running = json.load(f)
        with open(test_case_path.joinpath("res_replace"), "r") as f:
            expected = f.read()

        _, translator_class = get_root_objects(platform)
        translator = translator_class(
            dm, candidate=candidate, running=running, replace=True
        )
        translated_obj = translator.process()
        assert translated_obj == expected

    @pytest.mark.parametrize(  # type: ignore
        "name,include,exclude",
        [
            ("none", [], []),
            ("if", ["/openconfig-interfaces:interfaces"], []),
            ("if_config", ["/openconfig-interfaces:interfaces/interface/config"], []),
            (
                "subif_config",
                [
                    "/openconfig-interfaces:interfaces/interface/subinterfaces/subinterface/config"  # noqa
                ],
                [],
            ),
            ("no_vlan", [], ["/openconfig-vlan:vlans"]),
            (
                "no_description",
                ["/openconfig-interfaces:interfaces/interface/config"],
                ["/openconfig-interfaces:interfaces/interface/config/description"],
            ),
        ],
        ids=["none", "if", "if_config", "subif_config", "no_vlan", "no_description"],
    )
    def test_parser_with_filter(
        self, name: str, include: List[str], exclude: List[str]
    ) -> None:
        test_case_path = BASE.joinpath(f"data/parse_with_filter/{name}")
        with open(test_case_path.joinpath("config"), "r") as f:
            config = f.read()
        with open(test_case_path.joinpath("structured.json"), "r") as f:
            structured = json.load(f)
        parser = IOSParser(dm, config, include=include, exclude=exclude)
        parsed_obj = parser.process(validate=False)
        assert parsed_obj.raw_value() == structured, json.dumps(parsed_obj.raw_value())
