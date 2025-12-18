from west.commands import WestCommand

# Even though we declare "self" as type WestCommand,
# it really must be an extension class which defines
# the field "subcommands".

def SC_do_add_parser(self: WestCommand,
                     subparser_help_text: str,
                     parser_adder):
    p = parser_adder.add_parser(self.name,
                                help=self.help,
                                description=self.description)

    sp = p.add_subparsers(dest='command',
                          required=True,
                          help=subparser_help_text)

    for sc in self.subcommands: # type: ignore
        sc.add_parser(sp)

    return p

def SC_do_run(self: WestCommand, args, unknown):
    for sc in self.subcommands: # type: ignore
        if args.command == sc.name:
            sc.run(args, unknown, self.topdir, self.manifest, self.config)
            return

class STM32Command(WestCommand):
    '''
    Abstract base class for all STM32 west commands.

    Only top-level commands should inherit from this;
    custom subcommands should inherit from WestCommand.
    '''
