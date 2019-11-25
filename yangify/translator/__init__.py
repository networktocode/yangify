import copy
import logging
from typing import Any, Dict, List, Optional, Type, cast

from yangson import instance
from yangson import schemanode
from yangson.datamodel import DataModel
from yangson.exceptions import NonexistentInstance


logger = logging.getLogger(__name__)


def unneeded(*args: Any, **kwargs: Any) -> None:
    """
    You can use this dummy function to flag that a particular leaf
    doesn't need to be processed. Otherwise, the system will
    flag it as not implemented.

    Example:

        we don't need to ``vlan_id`` as it's the same as the key::

            class VlanConfig(Translator):
                def name(self):
                    ...

                vlan_id = unneeded
    """
    pass


class TranslatorData:
    """
    This is the base class for the :obj:`Translator.Yangify` object.

    Attributes:

        result (`Any`): Exact details will depend on the translator implementation but the
            general idea is that the translator will set it to the most convenient object
            possible.

        root_result (`Any`): Exact details will depend on the translator but this object should
            always point to the root of resulting translation.

        path (`yangson.instance.InstanceRoute`): This attribute will hold the path to nearest
            grouping. For leaves it means it will point to the parent container, for lists to
            exact element being processed for containers to the container itself.

        schema (`yangson.schemanode.DataNode`): This is the schema for the current node.

        keys (`Dict[str, Any]`): This dictionary keeps track of all the keys relevant to the current
            object being processed. Keys are equal to the path where the key was extracted while
            the value is the actual value. For instance, if you were translating the interface
            ``FastEthernet1.1`` using the ``openconfig:interfaces`` model, you'd have the
            following keys::

                {
                    "openconfig-interfaces:interfaces/interface": "FastEthernet1",
                    "openconfig-interfaces:interfaces/interface/subinterfaces/subinterface": 1,
                }

        candidate (`yangson.instance.RootNode`): This is the object we are translating, it always
            always to the root of it. It can be combined with the :obj:`TranslatorData.path` to
            go to parts of it. For instance::

                self.candidate.goto(self.path[:-2]).raw_values()

            Should point you two steps above your current position and then give you the raw
            value of it (a dictionary most likely)

        running (`Optional[`yangson.instance.RootNode]`): This is set when merging one object into
            another. Pretty much like :obj:`TranslatorData.candidate`, but with the running data.

        replace (`bool`): This is set to `True` when performing a replace operation.

        to_remove (`List[yangson.instance.ObjectMember]`): When processing YANG lists and performing
            either a merge or replace operation, this List will be populated with the elements
            that need to be removed.

        values_to_remove (`List[Any]`): When processing YANG leaf-lists and performing
            either a merge or replace operation, this List will be populated with the elements
            that need to be removed.  The contents of the list are cooked values mapped from
            types in yangson.instance.ObjectValue.

        extra (`Dict[str, Any]`): Arbitrary data that can be defined by the user when instantiating
            the root of the object. Useful to share arbitrary information throughout the entire
            lifecycle of the translator
    """

    path = ""
    metadata: Dict[str, Any] = {}

    def __init__(
        self,
        result: Any,
        root_result: Any,
        path: instance.InstanceRoute,
        schema: schemanode.DataNode,
        keys: Dict[str, Any],
        candidate: instance.ObjectMember,
        running: Optional[instance.ObjectMember],
        replace: bool,
        extra: Dict[str, Any],
    ) -> None:
        self.result = result
        self.root_result = root_result
        self.path = path
        self.schema = schema
        self.keys = keys
        self.candidate = candidate
        self.running = running
        self.replace = replace
        self.to_remove: List[instance.ArrayEntry] = []
        self.values_to_remove: List[Any] = []
        self.extra = extra

    def init(self) -> None:
        """
        Called only by the :obj:`RootTranslator` in the very beginning of the processing. This
        function may be used to preprocess the result object or for anything else
        that may be needed to do before the actual processing starts.
        """
        pass

    def post(self) -> None:
        """
        Called only by the :obj:`RootTranslator` in the very end of the processing.
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

    def pre_process_list(self) -> None:
        """
        This is called before processing a list.
        """
        pass

    def pre_process_leaf_list(self) -> None:
        """
        This is called before processing a leaf-list.
        """
        pass

    def post_process_list(self) -> None:
        """
        This is called after processing a list.
        """
        pass

    def post_process_leaf_list(self) -> None:
        """
        This is called after processing a leaf-list.
        """
        pass

    @property
    def key(self) -> Any:
        """
        Last key extracted in the current object being processed.
        """
        node = self.schema
        while not isinstance(node, schemanode.ListNode):
            node = node.parent
        return self.keys[node.data_path()]


class Translator:
    """
    Translator classes used to parse groupings need to inherit from this class.
    In addition to the relevant functions and classes to translate children nodes,
    they may include a ``Yangify`` class that inherits from :obj:`TranslatorData`
    to implement some parsing logic.

    Attributes:
        yy (:obj:`TranslatorData`): This attribute will be instantiated using the nested
            class :obj:`Translator.Yangify`. Everything you implement inside your
            ``class Yangify`` will be available through this attribute.

    Example:

        Interface class to parse ``openconfig-interfaces:interfaces/interface`` model::

            class Interface(Parser):
                class Yangify(ParserData):
                    def extract_elements(self) -> Iterator[Tuple[str, Dict[str, Any]]]:
                        for k, v in interfaces_magic:
                            yield k, v
    """

    Yangify = TranslatorData

    def __init__(
        self,
        result: Any,
        root_result: Any,
        path: instance.InstanceRoute,
        dm: DataModel,
        schema: schemanode.DataNode,
        keys: Dict[str, str],
        candidate: instance.ObjectMember,
        running: Optional[instance.ObjectMember],
        replace: bool,
        extra: Dict[str, Any],
    ) -> None:
        self.dm = dm
        self.yy = self.Yangify(
            result, root_result, path, schema, keys, candidate, running, replace, extra
        )

    def _obj_changed(self, irt: instance.InstanceRoute) -> bool:
        if self.yy.running is None:
            running = None
        else:
            try:
                running = self.yy.running.goto(irt).value
            except NonexistentInstance:
                running = None
        try:
            candidate = self.yy.candidate.goto(irt).value
        except NonexistentInstance:
            candidate = None
        return cast(bool, running != candidate)

    def _present_in_candidate(self, irt: instance.InstanceRoute) -> bool:
        try:
            self.yy.candidate.goto(irt)
            return True
        except NonexistentInstance:
            return False

    def _present_in_running(self, irt: instance.InstanceRoute) -> bool:
        if self.yy.running:
            try:
                self.yy.running.goto(irt)
                return True
            except NonexistentInstance:
                return False
        else:
            return False

    def _obj_remove_running(self, irt: instance.InstanceRoute) -> bool:
        if self.yy.running is None:
            return False
        try:
            self.yy.running.goto(irt)
        except NonexistentInstance:
            return False
        try:
            self.yy.candidate.goto(irt)
        except NonexistentInstance:
            return True
        return False

    def _obj_forward_progress_leaf(self, path: instance.InstanceRoute) -> bool:
        if self.yy.replace:
            if self._present_in_candidate(path):
                return True
            else:
                return False
        return self._obj_changed(path) or self._obj_remove_running(path)

    def _obj_forward_progress_container(self, path: instance.InstanceRoute) -> bool:
        return self._present_in_candidate(path) or self._present_in_running(path)

    def __str__(self) -> str:
        return str(self.yy.schema.data_path())

    def _get_child(self, child: schemanode.DataNode) -> Optional["Translator"]:
        child_name = child.name.replace("-", "_")
        c_type: Optional[Type[Translator]] = getattr(self, child_name, None)
        if not c_type:
            return None
        if not issubclass(c_type, Translator):
            raise ValueError(f"{c_type.__qualname__} doesn't inherit from Translator")
        child_path = self._append_node_to_path(self.yy.path, child)
        return c_type(
            self.yy.result,
            self.yy.root_result,
            child_path,
            self.dm,
            child,
            self.yy.keys,
            self.yy.candidate,
            self.yy.running,
            self.yy.replace,
            self.yy.extra,
        )

    def _get_key_name(self, node: schemanode.DataNode) -> str:
        if node.ns == node.parent.ns:
            return cast(str, node.name)
        else:
            return f"{node.ns}:{node.name}"

    def _get_inst(
        self, irt: instance.InstanceRoute, candidate: bool = True
    ) -> instance.InstanceNode:
        inst = self.yy.candidate if candidate else self.yy.running
        if not inst:
            return
        try:
            return inst.goto(irt)
        except NonexistentInstance:
            return None

    def _get_inst_value(
        self, irt: instance.InstanceRoute, candidate: bool = True
    ) -> Any:
        inst = self.yy.candidate if candidate else self.yy.running
        if not inst:
            return
        try:
            return inst.goto(irt).value
        except NonexistentInstance:
            return None

    def _append_node_to_path(
        self, irt: instance.InstanceRoute, schema_node: schemanode.DataNode
    ) -> instance.InstanceRoute:
        candidate_irt = instance.InstanceRoute(irt)
        candidate_irt.append(self.dm.parse_instance_id(schema_node.data_path())[-1])
        return candidate_irt

    def _append_child_path(
        self, base_path: instance.InstanceRoute, inst: instance.ArrayEntry
    ) -> instance.EntryKeys:
        key = inst.schema_node.keys[0]
        candidate_irt = instance.InstanceRoute(base_path)
        candidate_irt.append(instance.EntryKeys({key: inst.value[key[0]]}))
        return candidate_irt

    def _process_leaf(self, leaf: schemanode.DataNode) -> None:
        leaf_path = self._append_node_to_path(self.yy.path, leaf)
        logger.debug("%s: is a leaf", leaf_path)
        if not self._obj_forward_progress_leaf(leaf_path):
            logger.debug("%s: no need to progress", leaf_path)
            return

        child_name = leaf.name.replace("-", "_")
        c = getattr(self, f"{child_name}", None)
        if not c:
            logger.info("%s: (set) not implemented", leaf_path)
            return

        if self._obj_remove_running(leaf_path):
            # TODO: if we decide to have a "use defaults" parameters
            # this will have to be set to `leaf.default
            candidate = None
        else:
            candidate = self._get_inst_value(leaf_path)
        c(candidate)

    def _process_leaf_list(self, leaf_list: schemanode.DataNode) -> None:
        """Process yangson.schemanode.LeafLiftNode data.

        Process leaf-list nodes and populate self.yy.values_to_remove.

        Args:
            leaf_list: yangson.schemanode.LeafListNode

        Returns:
            None

        """
        leaf_path = self._append_node_to_path(self.yy.path, leaf_list)
        logger.debug("%s: is a leaf list", leaf_path)
        if not self._obj_forward_progress_leaf(leaf_path):
            logger.debug("%s: no need to progress", leaf_path)
            return
        try:
            elements = self.yy.candidate.goto(leaf_path)
        except NonexistentInstance:
            elements = None
        if self.yy.running:
            try:
                running = self.yy.running.goto(leaf_path)
            except NonexistentInstance:
                running = []
        else:
            running = []
        self._fill_to_remove_values(elements, running)
        self.yy.pre_process_leaf_list()

        child_name = leaf_list.name.replace("-", "_")
        c = getattr(self, f"{child_name}", None)
        if not c:
            logger.info("%s: (set) not implemented", leaf_path)
            return

        if self._obj_remove_running(leaf_path):
            # TODO: if we decide to have a "use defaults" parameters
            # this will have to be set to `leaf.default
            candidate = None
        elif not self.yy.replace:
            # only process child if there are elements to add
            elements = running.value if running else []
            candidate = [
                i for i in self._get_inst_value(leaf_path) if i not in elements
            ] or []
        else:
            candidate = self._get_inst_value(leaf_path)
        c(candidate)
        self.yy.post_process_leaf_list()

    def _process_container_node(self, node: schemanode.DataNode) -> None:
        node_path = self._append_node_to_path(self.yy.path, node)
        logger.debug("%s: is a container", node_path)
        if not self._obj_forward_progress_container(node_path):
            logger.debug("%s: no need to progress", node_path)
            return
        attr = self._get_child(node)
        if attr:
            if isinstance(node, (schemanode.ContainerNode, schemanode.GroupNode)):
                attr._process_container()
            elif isinstance(node, (schemanode.ListNode,)):
                attr._process_list()
        else:
            logger.info("%s: not implemented", node_path)

    def _process_container(self) -> None:
        logger.debug("%s: processing", self.yy.path)
        self.yy.pre_process()
        for child in self.yy.schema.data_children():
            logger.debug(
                "%s: processing child %s:%s", self.yy.path, child.ns, child.name
            )
            if isinstance(child, (schemanode.ContainerNode, schemanode.GroupNode)):
                if isinstance(child, schemanode.GroupNode):
                    children = child.children
                else:
                    children = [child]
                for c in children:
                    self._process_container_node(c)
            elif isinstance(child, (schemanode.ListNode,)):
                self._process_container_node(child)
            elif isinstance(child, (schemanode.LeafNode)):
                self._process_leaf(child)
            elif isinstance(child, (schemanode.LeafListNode)):
                self._process_leaf_list(child)
            else:
                msg = f"{self.yy.path}: I don't know the type of this element"
                logger.error(msg)
                raise ValueError(msg)
        self.yy.post_process()

    def _fill_to_remove(
        self, candidate: Optional[instance.ObjectMember], running: instance.ObjectMember
    ) -> None:
        self.yy.to_remove = []
        if self.yy.running:
            for element in running:
                irt = self._append_child_path(self.yy.path, element)
                if candidate is not None:
                    try:
                        candidate.top().goto(irt)
                    except NonexistentInstance:
                        self.yy.to_remove.append(element)
                else:
                    self.yy.to_remove.append(element)

    def _fill_to_remove_values(
        self, candidate: Optional[instance.ObjectValue], running: instance.ObjectValue
    ) -> None:
        """
        This method returns the set difference of candidate - running.

        The method uses a list comprehension in order to preserve the list order
        as it is passed in from the caller.  The difference is set on the `values_to_remove`
        class attribute.

        Args:
            candidate: list of values in the candidate leaf-list
            running: list of values in the running leaf-list

        Returns:
            None
        """
        self.yy.values_to_remove = []
        this = running.raw_value() if running else []
        other = candidate.raw_value() if candidate else []
        self.yy.values_to_remove = [i for i in this if i not in other]

    def _extract_key(self, element: instance.ArrayEntry) -> str:
        return cast(str, element.value[element.schema_node.keys[0][0]])

    def _process_list(self) -> None:
        logger.debug("%s: processing list", self)
        try:
            elements = self.yy.candidate.goto(self.yy.path)
        except NonexistentInstance:
            elements = None
        if self.yy.running:
            try:
                running = self.yy.running.goto(self.yy.path)
            except NonexistentInstance:
                running = []
        else:
            running = []
        self._fill_to_remove(elements, running)
        self.yy.pre_process_list()
        running_keys = copy.deepcopy(self.yy.keys)
        elements = [] if elements is None else elements
        for element in elements:
            element_path = self._append_child_path(self.yy.path, element)
            if not self._obj_changed(element_path) and not self.yy.replace:
                logger.debug("%s: didn't change or replacing, skipping", element_path)
                continue
            self.yy.keys = copy.deepcopy(running_keys)
            self.yy.keys[self.yy.schema.data_path()] = self._extract_key(element)
            self.__class__(
                self.yy.result,
                self.yy.root_result,
                element_path,
                self.dm,
                self.yy.schema,
                self.yy.keys,
                self.yy.candidate,
                self.yy.running,
                self.yy.replace,
                self.yy.extra,
            )._process_container()
        self.yy.keys = running_keys
        self.yy.post_process_list()


class RootTranslator(Translator):
    """
    This object represents the root of the translator and allows the user to choose which
    parts of the model to translate and with which translators. To do so assign the parser
    classes to class attributes named after the nodes you want to translate.

    Parameters:

        dm: DataModel we are going to be translating

        candidate: This is the data of the object we are translating

        running: This is set when merging one object into
            another. Pretty much like :obj:`TranslatorData.candidate`, but with the running data.

        replace: Whether we are merging candidate into running or replacing it entirely.

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
        candidate: Dict[str, Any],
        running: Optional[Dict[str, Any]] = None,
        replace: bool = False,
        extra: Dict[str, Any] = None,
    ) -> None:
        n = dm.from_raw(candidate)
        if running is not None:
            o = dm.from_raw(running)
        else:
            o = None

        super().__init__(
            result=None,
            root_result=None,
            path=instance.InstanceRoute(),
            dm=dm,
            schema=dm.schema,
            keys={},
            candidate=n,
            running=o,
            replace=replace,
            extra=extra or {},
        )

    def __str__(self) -> str:
        return self.__class__.__qualname__

    def process(self) -> Any:
        self.yy.init()
        self._process_container()
        self.yy.post()
        return self.yy.root_result
