import pathlib
import logging
from typing import Any, Dict, Iterator, Tuple, cast

from yangify import parser

from yangson.datamodel import DataModel


BASE = pathlib.Path(__file__).parent
dm = DataModel.from_file(
    f"{BASE}/yang/simple/yang-library-data.json", [f"{BASE}/yang/simple/"]
)


test_data = {
    "element1": {
        "config": {"description": "this is element1.config.description"},
        "state": {"description": "this is element1.state.description"},
    },
    "element2": {
        "config": {"description": "this is element2.config.description"},
        "state": {"description": "this is element2.state.description"},
    },
}

test_expected_config = {
    "yangify-tests:start": {
        "elements": {
            "element": [
                {
                    "name": "element1",
                    "config": {"description": "this is element1.config.description"},
                },
                {
                    "name": "element2",
                    "config": {"description": "this is element2.config.description"},
                },
            ]
        }
    }
}


test_expected_state = {
    "yangify-tests:start": {
        "elements": {
            "element": [
                {
                    "name": "element1",
                    "state": {"description": "this is element1.state.description"},
                },
                {
                    "name": "element2",
                    "state": {"description": "this is element2.state.description"},
                },
            ]
        }
    }
}


class ConfigParser(parser.Parser):
    class Yangify(parser.ParserData):
        def pre_process(self) -> None:
            self.native = self.native["config"]

    def description(self) -> str:
        return cast(str, self.yy.native["description"])


class StateParser(parser.Parser):
    def description(self) -> str:
        return cast(str, self.yy.native["state"]["description"])


class ElementParser(parser.Parser):
    class Yangify(parser.ParserData):
        def extract_elements(self) -> Iterator[Tuple[str, Dict[str, Any]]]:
            for k, v in test_data.items():
                yield k, v

    config = ConfigParser
    state = StateParser

    def name(self) -> str:
        return self.yy.key


class ElementsParser(parser.Parser):
    element = ElementParser


class StartParser(parser.Parser):
    elements = ElementsParser


class RootTestParser(parser.RootParser):

    start = StartParser


class RootTestParserWithExtra(parser.RootParser):
    """
    This is just a sample parser similar to RootTestParser
    but that asserts at different points that `extra`
    is set to a predetermined value
    """

    class start(parser.Parser):
        class elements(parser.Parser):
            class element(parser.Parser):
                class Yangify(parser.ParserData):
                    def extract_elements(self) -> Iterator[Tuple[str, Dict[str, Any]]]:
                        assert self.extra == {"os_version": "test"}
                        for k, v in test_data.items():
                            yield k, v

                def name(self) -> str:
                    assert self.yy.extra == {"os_version": "test"}
                    return self.yy.key

                class config(parser.Parser):
                    class Yangify(parser.ParserData):
                        def pre_process(self) -> None:
                            assert self.extra == {"os_version": "test"}
                            self.native = self.native["config"]

                    def description(self) -> str:
                        assert self.yy.extra == {"os_version": "test"}
                        return cast(str, self.yy.native["description"])

                class state(parser.Parser):
                    def description(self) -> str:
                        assert self.yy.extra == {"os_version": "test"}
                        return cast(str, self.yy.native["state"]["description"])


class NotInModel(parser.Parser):
    def description(self) -> str:
        return "doesn't do anything"


class WarnTestParser(parser.RootParser):
    start = StartParser
    notinmodel = NotInModel


class Test:
    def test_parse_all(self) -> None:
        parser = RootTestParser(dm, test_data, config=True, state=True)
        parsed_obj = parser.process()
        assert parsed_obj.raw_value() == {
            "yangify-tests:start": {
                "elements": {
                    "element": [
                        {
                            "name": "element1",
                            "config": {
                                "description": "this is element1.config.description"
                            },
                            "state": {
                                "description": "this is element1.state.description"
                            },
                        },
                        {
                            "name": "element2",
                            "config": {
                                "description": "this is element2.config.description"
                            },
                            "state": {
                                "description": "this is element2.state.description"
                            },
                        },
                    ]
                }
            }
        }

    def test_parse_config(self) -> None:
        parser = RootTestParser(dm, test_data, config=True, state=False)
        parsed_obj = parser.process()
        assert parsed_obj.raw_value() == test_expected_config

    def test_parse_state(self) -> None:
        parser = RootTestParser(dm, test_data, config=False, state=True)
        parsed_obj = parser.process()
        assert parsed_obj.raw_value() == test_expected_state

    def test_parse_config_with_extra(self) -> None:
        parser = RootTestParserWithExtra(
            dm, test_data, config=True, state=False, extra={"os_version": "test"}
        )
        parsed_obj = parser.process()
        assert parsed_obj.raw_value() == test_expected_config

    def test_parse_state_with_extra(self) -> None:
        parser = RootTestParserWithExtra(
            dm, test_data, config=False, state=True, extra={"os_version": "test"}
        )
        parsed_obj = parser.process()
        assert parsed_obj.raw_value() == test_expected_state

    def test_parse_warning(self, caplog: Any) -> None:
        """Assert that a warning is raised for elements no in the dm"""
        parser = RootTestParser(dm, test_data, config=False, state=True)
        with caplog.at_level(logging.WARNING):
            parser.process()
        assert "attributes {'" not in caplog.text

        parser = WarnTestParser(dm, test_data, config=True, state=False)
        with caplog.at_level(logging.WARNING):
            parser.process()
        assert "attributes" in caplog.text and "notinmodel" in caplog.text
