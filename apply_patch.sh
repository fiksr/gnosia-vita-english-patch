#!/usr/bin/env bash
set -e
python3 tools/extract_pc_tm.py
python3 tools/patch_elf.py
python3 tools/unpack_psarc.py
python3 tools/port_ui_textures.py
python3 tools/composite_menu.py
python3 tools/composite_entry.py
python3 tools/composite_ui_batch.py
python3 tools/fix_options.py
python3 tools/pack_psarc.py
echo "Done! eboot.bin and game_data.psarc updated."
