import inspect
import pathlib
from dataclasses import dataclass, field
from importlib.machinery import SourceFileLoader
from types import ModuleType
from typing import Any, Dict, Iterable, List, Optional, Set, Tuple, Type, Union


from yangify.parser import Parser, RootParser
from yangify.translator import RootTranslator, Translator

from yangson import schemanode
from yangson.datamodel import DataModel
from yangson.exceptions import InvalidSchemaPath


LintObjectType = Union[
    Type[Parser],
    Type[RootParser],
    Type[Translator],
    Type[RootTranslator],
    ModuleType,
    str,
]


class MessageType:
    PATH_EMPTY = "E001"
    SCHEMA_NOT_FOUND = "E101"
    SCHEMA_INVALID = "E102"
    CHILDREN_MISSING = "W001"
    PATH_MISSING_SLASH = "W002"
    ATTRIBUTE_EXTRA = "W101"

    @staticmethod
    def help() -> Dict[str, Tuple[str, str]]:
        return {
            "E001": ("PATH_EMPTY", "path is empty"),
            "E101": ("SCHEMA_NOT_FOUND", "schema path couldn't be found"),
            "E102": ("SCHEMA_INVALID", "schema path is invalid"),
            "W001": ("CHILDREN_MISSING ", "children is missing"),
            "W002": ("PATH_MISSING_SLASH", "path should begin with forward slash"),
            "W101": ("ATTRIBUTE_EXTRA ", "class attribute doesn't belong to the model"),
        }


@dataclass
class Message:
    """
    A message, usually indicating some error or warning.

    Attributes:
        message: Text of the message
        message_type: Code identifying the type of message, i.e., E101 or W101
    """

    message: str
    message_type: str

    def serialize(self) -> Dict[str, str]:
        """
        Representation of the object using native types
        """
        return {"message": self.message, "message_type": self.message_type}

    def to_text(self) -> str:
        """
        A text representation of the object
        """
        return f"{self.message_type}:{self.message}"


class Messages(List[Message]):
    """
    A list of :obj:`Message` objects

    Attributes:
        ignore: Populated with a list of message codes (see :obj:`MessageType`)
            it will cause the functions ``append`` and ``extend`` to ignore
            messages of ``message_type`` included in this list.
    """

    def __init__(self, ignore: Optional[Set[str]] = None) -> None:
        self.ignore = ignore or []
        valid_codes = MessageType.help()
        for i in self.ignore:
            if i not in valid_codes:
                raise ValueError(f"don't recognize error code '{i}'")

    def serialize(self) -> List[Any]:
        """
        Representation of the object using native types
        """
        return [m.serialize() for m in self]

    def append(self, message: Message) -> None:
        if message.message_type not in self.ignore:
            super().append(message)

    def extend(self, messages: Iterable[Message]) -> None:
        msgs = [m for m in messages if m.message_type not in self.ignore]
        super().extend(msgs)


class LinterException(Exception):
    def __init__(self, message: Message) -> None:
        self.message = message


@dataclass
class LinterResult:
    """
    Parent class for results of linting object.

    Attributes:
        name: name of the object linted
        path: YANG path of the object
        filepath: path fo the file where the object resides
        lineno: line number where the object resides
        messages: Messages generated while liniting the object
        children: Result of linting descending objects
        type: Type of the object linted (module, file, folder, container...)
    """

    name: str
    path: str
    filepath: str
    lineno: int
    messages: Messages = field(default_factory=Messages)
    children: Dict[str, "LinterResult"] = field(default_factory=dict)
    type: str = "unknown"

    def serialize(self) -> Dict[str, Any]:
        """
        Representation of the object using native types
        """
        return {
            "name": self.name,
            "path": self.path,
            "filepath": self.filepath,
            "lineno": self.lineno,
            "messages": self.messages.serialize(),
            "children": {k: v.serialize() for k, v in self.children.items()},
            "type": self.type,
        }

    def to_text(self) -> str:
        """
        A text representation of the object
        """
        text = ""
        for m in self.messages:
            text += f"{self.filepath}:{self.lineno}:{m.to_text()}\n"

        for c in self.children.values():
            text += c.to_text()
        return text

    def to_ascii_tree(self, prefix: str, is_last: bool = False) -> str:
        """
        ASCII tree representation of the object linted
        """
        return f"{prefix}+--{self.name}\n"


@dataclass
class RootLinterResult(LinterResult):
    type: str = "root"

    def to_ascii_tree(self, prefix: str, is_last: bool = False) -> str:
        """
        ASCII tree representation of the object linted
        """
        text = f"{prefix}+--{self.name}\n"
        p = f"{prefix}   " if is_last else f"{prefix}    "
        num_children = len(self.children)
        for i, c in enumerate(self.children.values()):
            text += c.to_ascii_tree(p, is_last=i + 1 == num_children)
        return text


