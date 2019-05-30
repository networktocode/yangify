import copy
import logging
from typing import Any, Dict, Iterator, List, Optional, Tuple, cast

from yangify.model_filter import ModelFilter

from yangson import schemanode
from yangson.datamodel import DataModel
from yangson.enumerations import ContentType
from yangson.instance import RootNode


logger = logging.getLogger(__name__)


def unneeded(*args: Any, **kwargs: Any) -> None:
    """
    You can use this dummy function to flag that a particular leaf
    doesn't need to be processed. Otherwise, the system will
    flag it as not implemented.

    Example:

        we don't need to ``vlan_id`` as it's the same as the key::

            class VlanConfig(Parser):
                def name(self):
                    ...

                vlan_id = unneeded
    """
    pass


class ParserData:
    """
    This is the base class for the :obj:`Parser.Yangify` object.

    Attributes:

        schema (`yangson.schemanode.DataNode`): Schema of the current grouping being processed

        native (`Any`): Exact details will depend on the parser implementation. As a rule of thumb
           points to the native configuration/data relevant for the current element being
           processed. On start it's set the same as :obj:`ParserData.root_native`, however,
           it can be changed by the parser implementation. When processing lists, it's
           set automatically to the second object returned by :obj:`ParserData.extract_elements`

        root_native (`Any`): Exact type and details will depend on the parser implementation.
            However, it points to the original object passed to :obj:`RootParser` in the ``native``
            argument.

        keys (`Dict[str, Any]`): This dictionary keeps track of all the keys relevant to the current
            object being processed. Keys are equal to the path where the key was extracted while
            the value is the actual value. For instance, if you were parsing the interface
            ``FastEthernet1.1`` using the ``openconfig:interfaces`` model, you'd have the
            following keys::

                {
                    "openconfig-interfaces:interfaces/interface": "FastEthernet1",
                    "openconfig-interfaces:interfaces/interface/subinterfaces/subinterface": 1,
                }

        extra (`Dict[str, Any]`): Arbitrary data that can be defined by the user when instantiating
            the root of the object. Useful to share arbitrary information throughout the entire
            lifecycle of the parser
    """

    path = ""
    metadata: Dict[str, Any] = {}

    def __init__(
        self,
        schema: schemanode.DataNode,
        native: Any,
        root_native: Any,
        keys: Dict[str, str],
        extra: Dict[str, Any],
    ) -> None:
        self.schema = schema
        self.native = native
        self.root_native = root_native
        self.keys = keys
        self.extra = extra

    @property
    def key(self) -> str:
        """
        Last key extracted in the current object being processed.
        """
        node = self.schema
        while not isinstance(node, schemanode.ListNode):
            node = node.parent
        return self.keys[node.data_path()]

    def init(self) -> None:
        """
        Called only by the :obj:`RootParser` in the very beginning of the processing. This
        function may be used to preprocess the native objects or for anything else
        that may be needed to do before the actual processing starts.
        """
        pass

    def post(self) -> None:
        """
        Called only by the :obj:`RootParser` in the very end of the processing.
        """
        pass

    def pre_process(self) -> None:
        """
        This is called before processing either a container or a list element.
        """
        pass

    def post_process(self) -> None:
        """
        This is called after processing either a container or a list element.
        """
        pass

    def extract_elements(self) -> Iterator[Tuple[str, Any]]:
        """
        This function is called when processing a YANG list. It's mandatory to implement
        and needs to return an iterator of <key, value> pairs where:

            * the **key** is the identifier of en element of the list
            * the **value** is a relevant block of native data for the current object

        The **key** will be added to :obj:`ParserData.keys` (referenced as the path to the
        node) and the **value** will be set in the :obj:`ParserData.native` attribute.
        """
        raise NotImplementedError(f"needs to be implemented by user")


