import pathlib
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


class RootTestTranslatorWithExtra(translator.RootTranslator):
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


class Test:
    def test_translate_config_with_extra(self) -> None:
        translater = RootTestTranslatorWithExtra(
            dm, candidate=test_data, extra={"os_version": "test"}
        )
        translated_obj = translater.process()
        assert translated_obj == {
            "element1": {
                "description": "this is element1.config.description",
                "name": "element1",
            },
            "element2": {
                "description": "this is element2.config.description",
                "name": "element2",
            },
        }
