from yangify.translator.config_tree import ConfigTree

expected_simple = """interface Gi1
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
"""

expected_double_nested = """interface Gi1
   description "A description for Gi1"
   shutdown
   another nest
      more subsubcommands
   exit
!
interface Gi2
   description "A description for Gi2"
   exit
!
logging something something
logging something else
"""


class Test:
    def test_simple(self) -> None:
        config = ConfigTree()
        gi1 = config.new_section("interface Gi1")
        gi1.add_command('   description "A description for Gi1"')
        gi1.add_command("   shutdown")
        gi1.add_command("   exit")
        gi1.add_command("!")
        gi2 = config.new_section("interface Gi2")
        gi2.add_command('   description "A description for Gi2"')
        gi2.add_command("   exit")
        gi2.add_command("!")
        config.add_command("logging something something")
        config.add_command("logging something else")
        assert config.to_string() == expected_simple

    def test_simple_pop(self) -> None:
        config = ConfigTree()
        gi1 = config.new_section("interface Gi1")
        gi1.add_command('   description "A description for Gi1"')
        gi1.add_command("   shutdown")
        gi1.add_command("   exit")
        gi1.add_command("!")
        gi2 = config.new_section("interface Gi2")
        gi2.add_command('   description "A description for Gi2"')
        gi2.add_command("   exit")
        gi2.add_command("!")
        gi3 = config.new_section("interface Gi3")
        gi3.add_command('   description "A description for Gi3"')
        gi3.add_command("   exit")
        gi3.add_command("!")
        config.pop_section("interface Gi3")
        config.add_command("logging something something")
        config.add_command("logging something else")
        assert config.to_string() == expected_simple

    def test_double_nest(self) -> None:
        config = ConfigTree()
        gi1 = config.new_section("interface Gi1")
        gi1.add_command('   description "A description for Gi1"')
        gi1.add_command("   shutdown")
        nest = gi1.new_section("   another nest")
        nest.add_command("      more subsubcommands")
        gi1.add_command("   exit")
        gi1.add_command("!")
        gi2 = config.new_section("interface Gi2")
        gi2.add_command('   description "A description for Gi2"')
        gi2.add_command("   exit")
        gi2.add_command("!")
        config.add_command("logging something something")
        config.add_command("logging something else")
        assert config.to_string() == expected_double_nested