@dataclass
class ModuleLinterResult(LinterResult):
    """
    Result of linting a python module
    """

    type: str = "module"


@dataclass
class FileLinterResult(LinterResult):
    """
    Result of linting a file with python code
    """

    type: str = "file"


@dataclass
class FolderLinterResult(LinterResult):
    """
    Result of linting a folder with python code
    """

    type: str = "folder"


@dataclass
class ContainerLinterResult(LinterResult):
    """
    Result of linting a class processing a YANG container
    """

    class_name: str = ""
    type: str = "container"
    implements: List[str] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)

    def serialize(self) -> Dict[str, Any]:
        """
        Representation of the object using native types
        """
        return {
            **super().serialize(),
            "class_name": self.class_name,
            "implements": self.implements,
            "metadata": self.metadata,
        }

    def to_ascii_tree(self, prefix: str, is_last: bool = False) -> str:
        """
        ASCII tree representation of the object linted
        """
        text = f"{prefix}+--{self.name} ({self.class_name})\n"
        p = f"{prefix}   " if is_last else f"{prefix}|   "
        num_children = len(self.children)
        for i, c in enumerate(self.children.values()):
            text += c.to_ascii_tree(p, is_last=i + 1 == num_children)
        return text


class ContainerLinter:
    """
    Placeholder for functions to lint classes processing YANG containers
    """

    @staticmethod
    def lint(
        cls: Union[Type[Parser], Type[Translator]],
        dm: DataModel,
        recursive: bool,
        ignore: Optional[Set[str]],
    ) -> ContainerLinterResult:
        """
        Lint supported objects
        """
        name = cls.__qualname__
        path = cls.Yangify.path
        lineno = inspect.getsourcelines(cls)[1]
        filepath = inspect.getsourcefile(cls)
        res = ContainerLinterResult(
            name=cls.Yangify.path.split("/")[-1],
            class_name=name,
            path=path,
            lineno=lineno,
            filepath=filepath,
            messages=Messages(ignore),
            metadata=cls.Yangify.metadata,
        )
        if not path:
            res.messages.append(
                Message("Yangify.path is not set or empty", MessageType.PATH_EMPTY)
            )
            return res
        else:
            if not path.startswith("/"):
                res.messages.append(
                    Message(
                        "Yangify.path should begin with forward slash",
                        MessageType.PATH_MISSING_SLASH,
                    )
                )
                return res

        try:
            children, messages = ContainerLinter._process_children(
                cls, dm, recursive, ignore
            )
            res.children.update(children)
            res.messages.extend(messages)
            msgs, implements = ContainerLinter._process_class_attrs(cls, dm)
            res.messages.extend(msgs)
            res.implements = implements
        except LinterException as e:
            res.messages.append(e.message)
        return res

    @staticmethod
    def _extract_shema(dm: DataModel, path: str) -> schemanode.SchemaNode:
        try:
            schema = dm.get_schema_node(path)
            if not schema:
                raise LinterException(
                    Message(
                        f"Yangify.path couldn't be found in model: {path}",
                        MessageType.SCHEMA_NOT_FOUND,
                    )
                )
        except InvalidSchemaPath:
            raise LinterException(
                Message(f"Yangify.path is invalid: {path}", MessageType.SCHEMA_INVALID)
            )
        except Exception:
            raise
        return schema

    @staticmethod
    def _process_children(
        cls: Union[Type[Parser], Type[Translator]],
        dm: DataModel,
        recursive: bool,
        ignore: Optional[Set[str]],
    ) -> Tuple[Dict[str, LinterResult], Messages]:
        schema = ContainerLinter._extract_shema(dm, cls.Yangify.path)
        messages: Messages = Messages(ignore)
        children: Dict[str, LinterResult] = {}
        for child in schema.children:
            if child.name is None:
                continue
            child_name = child.name.replace("-", "_")
            if isinstance(child, schemanode.GroupNode):
                continue
            if not hasattr(cls, child_name):
                messages.append(
                    Message(
                        f"doesn't implement {child.name}", MessageType.CHILDREN_MISSING
                    )
                )
                continue
            if isinstance(child, schemanode.LeafNode):
                pass
            elif recursive:
                children[child_name] = ContainerLinter.lint(
                    getattr(cls, child_name), dm, recursive, ignore
                )
        return children, messages

    @staticmethod
    def _find_child(
        child: str, schema: schemanode.SchemaNode
    ) -> Optional[schemanode.DataNode]:
        for c in schema.data_children():
            if c.name == child:
                return c
        return None

    @staticmethod
    def _process_class_attrs(
        cls: Union[Type[Parser], Type[Translator]], dm: DataModel
    ) -> Tuple[Messages, List[str]]:
        skip = ["Yangify"]
        schema = ContainerLinter._extract_shema(dm, cls.Yangify.path)
        messages: Messages = Messages()
        implements: List[str] = []
        for child in dir(cls):
            if child.startswith("_") or child in skip:
                continue
            child_clean = child.replace("_", "-")
            if ContainerLinter._find_child(child_clean, schema) is None:
                messages.append(
                    Message(
                        f"{child} doesn't correspond to a leaf or container",
                        MessageType.ATTRIBUTE_EXTRA,
                    )
                )
            else:
                implements.append(child)
        return messages, implements


