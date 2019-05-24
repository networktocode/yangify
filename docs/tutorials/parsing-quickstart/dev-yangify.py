import argparse
import json
from typing import Any, Dict

import ios_parsing

import textfsm

from yangify import parser
from yangify.parser.text_tree import parse_indented_config

from yangson.datamodel import DataModel
from yangson.exceptions import SchemaError
from yangson.exceptions import SemanticError


LIB = "../yang/yang-library-data.json"

MODELS = ["../yang/yang-modules/ietf", "../yang/yang-modules/openconfig"]

dm = DataModel.from_file(LIB, MODELS)


class IOSParser(parser.RootParser):
    class Yangify(parser.ParserData):
        def init(self) -> None:
            self.root_native = {}
            self.root_native["show run"] = parse_indented_config(
                self.native["show run"].splitlines()
            )
            self.root_native["lldp_data"] = self.native["lldp_data"]
            self.native = self.root_native

    parser = argparse.ArgumentParser(
        description="Yangify parser Tutorial.  Use at least one of the options."
    )
    parser.add_argument("--vlans", help="Use to parse VLANs", action="store_true")
    parser.add_argument(
        "--interfaces", help="Use to parse interfaces", action="store_true"
    )
    parser.add_argument("--lldp", help="Use to parse LLDP", action="store_true")

    args = parser.parse_args()

    if args.interfaces:
        interfaces = ios_parsing.Interfaces
    if args.lldp:
        lldp = ios_parsing.LLdp
    if args.vlans:
        vlans = ios_parsing.Vlans


def pre_parse() -> Dict[str, Any]:
    with open("../data/ios/ntc-r1/config.txt", "r") as f:
        config = f.read()

    with open("../data/ios/ntc-r1/lldp.txt", "r") as f:
        lldp_txt = f.read()
    template = "../data/ntc-templates/cisco_ios_show_lldp_neighbors.template"
    table = textfsm.TextFSM(open(template))

    converted_data = table.ParseText(lldp_txt)

    neighbors: Dict[str, Any] = {}
    for item in converted_data:
        neighbor = item[0]
        local_interface = item[1].replace("Gi", "GigabitEthernet")
        neighbor_interface = item[2]
        if not neighbors.get(local_interface):
            neighbors[local_interface] = []
        neighbor = dict(
            local_interface=local_interface,
            neighbor=neighbor,
            neighbor_interface=neighbor_interface,
        )
        neighbors[local_interface].append(neighbor)

    data: Dict[str, Any] = {}
    data["show run"] = config
    data["lldp_data"] = neighbors
    return data


def main() -> None:

    data = pre_parse()

    p = IOSParser(dm, native=data)

    try:
        result = p.process(validate=True)
    except SchemaError as e:
        print("There was an error parsing.  Trying again with validation disabled.")
        print("***************************")
        print(f"error: {e}")
        p = IOSParser(dm, native=data)
        result = p.process(validate=False)
    except SemanticError as e:
        print("There was an error parsing.  Trying again with validation disabled.")
        print("***************************")
        print(f"error: {e}")
        p = IOSParser(dm, native=data)
        result = p.process(validate=False)

    print(json.dumps(result.raw_value(), indent=4))


if __name__ == "__main__":
    main()
