"""
Cube bundle manager commands
"""
import shutil
import subprocess

from pathlib import Path
from west.commands import WestCommand

from stm32_helpers import STM32Command

class STM32ToolsInstallCommand(STM32Command):
    '''
    Installs STM32 tools used in Zephyr environment:
     - STM32CubeProgrammer
     - ST-Link GDB Server
    '''
    INSTALL_URL = "<...>"

    def __init__(self):
        super().__init__(
            'tools-install',
            'Installs STM32 tools used in Zephyr environment',
            self.__doc__, accepts_unknown_args=False)

    def do_add_parser(self, parser_adder):
        parser = parser_adder.add_parser(self.name,
                                         help=self.help,
                                         description=self.description)

        parser.add_argument('--pin', action='store_true',
                            help="Create `cube` project and pin tool versions")
        parser.add_argument('--prg-version',
                            help="Version of STM32CubeProgrammer to download")
        parser.add_argument('--lnk-version',
                            help="Version of ST-Link GDB Server to download")

        return parser

    def do_run(self, args, unknown):
        if not (cube_tool := shutil.which("cube")):
            self.die("Could not find `cube` bundle manager in PATH.\n"
                     f"Refer to {self.INSTALL_URL} for the installation procedure.")

        def _run(cmd: str, info: str):
            self.banner(f"{info} (cube {cmd})")
            try:
                if (status := subprocess.call([cube_tool] + cmd.split(), timeout=1000)) != 0:
                    self.die(f"Cube bundle manager returned non-zero status code {status}")
            except subprocess.TimeoutExpired:
                self.die(f"Command timed out")

        if args.pin: # Create Cube bundle project if it doesn't exist
            if not Path("./.settings/bundles.store.json").is_file():
                _run("bundle init --project", "Creating Cube bundle manager project")

        cube_prg = f"programmer" + (f'@{args.prg_version}' if args.prg_version else '')
        st_link = f"stlink-gdbserver" + (f'@{args.lnk_version}' if args.lnk_version else '')

        _run(f"bundle install --yes{' --project' if args.pin else ''} {cube_prg} {st_link}", "Installing tools")