class RootLinter:
    """
    Placeholder for functions to lint :obj:`yangify.parser.RootParser` and
    :obj:`yangify.translator.RootTranslator` objects
    """

    @staticmethod
    def lint(
        cls: Union[Type[RootParser], Type[RootTranslator]],
        dm: DataModel,
        recursive: bool,
        ignore: Optional[Set[str]],
    ) -> RootLinterResult:
        """
        Lint supported objects
        """
        name = cls.__qualname__
        lineno = inspect.getsourcelines(cls)[1]
        filepath = inspect.getsourcefile(cls)
        res = RootLinterResult(name=name, path="/", lineno=lineno, filepath=filepath)

        skip = ["Yangify", "process"]
        for child in dir(cls):
            if child.startswith("_") or child in skip:
                continue
            child_obj = getattr(cls, child)
            res.children[child] = ContainerLinter.lint(child_obj, dm, recursive, ignore)
        return res


class ModuleLinter:
    """
    Placeholder for functions to lint python modules
    """

    @staticmethod
    def lint(
        cls: ModuleType, dm: DataModel, recursive: bool, ignore: Optional[Set[str]]
    ) -> ModuleLinterResult:
        """
        Lint supported objects
        """
        name = cls.__name__
        filepath = inspect.getsourcefile(cls)
        res = ModuleLinterResult(name=name, path="n/a", lineno=0, filepath=filepath)

        for child in dir(cls):
            obj = getattr(cls, child)
            if not inspect.isclass(obj):
                continue
            if (
                issubclass(obj, (RootParser, RootTranslator))
                and inspect.getsourcefile(obj) == filepath
            ):
                res.children[child] = RootLinter.lint(obj, dm, recursive, ignore)
            elif (
                issubclass(obj, (Parser, Translator))
                and inspect.getsourcefile(obj) == filepath
            ):
                res.children[child] = ContainerLinter.lint(obj, dm, recursive, ignore)
        return res


class FileLinter:
    """
    Placeholder for functions to lint files with python code
    """

    @staticmethod
    def lint(
        path: pathlib.Path, dm: DataModel, recursive: bool, ignore: Optional[Set[str]]
    ) -> FileLinterResult:
        """
        Lint supported objects
        """
        loader = SourceFileLoader(str(path), str(path))
        mod = loader.load_module(str(path))
        res = FileLinterResult(name=str(path), path="n/a", lineno=0, filepath=str(path))
        res.children[str(path)] = ModuleLinter.lint(mod, dm, recursive, ignore)
        return res


class FolderLinter:
    """
    Placeholder for functions to lint folders with python code
    """

    @staticmethod
    def lint(
        path: pathlib.Path, dm: DataModel, recursive: bool, ignore: Optional[Set[str]]
    ) -> FolderLinterResult:
        """
        Lint supported objects
        """
        res = FolderLinterResult(
            name=str(path), path="n/a", lineno=0, filepath=str(path)
        )
        for p in path.iterdir():
            if p.suffix == ".py":
                res.children[str(p)] = FileLinter.lint(p, dm, recursive, ignore)
            elif p.is_dir():
                res.children[str(p)] = FolderLinter.lint(p, dm, recursive, ignore)
            else:
                continue
        return res


class Linter:
    """
    Placeholder for functions to lint supported objects
    """

    @staticmethod
    def lint(
        obj: LintObjectType,
        dm: DataModel,
        recursive: bool = False,
        ignore: Optional[Set[str]] = None,
    ) -> LinterResult:
        """
        Lint supported objects
        """
        if isinstance(obj, ModuleType):
            return ModuleLinter.lint(obj, dm, recursive, ignore)
        elif isinstance(obj, (str, pathlib.Path)):
            path = pathlib.Path(obj)
            if path.is_file():
                return FileLinter.lint(path, dm, recursive, ignore)
            else:
                return FolderLinter.lint(path, dm, recursive, ignore)
        elif issubclass(obj, (RootParser, RootTranslator)):
            return RootLinter.lint(obj, dm, recursive, ignore)
        elif issubclass(obj, (Parser, Translator)):
            return ContainerLinter.lint(obj, dm, recursive, ignore)
        else:
            raise ValueError(f"don't know what {obj} is")
