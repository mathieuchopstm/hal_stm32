#!/usr/bin/env bash

set -euo pipefail

if [ "$#" -ne 3 ]; then
	echo "Usage: $0 <series_name> <cube_pkg_path> <hal_repo_root>"
	exit 1
fi

SERIES_INPUT="$1"
CUBE_PKG="$2"
HAL_REPO="$3"

SERIES_LOWER="${SERIES_INPUT,,}"
SERIES_UPPER="${SERIES_INPUT^^}"

# Keep trailing x/xx suffix lowercase (e.g. STM32H7x, STM32G4xx)
if [[ "$SERIES_LOWER" =~ (xx|x)$ ]]; then
	SUFFIX="${BASH_REMATCH[1]}"
	SERIES_UPPER="${SERIES_UPPER:0:${#SERIES_UPPER}-${#SUFFIX}}${SUFFIX}"
fi

DIFF_CMD="diff --color -BZ -x '*.rej'"

CUBE_DRV_DIR="$CUBE_PKG/Drivers/${SERIES_UPPER}_HAL_Driver"
CUBE_CMSIS_DIR="$CUBE_PKG/Drivers/CMSIS/Device/ST/${SERIES_UPPER}"

ZEPHYR_DRV_DIR="$HAL_REPO/stm32cube/${SERIES_LOWER}/drivers"
ZEPHYR_CMSIS_DIR="$HAL_REPO/stm32cube/${SERIES_LOWER}/soc"

CMSIS_EXCLUDES="-x '*.md' -x 'arm' -x 'gcc' -x 'iar'"

command_names=(
	"HAL headers"
	"HAL legacy headers"
	"HAL configuration"
	"HAL sources"
	"HAL legacy sources"
	"CMSIS sources"
	"CMSIS includes"
)

commands=(
	"$DIFF_CMD \"$CUBE_DRV_DIR/Inc/\" \"$ZEPHYR_DRV_DIR/include/\" -x 'Legacy' -x '*_hal_conf*.h' -x 'stm32_assert.h' -x 'stm32_assert_template.h'"
	"$DIFF_CMD \"$CUBE_DRV_DIR/Inc/Legacy\" \"$ZEPHYR_DRV_DIR/include/Legacy\""
	"$DIFF_CMD \"$CUBE_DRV_DIR/Inc/${SERIES_LOWER}_hal_conf_template.h\" \"$ZEPHYR_DRV_DIR/include/${SERIES_LOWER}_hal_conf.h\""
	"$DIFF_CMD \"$CUBE_DRV_DIR/Src/\" \"$ZEPHYR_DRV_DIR/src/\" -x 'Legacy'"
	"$DIFF_CMD \"$CUBE_DRV_DIR/Src/Legacy/\" \"$ZEPHYR_DRV_DIR/src/Legacy/\""
	"$DIFF_CMD \"$CUBE_CMSIS_DIR/Source/Templates/\" \"$ZEPHYR_CMSIS_DIR/\" -x '*.h' $CMSIS_EXCLUDES"
	"$DIFF_CMD \"$CUBE_CMSIS_DIR/Include/\" \"$ZEPHYR_CMSIS_DIR/\" -x '*.c' $CMSIS_EXCLUDES"
)

for i in "${!commands[@]}"; do
	cmd="${commands[$i]}"
	echo "${command_names[$i]}"
	if eval "$cmd"; then
		printf '\033[35m\tno change detected\033[0m\n'
	else
		status=1
	fi
	echo
done

exit ${status:-0}
