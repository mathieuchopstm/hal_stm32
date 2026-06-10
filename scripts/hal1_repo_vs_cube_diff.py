#!/usr/bin/env python3

from __future__ import annotations

import argparse
import re
import subprocess
import sys
from dataclasses import dataclass, field
from pathlib import Path


NO_CHANGE_MSG = "\033[35m\tno change detected\033[0m"
WARNING_MSG_COLOR = "\033[33m"
SOFT_WARNING_MSG_COLOR = "\033[36m"
RESET_COLOR = "\033[0m"
BASE_DIFF_ARGS = ["diff", "--color", "-BZ", "-x", "*.rej"]

@dataclass
class DiffCommand:
    name: str
    source: Path
    destination: Path
    exclude: list[str] = field(default_factory=list)
    expected_missing: bool = False

    def build_args(self) -> list[str]:
        args = [*BASE_DIFF_ARGS, str(self.source), str(self.destination)]
        for pattern in self.exclude:
            args.extend(["-x", pattern])
        return args


def normalize_series(series_input: str) -> tuple[str, str]:
    series_lower = series_input.lower()
    series_upper = series_input.upper()

    # Keep trailing x/xx suffix lowercase (e.g. STM32H7x, STM32G4xx).
    suffix_match = re.search(r"(xx|x)$", series_lower)
    if suffix_match:
        suffix = suffix_match.group(1)
        series_upper = f"{series_upper[:-len(suffix)]}{suffix}"

    return series_lower, series_upper


def build_commands(series_lower: str, series_upper: str, cube_pkg: Path, hal_repo: Path) -> list[DiffCommand]:
    cube_drv_dir = cube_pkg / "Drivers" / f"{series_upper}_HAL_Driver"
    cmsis_base = cube_pkg / "Drivers" / "CMSIS" / "Device" / "ST"

    # HACK: STM32WB0 series uses uppercase 'X' suffix for CMSIS
    if series_lower == "stm32wb0x":
        cube_cmsis_dir = cmsis_base / "STM32WB0X"
    else:
        cube_cmsis_dir = cmsis_base / series_upper

    zephyr_drv_dir = hal_repo / "stm32cube" / series_lower / "drivers"
    zephyr_cmsis_dir = hal_repo / "stm32cube" / series_lower / "soc"

    CMSIS_SRC_HDR_EXCLUDES = ["*.md", "arm", "gcc", "iar", "Templates_TZ"]

    return [
        DiffCommand(
            name="HAL configuration",
            source=cube_drv_dir / "Inc" / f"{series_lower}_hal_conf_template.h",
            destination=zephyr_drv_dir / "include" / f"{series_lower}_hal_conf.h",
        ),
        DiffCommand(
            name="HAL headers",
            source=cube_drv_dir / "Inc",
            destination=zephyr_drv_dir / "include",
            exclude=["Legacy", "*_hal_conf*.h", "stm32_assert.h", "stm32_assert_template.h"],
        ),
        DiffCommand(
            name="HAL legacy headers",
            source=cube_drv_dir / "Inc" / "Legacy",
            destination=zephyr_drv_dir / "include" / "Legacy",
        ),
        DiffCommand(
            name="HAL sources",
            source=cube_drv_dir / "Src",
            destination=zephyr_drv_dir / "src",
            exclude=["Legacy"],
        ),
        DiffCommand(
            name="HAL legacy sources",
            source=cube_drv_dir / "Src" / "Legacy",
            destination=zephyr_drv_dir / "src" / "Legacy",
            expected_missing=True,
        ),
        DiffCommand(
            name="CMSIS sources",
            source=cube_cmsis_dir / "Source" / "Templates",
            destination=zephyr_cmsis_dir,
            exclude=["*.h", *CMSIS_SRC_HDR_EXCLUDES],
        ),
        DiffCommand(
            name="CMSIS includes",
            source=cube_cmsis_dir / "Include",
            destination=zephyr_cmsis_dir,
            exclude=["*.c", *CMSIS_SRC_HDR_EXCLUDES],
        ),
        DiffCommand(
            name="CMSIS TrustZone includes",
            source=cube_cmsis_dir / "Include" / "Templates_TZ",
            destination=zephyr_cmsis_dir / "Templates_TZ",
            expected_missing=True,
        )
    ]


def run_diff_command(command: DiffCommand) -> bool:
    print(command.name)

    if not command.source.exists() or not command.destination.exists():
        nonexistent = [str(path) for path in [command.source, command.destination] if not path.exists()]
        if command.expected_missing:
            print(f"{SOFT_WARNING_MSG_COLOR}\tskipped (not found){RESET_COLOR}")
        else:
            print(f"{WARNING_MSG_COLOR}\tskipped ({' and '.join(nonexistent)} not found){RESET_COLOR}")
        print()
        return False

    if command.source.is_file():
        # `diff` display pathes only for directories; do it ourselves for files.
        assert command.destination.is_file(), "Source and destination type mismatch"
        print(f"diff {command.source} {command.destination}")

    result = subprocess.run(command.build_args(), check=False)
    no_change = result.returncode == 0

    if no_change:
        print(NO_CHANGE_MSG)

    print()
    return no_change


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        prog="hal1_repo_vs_cube_diff.py",
        description="Compare STM32 HAL and CMSIS content between Cube package and hal_stm32 repository.",
    )
    parser.add_argument("series_name", help="Series name (example: stm32l1xx)")
    parser.add_argument("cube_pkg_path", help="Path to STM32Cube package")
    parser.add_argument("hal_repo_root", help="Path to hal_stm32 repository root")
    return parser.parse_args()


def main() -> int:
    args = parse_args()

    series_lower, series_upper = normalize_series(args.series_name)
    cube_pkg = Path(args.cube_pkg_path)
    hal_repo = Path(args.hal_repo_root)

    commands = build_commands(series_lower, series_upper, cube_pkg, hal_repo)

    status = 0
    for command in commands:
        if not run_diff_command(command):
            status = 1

    return status


if __name__ == "__main__":
    sys.exit(main())
