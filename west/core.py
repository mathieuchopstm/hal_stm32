# Copyright (c) 2025 STMicroelectronics
#
# SPDX-License-Identifier: Apache-2.0

'''core.py

STM32 west extension core'''

import subprocess
from inspect import isabstract

from west.commands import WestCommand

from stm32_helpers import STM32Command, SC_do_add_parser, SC_do_run

# Import all files containing commands to ensure
# their classes are visible and can be enumerated
import cube

def cmd_check(cmd, cwd=None, stderr=subprocess.STDOUT):
    return subprocess.check_output(cmd, cwd=cwd, stderr=stderr)

def cmd_exec(cmd, cwd=None, shell=False):
    return subprocess.check_call(cmd, cwd=cwd, shell=shell)

class WestSTM32RootCommand(WestCommand):
    @staticmethod
    def get_stm32_commands() -> list[STM32Command]:
        '''Get a list of all currently defined runner classes.'''
        def inheritors(klass):
            subclasses = set()
            work = [klass]
            while work:
                parent = work.pop()
                for child in parent.__subclasses__():
                    if child not in subclasses:
                        if not isabstract(child):
                            subclasses.add(child)
                        work.append(child)
            return subclasses

        return list(map(lambda k: k(), inheritors(STM32Command)))

    def __init__(self):
        super().__init__(
            'stm32',
            # Keep this in sync with the string in west-commands.yml.
            'STM32 tools for west framework',
            'West commands for STM32',
            accepts_unknown_args=False)

        self.subcommands = self.get_stm32_commands()

    def do_add_parser(self, parser_adder):
        return SC_do_add_parser(self, "Command to execute", parser_adder)
    def do_run(self, args, unknown): return SC_do_run(self, args, unknown)
