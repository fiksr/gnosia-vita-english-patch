# Gnosia (PS Vita `PCSG01277`) English Backport — Handover

## 1. Environment & Key Paths
- **Project Workspace:** `c:\Users\Nikola\Desktop\AI PROJECTS\Gnosia\`
- **Vita3K Install:** `C:\Users\Nikola\AppData\Roaming\Vita3K\Vita3K\ux0\app\PCSG01277\`
  - Original backups: `eboot.bin.orig`, `game_data\game_data.psarc.orig`
- **Dumped Decrypted ELF:** `C:\Users\Nikola\Desktop\Vita3K\elfdumps\PCSG01277\0x81000000-0x81AE3CC8_app0.elf`
- **PC (Steam) Source:** `C:\Program Files (x86)\Steam\steamapps\common\GNOSIA\Gnosia_Data\`
  - Localization triplets (`[JP, EN, ZH]`): `sharedassets0.assets`
  - English UI AssetBundles: `StreamingAssets\aa\StandaloneWindows64\*_en_*.bundle`
- **Vita3K Config:** `C:\Users\Nikola\Desktop\Vita3K\config.yml`

---

## 2. Engine Architecture (Verified)
- **NOT Unity on Vita:** `PCSG01277` uses a custom C++ + Lua (`prx/liblua.suprx`) engine with a TrueType font (`game_data/font/cinecaption228.ttf`).
- **`game_data/game_data.psarc`:** Contains **722 files** (`590` `.png`, `97` `.vag`, `29` `.at9`, `6` `.gxp`). **Zero script/text files.**
- **`eboot.bin` (`app0.elf`):** Contains **all** dialogue, choice, and UI text as UTF-8 null-terminated strings in `.rodata` (`0x759000..0x87b2bb`).
  - Relocation table **`PT_SCE_RELA` (`PHDR 2`, `off=0xae5e30`, `filesz=0x232be8`)** mixes **12-byte** (`fmt=0`, `192,078` entries) and **8-byte** (`fmt=1`, `8` entries) records. **Both** ELF pointers/MOVW+MOVT **and** `PT_SCE_RELA` `r_addend` values must be updated when repointing strings, or Vita3K/Vita reverts pointers at boot.

---

## 3. What Is Built & Working (`tools/`)
1. **`tools/extract_pc_tm.py`** → `translation_memory.json`
   - Parses Unity `[count=3][JP][EN][ZH]` arrays from PC `sharedassets0.assets` (`7,778` exact / `7,771` normalized pairs, with `\\n` → `\n` and `\"` → `"` unescaped).
2. **`delta_translations.json`**
   - Overrides speaker names (`セツ` → `Setsu`, `ステラ` → `Stella`, `レムナン` → `Remnan`), shortens `How to Play` labels (`The Rules`, `UI Guide`), and translates Vita-specific lines (`○`/`△`/`□`/`L`/`R` tutorials, Sha-Ming's Vita-only event, statement summaries, runoff vote, save-slot format).
3. **`tools/patch_elf.py`** → `patched_app0.elf`, `elf_patch_report.json`, and `eboot.bin` (unencrypted FSELF `enc=2, comp=2`)
   - Current stats: `9,419` `.rodata` JP strings → **`7,927` in-place + `1,279` repointed** to extended `PHDR 1` (`1,711` `PT_SCE_RELA` entries updated); `133` unrepointed (unreferenced dead strings); `80` unmatched (mostly internal debug TTY logs).
   - Boots cleanly in Vita3K; ~100% of first-5-minute gameplay dialogue is in English.
4. **UI Texture Pipeline (`76` / `590` `.png`s replaced in `game_data.psarc`):**
   - `tools/unpack_psarc.py` → `extracted_vita_psarc/`
   - `tools/port_ui_textures.py` → `patched_ui_safe/` (1:1 aspect-matched textures like `help_cont*.png`, `data_talent_*.png`, etc.; excludes multi-panel atlases)
   - `tools/composite_menu.py` → `menu.png` (Start Menu buttons, Status, Charisma–Stealth)
   - `tools/composite_entry.py` → `entry.png` (Player Registration panels)
   - `tools/composite_ui_batch.py` → `interface.png` (16 HUD buttons keeping PS `○`/`×`/`△`/`□`/`START` icons) and `vote.png` (4 vote banners)
   - `tools/fix_options.py` → `menu_option.png` (PC-only Display Mode & Resolution removed; labels aligned to Vita's sliders/checkboxes)
   - `tools/pack_psarc.py` → repacks `game_data.psarc`

---

## 4. Open Issues to Fix Next

### Priority 1: Dialogue Line-Wrap (`31`-char split) & 3-Line Box Cutoff
- **Symptom:** The main dialogue box hard-wraps at **31 characters** (splitting words like `Are y\nou`, `these medi\ncal`) and **clips line 4+** at the bottom.
- **Why current `patch_elf.py` still splits words:** `wrap_english` in `tools/patch_elf.py` is currently set to `width=44` expecting the binary wrap-widening patch to work—which it didn't.
- **What was tried and did NOT affect the main dialogue box:**
  1. Changing `0x812a01c2` (`36.0f` → `26.0f`) did not change dialogue font size or wrap width.
  2. Patching `movs r3, #0x1f` → `#0x2d` and `movs r2, #0x14` → `#0x10` at `0x81004af4`, `0x8106536a`, and `0x8129cb5c` (callers of `0x812a3978`) did **not** change the main story dialogue box wrap limit.
  3. A Thumb-2 `BL` code cave at `0x8167951e` (`ldr r1, [r1, #0x40]; cmp r2, r1` inside `0x816793e0`) jumping to `0x87b39c` (`PHDR 0` tail) crashed on New Game with `Invalid read at 0x370ed20 by thread 8 (pc 0x81679522)` / `St12out_of_range`.
- **Two paths forward:**
  - **Path A (Binary fix):** Trace the actual caller/setter that writes `31` (`0x1f`) into `[text_obj + 0x40]` for the main dialogue box (e.g. via `0x816793e0` callers or `0x812a40b6` callers, or fix the `0x8167951e` hook cleanly) AND check where the character advance / font size is actually set so 42–45 chars fit visually inside the 960px box.
  - **Path B (Safe text-only fix):** Immediately set `wrap_english(width=30)` in `tools/patch_elf.py` (stops all mid-word breaks), and condense the `~1,825` strings in `translation_memory.json` that wrap to `> 3` lines at `width=30` down to `<= 3 × 30` chars.

### Priority 2: Remaining Multi-Panel UI Sprite Sheets (`game_data.psarc`)
Raw PC textures are already extracted in `pc_ui_raw/`:
- **In-game HUD / Navigation:** `move.png`, `myroom.png`, `paramChange.png`, `loop.png`, `info.png`, `infoR.png`
- **Data Reference & Crew Index:** `data.png`, `data_all.png`, `data_doctor.png`, `data_engineer.png`, `data_join.png`, `data_log.png`, `data_vote.png`, `cIndex.png`, `charaIndex*.png`, `charaTelling*.png`
- Note: Like `menu.png`, `entry.png`, `interface.png`, and `vote.png`, these have different UV layouts on PC vs Vita and must be composited panel-by-panel onto Vita's original coordinates (never resized whole-image).

### Priority 3: Verify `entry.png` & `menu_option.png`
- Both were rebuilt into `game_data.psarc` and still need visual confirmation in-game after the latest fixes.