class Parser:
    """
    Parsing classes used to parse groupings need to inherit from this class.
    In addition to the relevant functions and classes to parse children nodes,
    they may include a ``Yangify`` class that inherits from :obj:`ParserData`
    to implement some parsing logic. This is mandatory when parsing YANG Lists.

    Attributes:
        yy (:obj:`ParserData`): This attribute will be instantiated using the nested
            class :obj:`Parser.Yangify`. Everything you implement inside your
            ``class Yangify`` will be available through this attribute.

    Example:

        Interface class to parse ``openconfig-interfaces:interfaces/interface`` model::

            class Interface(Parser):
                class Yangify(ParserData):
                    def extract_elements(self) -> Iterator[Tuple[str, Dict[str, Any]]]:
                        for k, v in interfaces_magic:
                            yield k, v
    """

    Yangify = ParserData

    def __init__(
        self,
        schema: schemanode.DataNode,
        model_filter: ModelFilter,
        native: Any,
        root_native: Any,
        keys: Dict[str, str],
        extra: Dict[str, Any],
    ) -> None:
        self.model_filter = model_filter
        self.yy: ParserData = self.Yangify(schema, native, root_native, keys, extra)

    def __str__(self) -> str:
        return str(self.yy.schema.data_path())

    def _get_child(self, child: schemanode.DataNode) -> Optional["Parser"]:
        child_name = child.name.replace("-", "_")
        c_type = getattr(self, child_name, None)
        if not c_type:
            return None
        if not issubclass(c_type, Parser):
            raise ValueError(f"{c_type.__qualname__} doesn't inherit from BaseModel")
        return cast(
            "Parser",
            c_type(
                child,
                self.model_filter,
                self.yy.native,
                self.yy.root_native,
                self.yy.keys,
                self.yy.extra,
            ),
        )

    def _get_key_name(self, node: schemanode.DataNode) -> str:
        if node.ns == node.parent.ns:
            return cast(str, node.name)
        else:
            return f"{node.ns}:{node.name}"

    def _process_container(
        self, config: bool, state: bool, keys: List[str]
    ) -> Dict[str, Any]:
        logger.debug("%s: processing", self)
        self.yy.pre_process()
        result: Dict[str, Any] = {}
        try:
            if not self.model_filter.check(self.yy.schema.data_path()):
                return result
        except TypeError:
            pass
        for child in self.yy.schema.data_children():
            logger.debug("%s: processing child %s:%s", self, child.ns, child.name)
            if isinstance(child, (schemanode.ContainerNode, schemanode.GroupNode)):
                if isinstance(child, schemanode.GroupNode):
                    children = child.children
                else:
                    children = [child]
                for c in children:
                    attr = self._get_child(c)
                    if attr:
                        r = attr._process_container(config, state, [])
                        if r:
                            key_name = self._get_key_name(c)
                            result[key_name] = r
                    else:
                        logger.info(
                            "%s: doesn't implement %s:%s", self, child.ns, child.name
                        )
            elif isinstance(child, (schemanode.ListNode,)):
                attr = self._get_child(child)
                if attr:
                    r = attr._process_list(config, state)
                    if r:
                        key_name = self._get_key_name(child)
                        result[key_name] = r
                else:
                    logger.info(
                        "%s: doesn't implement %s:%s", self, child.ns, child.name
                    )
            elif isinstance(child, (schemanode.LeafNode, schemanode.LeafListNode)):
                if child.name not in keys:
                    if not self.model_filter.check(child.data_path()):
                        continue
                    if child.config and not config or not child.config and not state:
                        continue
                child_name = child.name.replace("-", "_")
                c = getattr(self, child_name, None)
                if c:
                    r = c()
                    if r is not None:
                        key_name = self._get_key_name(child)
                        result[key_name] = r
                else:
                    logger.info(
                        "%s: doesn't implement %s:%s", self, child.ns, child.name
                    )
            else:
                msg = f"I don't know the type of {child.ns}:{child.name} - {child.__class__}"
                logger.error("%s: %s", self, msg)
                raise ValueError(msg)
        self.yy.post_process()
        return result

    def _process_list(self, config: bool, state: bool) -> List[Any]:
        logger.debug("%s: processing list", self)
        result: List[Any] = []
        old_keys = copy.deepcopy(self.yy.keys)
        old_native = self.yy.native
        keys = [e[0] for e in self.yy.schema.keys]
        for element_key, element_native in self.yy.extract_elements():
            self.yy.keys = copy.deepcopy(old_keys)
            self.yy.keys[self.yy.schema.data_path()] = element_key
            self.yy.native = element_native
            r = self._process_container(config, state, keys)
            result.append(r)
        self.yy.keys = old_keys
        self.yy.native = old_native
        return result


class RootParser(Parser):
    """
    This object represents the root of the parser and allows the user to choose which
    parts of the model to parse and with which parsers. To do so assign the parser
    classes to class attributes named after the nodes you want to parse.

    Parameters:

        dm: DataModel we are going to be parsing

        native: Native data to parse and map into the model

        config: Parse config leaves

        state: Parse state leaves

        extra (`Dict[str, Any]`): Arbitrary data that can be defined by the user when instantiating
            the root of the object. Useful to share arbitrary information throughout the entire
            lifecycle of the parser

    Examples:

        Parsing both ``openconfig-interfaces`` and ``openconfig-vlan`` models::

            from yangify import parser

            class Interfaces(parser.Parser):
                ...

            class Vlans(parser.Parser):
                ...

            class Parser(parser.RootParser):
                interfaces = Interfaces
                vlans = Vlans

        Parsing only ``openconfig-interfaces`` but using a different parser::

            from yangify import parser

            class InterfacesAlt(parser.Parser):
                ...

            class Parser(parser.RootParser):
                interfaces = InterfacesAlt
    """

    def __init__(
        self,
        dm: DataModel,
        native: Any,
        config: bool = True,
        state: bool = False,
        include: Optional[List[str]] = None,
        exclude: Optional[List[str]] = None,
        extra: Dict[str, Any] = None,
    ) -> None:
        if not config and not state:
            raise ValueError("either config or state must be true")
        self.dm = dm
        self.config = config
        self.state = state
        include = include if include is not None else ["/"]
        model_filter = ModelFilter(include=include, exclude=exclude or [])
        super().__init__(self.dm.schema, model_filter, native, native, {}, extra or {})

    def __str__(self) -> str:
        return self.__class__.__qualname__

    def process(self, validate: bool = True) -> RootNode:
        """
        Process the native data and map it into the model.

        Arguments:
            validate: Validates the object before returning it
        """
        self.yy.init()
        r = super()._process_container(self.config, self.state, [])
        obj = self.dm.from_raw(r)
        self.yy.post()
        if validate:
            ctype = ContentType.all if self.state else ContentType.config
            obj.validate(ctype=ctype)
        return obj
