from collections import OrderedDict
from typing import Any, Dict, List


def _attach_data_to_path(
    obj: Any, path_str: str, data: Dict[str, Any], list_: bool = False
) -> None:
    if "#list" not in obj:
        obj["#list"] = []

    path = path_str.split(" ")
    o = obj
    first = True

    while True:
        o["#text"] = " ".join(path)
        p = path.pop(0)
        if not path:
            break
        else:
            if p not in o:
                o[p] = OrderedDict()
            o = o[p]

            if first and list_:
                obj["#list"].append({p: o})
                first = False
    if p in o:
        o[p].update(data)
    else:
        o[p] = data

    # We add a standalong flag to be able to distinguish this situation:
    # switchport
    # switchport mode access
    o[p]["#standalone"] = True


def parse_indented_config(
    config: List[str],
    current_indent: int = 0,
    previous_indent: int = 0,
    nested: bool = False,
) -> Dict[str, Any]:
    """
    This method reads a configuration that conforms to a very poor industry standard
    CLI (aka IOS-style) and returns a nested structure that behaves like a dict.

    Example:
        The following block of configuration::

            interface FastEthernet1
                descrption this is a description
                switchport mode access
                switchport access vlan 1
                shutdown
            interface FastEthernet2
                descrption this is a description
                switchport mode trunk
                switchport trunk allowed vlan 10,20

        Will yield the following dict::

            interface:
                #text: FastEthernet1
                FastEthernet1:
                    #standalone: true
                    descrption:
                        #text: this is a description
                        this:
                            #text: is a description
                            is:
                                #text: a description
                                a:
                                    #text: description
                                    description:
                                        #standalone
                    switchport:
                        #text: access vlan 1
                        mode:
                            #text: access
                            access:
                                #standalone: true
                        access:
                            #text: vlan 1
                            vlan:
                                #text: 1
                                1:
                                    #standalone: true
                    shutdown:
                        #standalone: true
                FastEthernet2:
                    #standalone: true
                    descrption:
                        #text: this is another description
                        this:
                            #text: is another description
                            is:
                                #text: another description
                                a:
                                    #text: description
                                    description:
                                        #standalone
                    switchport:
                        #text: trunk allowed vlan 10,20
                        mode:
                            #text: trunk
                            trunk:
                                #standalone: true
                        trunk:
                            #text: allowed vlan 10,20
                            allowed:
                                #text: vlan 10,20
                                vlan:
                                    #text: 10,20
                                    10,20:
                                        #standalone: true

        Basically, the function does the following:

        1. It uses the indentation of the configuration to build a hierarchy,
           that's for instance how it knows the commands that are nested
           inside the interfaces.

        2. For commands with multiple words in the same line it builds a data
           structure that follows the following rules:

           a. each word goes into a nested dictionary inside the previous word.

           b. if a word is followed by more words, those following words go into
              a subkey ``#text``. For instance,
              ``parsed["interface"]["FastEthernet1"]["description"]["#text"]`` will give you
              the entire description

           c. if a word is not followed by any word, a ``#standalone`` key equal to
              ``True`` is added. For instance,
              ``parsed["interface"]["FastEthernet1"]["shutdown"]["#standalone"]`` will indicate
              the interface is shutdown.
    """
    parsed: Dict[str, Any] = OrderedDict()
    while True:
        if not config:
            break
        line = config.pop(0).rstrip()

        if line.lstrip().startswith("!"):
            continue

        last = line.lstrip()
        leading_spaces = len(line) - len(last)

        #  print("current_indent:{}, previous:{}, leading:{} - {}".format(
        #        current_indent, previous_indent, leading_spaces, line))

        if leading_spaces > current_indent:
            current = parse_indented_config(
                config, leading_spaces, current_indent, True
            )
            _attach_data_to_path(parsed, last, current, nested)
        elif leading_spaces < current_indent:
            config.insert(0, line)
            break
        else:
            if not nested:
                current = parse_indented_config(
                    config, leading_spaces, current_indent, True
                )
                _attach_data_to_path(parsed, last, current, nested)
            else:
                config.insert(0, line)
                break

    return parsed
