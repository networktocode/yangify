from typing import List, Optional, Union, cast


class ConfigTree:
    """
    ConfigTree is an object that helps you recreate a hierarchical config like::

        interface Gi1
           description "A description for Gi1"
           shutdown
           exit
        !
        interface Gi2
           description "A description for Gi2"
           exit
        !
        logging something something
        logging something else

    Headers represent the begining of the section, i.e., ``Interface Gi1`` and
    ``Interface Gi2`` in our example above (empty for the root object), while
    commands are commands within that section. For instance, to recreate the object
    above you'd do::

        >>> config = ConfigTree()
        >>> gi1 = config.new_section("interface Gi1")
        >>> gi1.add_command("   description \"A description for Gi1\"")
        >>> gi1.add_command("   shutdown")
        >>> gi1.add_command("   exit")
        >>> gi1.add_command("!")
        >>> gi2 = config.new_section("interface Gi2")
        >>> gi2.add_command("   description \"A description for Gi2\"")
        >>> gi2.add_command("   exit")
        >>> gi2.add_command("!")
        >>> config.add_command("logging something something")
        >>> config.add_command("logging something else")
    """

    def __init__(self, header: Optional[str] = None) -> None:
        """
        Initialize object with ``header``.
        """
        self._header: Optional[str] = header
        self._children: List[Union[str, "ConfigTree"]] = []

    def new_section(self, header: str) -> "ConfigTree":
        """
        Create a new section and return it.
        """
        c = ConfigTree(header)
        self._children.append(c)
        return c

    def add_command(self, child: str) -> None:
        """
        Adds a command to the current object
        """
        if child not in self._children:
            self._children.append(child)

    def pop_section(self, header: str) -> "ConfigTree":
        """
        Remove a section from the current object.
        """
        for i, c in enumerate(self._children):
            if isinstance(c, ConfigTree):
                if header == c._header:
                    break
        else:
            raise ValueError(f"couldn't find {header}")
        return cast(ConfigTree, self._children.pop(i))

    def __bool__(self) -> bool:
        return bool(self._children)

    def to_string(self) -> str:
        """
        Convert object to a string
        """
        text = ""
        if self._header:
            text += f"{self._header}\n"
        for c in self._children:
            if isinstance(c, ConfigTree):
                text += f"{c.to_string()}"
            else:
                text += f"{c}\n"
        return text
