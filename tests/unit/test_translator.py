import pathlib
import json
from typing import Optional

from yangify import translator

from yangson.datamodel import DataModel


BASE = pathlib.Path(__file__).parent
dm = DataModel.from_file(
    f"{BASE}/yang/simple/yang-library-data.json", [f"{BASE}/yang/simple/"]
)


test_data = {
    "yangify-tests:start": {
        "elements": {
            "element": [
                {
                    "name": "element1",
                    "config": {
                        "description": "this is element1.config.description",
                        "members": ["the", "first", "list"],
                    },
                },
                {
                    "name": "element2",
                    "config": {
                        "description": "this is element2.config.description",
                        "members": ["the", "second", "list"],
                    },
                },
            ]
        }
    }
}

test_expected = {
    "element1": {
        "description": "this is element1.config.description",
        "name": "element1",
        "members": ["the", "first", "list"],
    },
    "element2": {
        "description": "this is element2.config.description",
        "name": "element2",
        "members": ["the", "second", "list"],
    },
}

test_leaf_list_candidate = {
    "yangify-tests:start": {
        "elements": {
            "element": [
                {
                    "name": "element1",
                    "config": {
                        "description": "this is element1.config.description",
                        "members": ["one", "two"],
                    },
                },
                {
                    "name": "element2",
                    "config": {
                        "description": "this is element2.config.description",
                        "members": ["one", "two"],
                    },
                },
            ]
        }
    }
}

test_leaf_list_running = {
    "yangify-tests:start": {
        "elements": {
            "element": [
                {
                    "name": "element1",
                    "config": {
                        "description": "this is element1.config.description",
                        "members": ["one", "two", "three"],
                    },
                },
                {
                    "name": "element2",
                    "config": {
                        "description": "this is element2.config.description",
                        "members": ["one", "two", "three"],
                    },
                },
            ]
        }
    }
}


class RootTestTranslatorWithExtra(translator.RootTranslator):
    """
    This is just a sample translator
    but that asserts at different points that `extra`
    is set to a predetermined value
    """

    class Yangify(translator.TranslatorData):
        def init(self) -> None:
            self.root_result = {}
            self.result = self.root_result

    class start(translator.Translator):
        class elements(translator.Translator):
            class element(translator.Translator):
                class Yangify(translator.TranslatorData):
                    def pre_process(self) -> None:
                        assert self.extra == {"os_version": "test"}
                        self.root_result[self.key] = {}
                        self.result = self.root_result[self.key]

                    def pre_process_list(self) -> None:
                        assert self.extra == {"os_version": "test"}

                def name(self, value: Optional[bool]) -> None:
                    assert self.yy.extra == {"os_version": "test"}
                    self.yy.result["name"] = value

                class config(translator.Translator):
                    class Yangify(translator.TranslatorData):
                        def pre_process(self) -> None:
                            assert self.extra == {"os_version": "test"}

                    def description(self, value: Optional[bool]) -> None:
                        assert self.yy.extra == {"os_version": "test"}
                        self.yy.result["description"] = value

                    def members(self, value: Optional[bool]) -> None:
                        assert self.yy.extra == {"os_version": "test"}
                        self.yy.result["members"] = value


class RootTestTranslatorPreProcessLeafList(translator.RootTranslator):
    """
    This is just a sample translator
    but that asserts at different points that `extra`
    is set to a predetermined value
    """

    class Yangify(translator.TranslatorData):
        def init(self) -> None:
            self.root_result = {}
            self.result = self.root_result

    class start(translator.Translator):
        class elements(translator.Translator):
            class element(translator.Translator):
                class Yangify(translator.TranslatorData):
                    def pre_process(self) -> None:
                        self.root_result[self.key] = {}
                        self.result = self.root_result[self.key]

                def name(self, value: Optional[bool]) -> None:
                    self.yy.result["name"] = value

                class config(translator.Translator):
                    class Yangify(translator.TranslatorData):
                        def pre_process_leaf_list(self) -> None:
                            assert "three" in self.values_to_remove

                        def post_process_leaf_list(self) -> None:
                            self.root_result["test"] = "test"
                            assert self.result.get("members") == []

                    def description(self, value: Optional[bool]) -> None:
                        self.yy.result["description"] = value

                    def members(self, value: Optional[bool]) -> None:
                        self.yy.result["members"] = value


class Test:
    def test_translate_config_with_extra(self) -> None:
        translator = RootTestTranslatorWithExtra(
            dm, candidate=test_data, extra={"os_version": "test"}
        )
        translated_obj = translator.process()
        # Nested dicts require key order to match in comparisons
        assert json.dumps(translated_obj, sort_keys=True) == json.dumps(
            test_expected, sort_keys=True
        )

    def test_translate_config_leaf_list(self) -> None:
        translator = RootTestTranslatorPreProcessLeafList(
            dm, candidate=test_leaf_list_candidate, running=test_leaf_list_running
        )
        translated_obj = translator.process()
        # assert post_process_leaf_list is called
        assert translated_obj.get("test") == "test"
