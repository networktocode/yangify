import pathlib
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
        assert parsed_obj.raw_value() == {
            "yangify-tests:start": {
                "elements": {
                    "element": [
                        {
                            "name": "element1",
                            "config": {
                                "description": "this is element1.config.description"
                            },
                        },
                        {
                            "name": "element2",
                            "config": {
                                "description": "this is element2.config.description"
                            },
                        },
                    ]
                }
            }
        }

    def test_parse_state(self) -> None:
        parser = RootTestParser(dm, test_data, config=False, state=True)
        parsed_obj = parser.process()
        assert parsed_obj.raw_value() == {
            "yangify-tests:start": {
                "elements": {
                    "element": [
                        {
                            "name": "element1",
                            "state": {
                                "description": "this is element1.state.description"
                            },
                        },
                        {
                            "name": "element2",
                            "state": {
                                "description": "this is element2.state.description"
                            },
                        },
                    ]
                }
            }
        }

    def test_parse_config_with_extra(self) -> None:
        parser = RootTestParserWithExtra(
            dm, test_data, config=True, state=False, extra={"os_version": "test"}
        )
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
                        },
                        {
                            "name": "element2",
                            "config": {
                                "description": "this is element2.config.description"
                            },
                        },
                    ]
                }
            }
        }

    def test_parse_state_with_extra(self) -> None:
        parser = RootTestParserWithExtra(
            dm, test_data, config=False, state=True, extra={"os_version": "test"}
        )
        parsed_obj = parser.process()
        assert parsed_obj.raw_value() == {
            "yangify-tests:start": {
                "elements": {
                    "element": [
                        {
                            "name": "element1",
                            "state": {
                                "description": "this is element1.state.description"
                            },
                        },
                        {
                            "name": "element2",
                            "state": {
                                "description": "this is element2.state.description"
                            },
                        },
                    ]
                }
            }
        }
