@echo off
echo Running Gnosia Vita English Patch pipeline...
python tools\extract_pc_tm.py || exit /b 1
python tools\patch_elf.py || exit /b 1
python tools\unpack_psarc.py || exit /b 1
python tools\port_ui_textures.py || exit /b 1
python tools\composite_menu.py || exit /b 1
python tools\composite_entry.py || exit /b 1
python tools\composite_ui_batch.py || exit /b 1
python tools\fix_options.py || exit /b 1
python tools\pack_psarc.py || exit /b 1
echo Done! eboot.bin and game_data.psarc updated.
pause
