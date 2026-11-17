# Gnosia (PS Vita `PCSG01277`) — English Translation Patch (Beta)

**Title ID:** `PCSG01277`  
**Platform:** PlayStation Vita (`rePatch`) & Vita3K (Windows / Linux / Android / macOS)  
**Status:** Playable Beta (97.7% `.rodata` string coverage + 76 localized UI textures)

---

## What This Patch Does
Unlike the PC/Switch Unity ports, the original 2019 PS Vita release of *Gnosia* (`PCSG01277`) runs on a custom C++ + Lua engine where **all dialogue, choices, and UI strings are compiled inside `eboot.bin`** (with zero external script files in `game_data.psarc`).

This toolkit extracts the official English localization from a legal PC (Steam) copy of *Gnosia* and backports it into Vita's `eboot.bin` and `game_data.psarc`:

### 1. Text & Binary Localization (`eboot.bin`)
- **9,206 / 9,419 (97.7%)** `.rodata` Japanese strings translated:
  - **7,937** patched in-place (UTF-8).
  - **1,269** overflowing strings repointed to an extended `PHDR 1` segment, with **1,700** `PT_SCE_RELA` relocation entries updated (supporting both 12-byte `fmt=0` and 8-byte `fmt=1` records).
  - **133** unreferenced/dead duplicate strings skipped; **80** unmatched strings remaining (mostly internal debug TTY logs and room-description placeholders).
- **Vita-Specific Additions ([delta_translations.json](delta_translations.json)):**
  - PlayStation button prompts (`○`, `△`, `□`, `×`, `L`, `R`, `START`).
  - Vita-only Sha-Ming event lines, logical statement summaries, runoff vote labels, and speaker name fixes (`Setsu`, `Stella`, `Remnan`).
- **Binary UI & Dialogue Box Adjustments:**
  - Main Story & Discussion dialogue boxes widened from `31` → `58` chars/line (`3` → `4` lines, font size `40` → `25`) with automatic paragraph reflow at `56` chars.
  - **Command List**, **Skill Setup**, **How to Play**, and **In-Debate Speak Menu** column widths widened (`10` → `22` / `24` → `50` chars) so menu items stay on 1 row and keep cursor alignment intact.

### 2. UI Texture Localization (`game_data.psarc`)
- **76 / 590** `.png` textures replaced from PC's `*_en_*.bundle` Addressables:
  - **Direct 1:1 screens:** `help_cont*.png`, `data_talent_*.png`, `menu_load.png`, `menu_acList.png`, `credit.png`, `help.png`, `window_*.png`, `choise_bg_*.png`.
  - **Panel-by-panel composited atlases** (preserving Vita UV layouts):
    - `menu.png` (Start Menu, Status, Charisma–Stealth)
    - `entry.png` (Player Registration)
    - `interface.png` (16 HUD buttons keeping PlayStation `○`/`×`/`△`/`□`/`START` icons)
    - `vote.png` (4 voting banners)
    - `menu_option.png` (PC-only Display Mode & Resolution sections removed; labels aligned to Vita's sliders/checkboxes)

---

## Known Limitations
1. **Beta / Playtest Status:** Tested in Vita3K through early loops, Player Registration, Start Menu, Options, Command List, and How to Play. Full playthrough and real PS Vita (`rePatch`) hardware testing are still ongoing.
2. **Remaining Japanese Multi-Panel UI Sheets:** The following secondary sprite sheets still use Japanese labels because their UV coordinates differ between PC and Vita and have not yet been composited:
   - Navigation / HUD: `move.png`, `myroom.png`, `paramChange.png`, `loop.png`, `info.png`, `infoR.png`
   - Data Reference & Crew Index: `data.png`, `data_all.png`, `data_doctor.png`, `data_engineer.png`, `data_join.png`, `data_log.png`, `data_vote.png`, `cIndex.png`, `charaIndex*.png`, `charaTelling*.png`
3. **Requirements to Build:** You must supply your own legal PC (Steam) copy of *Gnosia*, decrypted Vita `game_data.psarc`, and decrypted Vita ELF (`app0.elf` dumped via Vita3K's ELF Dumping or `FAGDec`).

---

## How to Build & Install
1. Install Python 3.10+ and dependencies:
   ```bash
   pip install Pillow UnityPy
   ```
2. Update the input/output paths at the top of `tools/extract_pc_tm.py`, `tools/patch_elf.py`, `tools/unpack_psarc.py`, `tools/port_ui_textures.py`, and `tools/pack_psarc.py` to match your system, or run `Apply_Patch.bat` (Windows) / `./apply_patch.sh` (Linux/macOS).
3. Copy the generated `eboot.bin` and `game_data.psarc`:
   - **Vita3K:** `<Vita3K_ux0>/app/PCSG01277/eboot.bin` and `<Vita3K_ux0>/app/PCSG01277/game_data/game_data.psarc` (back up originals first).
   - **Real PS Vita (`rePatch`):** `ux0:rePatch/PCSG01277/eboot.bin` and `ux0:rePatch/PCSG01277/game_data/game_data.psarc`.

---

## Credits & Legal
- **English Localization Source:** Official PC (Steam) localization of *Gnosia* by **Petit Depotto / PLAYISM**.
- **PS Vita Backport & Patch Tooling:** `fiksr`.
- **Legal:** This repository contains **zero copyrighted game assets**—only localization tooling and Vita-specific delta mappings.
