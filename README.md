# Super Mario Bros. Chaos Randomizer

A Python randomizer for the original **Super Mario Bros. (NES)** that reshuffles level progression, in-level pipe/vine transitions, and Warp Zone destinations.

The default mode is **full chaos**. It also supports reproducible seeds, a tamer classic mode, per-world shuffling, an optional structural beatability check, and a GUI file picker.

## Features

In full-chaos mode, the script can randomize:

- The 32 main level slots across Worlds 1–8.
- Castle placement, allowing a world to end earlier than its usual `x-4` slot.
- Supported 3-byte area-pointer transitions used by pipes, vines, bonus areas, and other area changes.
- All seven live Warp Zone pipe destinations.
- Safe entry pages for randomized transitions.

It also includes SMB1-specific safety checks for preview areas, water rooms, same-level transition loops, and the special World 8-4 water section.

## Requirements

- Python 3
- CI currently verifies the project on **Python 3.13 and 3.14**, on both Windows and Linux
- A legally obtained, compatible **Super Mario Bros. (World)/(USA)** `.nes` ROM
- No third-party Python packages are required

> **ROM files are not included in this repository.** Do not commit or redistribute copyrighted ROM files. The randomizer validates the ROM layout before modifying anything and refuses incompatible files.

## Quick start

Clone or download this repository, then open PowerShell or a terminal in the project folder.

### Easiest mode — file picker

```powershell
python smb1_chaos_randomizer.py --gui
```

Choose your SMB1 ROM when the window appears.

### Run with a ROM path

Windows / PowerShell:

```powershell
python smb1_chaos_randomizer.py "C:\path\to\Super Mario Bros. (World).nes"
```

macOS / Linux:

```bash
python3 smb1_chaos_randomizer.py "/path/to/Super Mario Bros. (World).nes"
```

By default, the original ROM is left untouched. A randomized ROM is written beside it with the generated seed in the filename, plus a matching log file describing the generated mappings.

## Reproducible seeds

To recreate the same randomization later:

```powershell
python smb1_chaos_randomizer.py "C:\path\to\rom.nes" --seed 12345
```

Using the same compatible source ROM, seed, and options reproduces the same randomized result.

## Useful options

### Structural beatability check

```powershell
python smb1_chaos_randomizer.py "C:\path\to\rom.nes" --ai-check
```

This runs the built-in conservative structural solver and rejects seeds that violate its progression checks. It is **not** a frame-by-frame Mario-playing AI.

Change how many candidate seeds may be tried:

```powershell
python smb1_chaos_randomizer.py "C:\path\to\rom.nes" --ai-check --ai-attempts 250
```

### Keep shuffling inside each world

```powershell
python smb1_chaos_randomizer.py "C:\path\to\rom.nes" --per-world
```

### Classic / tamer mode

```powershell
python smb1_chaos_randomizer.py "C:\path\to\rom.nes" --classic
```

Classic mode only shuffles the main level slots, keeps castles in the normal dash-4 structure, and disables bonus-area / Warp Zone chaos.

### Mild Warp Zone randomization

```powershell
python smb1_chaos_randomizer.py "C:\path\to\rom.nes" --warp-mild
```

This shuffles Warp Zone destinations within their usual groups instead of pooling all seven live Warp Zone destinations together.

### Custom output filename

```powershell
python smb1_chaos_randomizer.py "C:\path\to\rom.nes" --output my_randomized_smb1.nes
```

### Modify the original ROM in place

```powershell
python smb1_chaos_randomizer.py "C:\path\to\rom.nes" --in-place
```

The script creates a `.bak` backup first. The default non-destructive mode is safer.

## Command-line help

```powershell
python smb1_chaos_randomizer.py --help
```

Important options include:

- `--gui`
- `--output PATH`
- `--in-place`
- `--seed NUMBER`
- `--per-world`
- `--keep-8-4`
- `--classic`
- `--ai-check`
- `--ai-attempts NUMBER`
- `--warp-mild`

## Modern development checks

The repository now includes automated checks designed around a current Windows development setup while remaining cross-platform.

On **PowerShell 7**, run:

```powershell
pwsh -File .\tools\dev-check.ps1
```

That command:

- prints the active PowerShell, Python, and Git versions;
- warns if Python is older than the repository's current 3.13/3.14 CI target range;
- compiles the Python source to catch syntax/import-time problems;
- runs the ROM-free regression test suite;
- verifies that the command-line help starts correctly; and
- shows the Git working tree at the end.

You can run the same Python checks directly:

```powershell
python -m compileall -q smb1_chaos_randomizer.py tests
python -m unittest discover -s tests -v
```

GitHub Actions runs those checks automatically on **Windows and Linux with Python 3.13 and 3.14**. The tests deliberately do not require or distribute a copyrighted ROM.

The repository also includes `.gitattributes` rules so modern Git installations keep source/documentation line endings consistent while treating NES ROMs and patch formats as binary data.

## Output files

A normal run creates files similar to:

```text
<rom name>_seed<SEED>_randomized.nes
<rom name>_seed<SEED>_randomized.nes.log.txt
```

The log records the seed, selected options, level mappings, transition mappings, Warp Zone mappings, and World 8-4 route information.

## Compatibility and safety

The randomizer is intentionally strict about its source ROM. It checks important SMB1 tables before writing and refuses ROMs that do not match the expected standard layout rather than risking corruption.

It also performs final structural invariant checks before writing randomized output.

## Repository contents

```text
smb1_chaos_randomizer.py          Main randomizer
tests/test_randomizer.py          ROM-free regression tests
tools/dev-check.ps1               PowerShell 7 developer health check
.github/workflows/python-ci.yml   Windows/Linux Python 3.13/3.14 CI
.gitattributes                    Cross-platform text/binary Git rules
README.md                         Documentation and usage guide
.gitignore                        Blocks ROMs, generated outputs, caches, and editor files
```

## Legal note

This repository contains randomizer code only. It does **not** include Super Mario Bros. game data. You must provide your own legally obtained ROM and comply with the laws that apply where you live.

Super Mario Bros. and Nintendo are trademarks/properties of their respective owners. This is an unofficial fan-made tool and is not affiliated with or endorsed by Nintendo.
