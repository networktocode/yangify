import json
import pathlib
from typing import Any, Dict, List

import pytest

from tests.linter import impl

from yangify.linter import LintObjectType, Linter

from yangson.datamodel import DataModel


BASE = pathlib.Path(__file__).parent
dm = DataModel.from_file(
    f"{BASE}/../impl/yang-library-data.json", [f"{BASE}/../impl/yang-modules"]
)


def get_test_cases() -> Dict[str, Any]:
    classes: List[LintObjectType] = [
        impl.InterfaceConfigWarnings,
        impl.InterfaceConfigCorrect,
        impl.InterfaceConfigMissingImplements,
        impl.InterfaceConfigWrongPath,
        impl.InterfaceConfigInvalidPath,
        impl.Interfaces,
        impl.RootP,
        impl.RootT,
        impl,
        "tests/linter/impl.py",
        "tests/linter",
    ]
    ids: List[str] = []
    test_cases: List[LintObjectType] = []
    for cls in classes:
        test_cases.append(cls)
        if isinstance(cls, str):
            ids.append(cls)
        else:
            ids.append(cls.__name__)
    return {"argnames": "cls", "argvalues": test_cases, "ids": ids}


def get_expected(path: pathlib.Path, expected: str, save: bool = False) -> str:
    if save:
        with open(path, "w+") as f:
            f.write(expected)
    with open(path, "r") as f:
        return f.read()


class TestLinter:
    @pytest.mark.parametrize(**get_test_cases())  # type: ignore
    def test_linter_serialize_not_recursive(self, cls: LintObjectType) -> None:
        if isinstance(cls, str):
            filename = cls.split("/")[-1].replace("py", "json")
        else:
            filename = f"{cls.__name__}.json"
        res = Linter.lint(cls, dm, False)
        got = res.serialize()
        got_text = json.dumps(got, indent=4)
        expected = json.loads(
            get_expected(
                BASE.joinpath("data", "serialize", "not_recursive", filename), got_text
            )
        )
        assert got == expected, got_text

    @pytest.mark.parametrize(**get_test_cases())  # type: ignore
    def test_linter_serialize_recursive(self, cls: LintObjectType) -> None:
        if isinstance(cls, str):
            filename = cls.split("/")[-1].replace("py", "json")
        else:
            filename = f"{cls.__name__}.json"
        res = Linter.lint(cls, dm, True)
        got = res.serialize()
        got_text = json.dumps(got, indent=4)
        expected = json.loads(
            get_expected(
                BASE.joinpath("data", "serialize", "recursive", filename), got_text
            )
        )
        assert got == expected, got_text

    def test_linter_serialize_skip_W101(self) -> None:
        filename = f"RootP.json"
        res = Linter.lint(impl.RootP, dm, True, {"W101"})
        got = res.serialize()
        got_text = json.dumps(got, indent=4)
        expected = json.loads(
            get_expected(
                BASE.joinpath("data", "serialize", "skip_W101", filename), got_text
            )
        )
        assert got == expected, got_text

    @pytest.mark.parametrize(**get_test_cases())  # type: ignore
    def test_linter_to_text_not_recursive(self, cls: LintObjectType) -> None:
        if isinstance(cls, str):
            filename = cls.split("/")[-1].replace("py", "text")
        else:
            filename = f"{cls.__name__}.text"
        res = Linter.lint(cls, dm, False)
        got = res.to_text()
        expected = get_expected(
            BASE.joinpath("data", "to_text", "not_recursive", filename), got
        )
        assert got == expected, got

    @pytest.mark.parametrize(**get_test_cases())  # type: ignore
    def test_linter_to_text_recursive(self, cls: LintObjectType) -> None:
        if isinstance(cls, str):
            filename = cls.split("/")[-1].replace("py", "text")
        else:
            filename = f"{cls.__name__}.text"
        res = Linter.lint(cls, dm, True)
        got = res.to_text()
        expected = get_expected(
            BASE.joinpath("data", "to_text", "recursive", filename), got
        )
        assert got == expected, got

    def test_linter_to_text_skip_W101(self) -> None:
        filename = f"RootP.text"
        res = Linter.lint(impl.RootP, dm, True, {"W101"})
        got = res.to_text()
        expected = get_expected(
            BASE.joinpath("data", "to_text", "skip_W101", filename), got
        )
        assert got == expected, got
