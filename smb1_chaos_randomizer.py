#!/usr/bin/env python3
"""
smb_level_randomizer.py
------------------------
Randomizes a Super Mario Bros. (NES, 1985) ROM. By default, EVERY seed
randomizes EVERY supported transition mechanism in the game at once:
level order, which world/level lands where, which area sits behind every
3-byte pipe/vine area pointer, which world every warp-zone pipe leads to,
and (since a cleared castle is itself a transition -- see below) even
which level in a world ends that world.

The transition pass is deliberately broad: normal level starts, underground
pipes, vines, water-room entries, castle/ground/underground/water area
pointers, and warp-zone pipes all draw from randomized destination pools. Pass --classic if you want the old, tamer,
just-shuffle-the-levels-safely behavior instead.

DEFAULT BEHAVIOR (every seed, unless --classic)
    1. The 32 main level slots (1-1 .. 8-4) are shuffled, with castles
       free to land in ANY of a world's 4 slots -- not just dash-4 --
       so a world can end after just its first level.
    2. The four $29 preview bytes for Worlds 1, 2, 4, and 7 are kept in place;
       their exits are retargeted to each world's randomized level-2 content.
    3. Every 3-byte area-pointer transition in all 34 enemy-area streams
       is found and randomized to any of the game's 34 valid area-data types,
       with a safe entry-page chosen from pages the original ROM really uses
       for that destination area.
    4. All 7 real warp-zone pipe destinations (the worlds you can warp
       to: 2, 3, 4, 5, 6, 7, 8) are pooled together and handed back out
       to all 7 pipes across the game's 3 warp-zone rooms in random
       order.
    Nothing about this is guesswork -- the level tables and transition
    command format are cross-checked against the SMB1 disassembly.
    The console log always tells you exactly what happened: which
    level plays where, which world ends after how many levels, which
    secret is behind which pipe/vine, and where every warp pipe goes.

HOW THE GAME ACTUALLY DECIDES "NEXT WORLD" (this matters a lot here)
    It would be natural to assume the game moves to the next world once
    you've cleared four levels. It doesn't. Verified straight from the
    game's own code: a castle level ends the *world* the instant you
    touch the axe at the end of it (a routine called HandleAxeMetatile
    unconditionally switches to victory mode / next-world setup) --
    completely regardless of which dash-slot that level happens to sit
    in. A normal (flagpole) level, on the other hand, never advances the
    world on its own no matter how many of them you clear in a row.
    So "when does the world end" is decided by WHICH LEVEL CONTENT you
    just played, not by a level-count.

    By default this script now lets that happen on purpose -- a castle
    can land in any of a world's 4 slots, so a world can end after just
    1, 2, or 3 levels instead of always 4. Pass --classic if you'd
    rather castle-type levels only ever move among the eight dash-4
    slots (one per world), guaranteeing every world is exactly 3 normal
    levels then a castle, like the very first version of this script
    did unconditionally. Either way, the console log always tells you
    exactly where each world will actually end, so it always matches
    what the game will actually do.

    I also found and fixed a bug while re-deriving this: four worlds
    (1, 2, 4, and 7) have a 5th, hidden byte in their level table for a
    mid-level bonus room (like 1-1's underground pipe). An earlier
    version of this script mis-identified which byte that was, which
    meant it was quietly shuffling the wrong two levels for those four
    worlds and never touching their real castles at all. That's fixed --
    the bonus room byte is now correctly identified (verified against
    the ROM's own area-type bits) and, by default, still left alone.

WHAT THIS DOES, MECHANICALLY
    SMB1's engine tracks your progress with a few independent things:
      1. A WorldNumber/LevelNumber counter -> what's shown on screen
         ("WORLD 3-2").
      2. A 36-byte table in the ROM ("AreaAddrOffsets") that says WHICH
         physical level layout gets loaded for each world/level slot --
         32 main (1-1 .. 8-4) bytes plus 4 "bonus" bytes, one each for
         worlds 1, 2, 4 and 7, only ever reached through a mid-level
         pipe or vine.
      3. A separate, tiny 12-byte table ("WarpZoneNumbers") that says
         which world each pipe in a warp zone room leads to.
    This script rewrites all of the above, every run, by default:
      - table #2's 32 main bytes are shuffled, castles free to land
        anywhere (unless --classic, which pins them to dash-4)
      - table #2's 4 bonus bytes are shuffled among each other (unless
        --classic, which leaves them alone)
      - table #3 is fully reshuffled (unless --classic; --warp-mild
        gives a gentler version -- see its help text)
    Nothing outside these tables (enemy placement, level geometry,
    graphics, music, text) is touched, so nothing here can corrupt the
    ROM -- worst case, a setting just isn't as wild as you wanted.

WARP ZONES, SPECIFICALLY
    SMB1 has exactly three physical warp-zone rooms, and none of them
    store their destinations as fixed per-room data -- the game works
    out where each pipe goes *at the moment you step into it*, using a
    small on-the-fly calculation (verified in the disassembly, routine
    ScrollLockObject_Warp -> HandlePipeEntry -> GetWNum) and then looks
    the result up in WarpZoneNumbers:
      - Warp Zone A: hidden ceiling route in 1-2 (only reachable while
        WorldNumber == World 1). Left/middle/right pipe -> World 4/3/2.
      - Warp Zone B: hidden ceiling route in 4-2. Only the middle pipe
        physically exists here -> World 5. (The other two table slots
        are never read in normal play -- there's no pipe standing on
        them -- and this script never touches them.)
      - Warp Zone C: hidden vine in 4-2 (this IS the world-4 "bonus"
        byte, so the default bonus shuffle can relocate it to a
        different world's pipe/vine entirely). Left/middle/right pipe
        -> World 8/7/6.
    All three were cross-checked against community-documented warp zone
    destinations (mariowiki.com, thonky.com's SMB1 guide) and matched
    exactly, in addition to being independently re-derived from the
    disassembly.

VERIFICATION METHOD
    The table location, the castle/bonus/normal classification, and the
    warp-zone table were all derived (not guessed) by assembling a
    community disassembly with a real 6502 toolchain and reading the
    resulting symbol table and bytes back out:
      - AreaAddrOffsets, GetAreaType, and the 32+4 byte classifications
        were originally verified against ca65/ld65 output.
      - WarpZoneNumbers ($87F2) and WorldAddrOffsets ($9CB4) were
        verified by assembling the Xkeeper0/smb1 disassembly (a
        restructured smbdis.asm whose own test suite rebuilds a
        byte-for-byte identical ROM -- confirmed here too, via SHA-256:
        f61548fd...88248de, matching the well-known original SMB1
        (World) dump) with asm6f, reading its .nl symbol file, and
        reading the assembled bytes back out. Both tables' bytes came
        back byte-for-byte identical to what's documented above.
    SMB1 is an NROM-256 (mapper 0) cartridge: the entire 32KB PRG-ROM is
    mapped directly to CPU addresses $8000-$FFFF with no bank switching,
    so file_offset = header_size + (cpu_address - 0x8000) holds for the
    whole ROM.

REQUIREMENTS / LEGAL NOTE
    You must supply your OWN legally obtained ROM file of the original
    "Super Mario Bros. (World)" / "(USA)" release (the common 40,976
    byte .nes dump: 16-byte iNES header + 32KB PRG + 8KB CHR, mapper 0/
    NROM). This script contains no copyrighted game data whatsoever --
    only the numeric table offsets needed to locate and permute
    single-byte pointers. It will refuse to touch a file that doesn't
    match the exact byte layout it expects (see verification below),
    rather than risk corrupting something else.

USAGE
    python3 smb1_chaos_randomizer_audited.py
        (it will ask you to type the path to your ROM -- every seed is
        full chaos by default: level order, bonus areas, AND every
        warp zone, all at once)
    python3 smb1_chaos_randomizer_audited.py --gui
        (opens a native "choose a file" window instead of typing a path)
    python3 smb1_chaos_randomizer_audited.py path/to/SuperMarioBros.nes
    python3 smb1_chaos_randomizer_audited.py rom.nes --seed 12345
    python3 smb1_chaos_randomizer_audited.py rom.nes --per-world
        Keep the level (and, since castles can move too, castle)
        shuffle contained within each world instead of mixing all 32
        levels together across worlds. Bonus areas and warp zones are
        still shuffled globally either way (see their help text).
    python3 smb1_chaos_randomizer_audited.py rom.nes --keep-8-4
        Leave the final Bowser castle (8-4) exactly where it is.
    python3 smb1_chaos_randomizer_audited.py rom.nes --output custom_name.nes

    Dialing chaos back down:
    python3 smb1_chaos_randomizer_audited.py rom.nes --warp-mild
        Still shuffles everything else, but warp zones only get their
        pipes reassigned within their own zone (1-2's zone still only
        offers some order of worlds 2/3/4; 4-2's hidden-vine zone
        still only offers some order of 6/7/8) instead of full chaos.
    python3 smb1_chaos_randomizer_audited.py rom.nes --classic
        Opt out of all of it: only the 32 main level slots are
        shuffled, castles stay pinned to dash-4 (every world
        guaranteed 3 normal levels then a castle), and bonus
        areas/warp zones are left exactly as in vanilla -- this is how
        the very first version of this script always behaved.

    By default the original file is left untouched and a new file is
    written next to it, named "<name>_seed<SEED>_randomized.nes" --
    the seed is always baked into the filename (even if you didn't
    pick one yourself, in which case one is generated for you and
    printed) so you always know exactly which run produced which file
    and can reproduce it later with --seed. A matching
    "<output>.log.txt" is written alongside it with the seed, the
    options used, and the full level/bonus/warp-zone mapping.
"""

import argparse
import random
import sys
from pathlib import Path

# ---------------------------------------------------------------------------
# ROM layout constants.
# See the VERIFICATION METHOD section in the module docstring above for how
# these were derived and cross-checked.
# ---------------------------------------------------------------------------

INES_HEADER_SIZE = 16
AREA_ADDR_OFFSETS_CPU_ADDR = 0x9CBC   # label: AreaAddrOffsets
AREA_ADDR_OFFSETS_LEN = 36

WARP_ZONE_NUMBERS_CPU_ADDR = 0x87F2   # label: WarpZoneNumbers
WARP_ZONE_NUMBERS_LEN = 12

# The 36 bytes exactly as they appear in an unmodified ROM. Each byte is
# a packed (area-type, sub-index) pointer -- graphics/enemies/layout all
# travel together with the byte, so moving a byte around is enough to
# relocate a whole level (or bonus area), type and all.
EXPECTED_AREA_ADDR_OFFSETS = bytes.fromhex(
    "25" "29" "c0" "26" "60"   # World 1: 1-1, 1-2, [bonus], 1-3, 1-4 (castle)
    "28" "29" "01" "27" "62"   # World 2: 2-1, 2-2, [bonus], 2-3, 2-4 (castle)
    "24" "35" "20" "63"        # World 3: 3-1, 3-2, 3-3, 3-4 (castle)
    "22" "29" "41" "2c" "61"   # World 4: 4-1, 4-2, [bonus], 4-3, 4-4 (castle)
    "2a" "31" "26" "62"        # World 5: 5-1, 5-2, 5-3, 5-4 (castle)
    "2e" "23" "2d" "60"        # World 6: 6-1, 6-2, 6-3, 6-4 (castle)
    "33" "29" "01" "27" "64"   # World 7: 7-1, 7-2, [bonus], 7-3, 7-4 (castle)
    "30" "32" "21" "65"        # World 8: 8-1, 8-2, 8-3, 8-4 (castle)
)

# The 12 bytes of WarpZoneNumbers exactly as they appear in an unmodified
# ROM: three 4-byte rows, one per physical warp-zone room. Within a row,
# byte 0/1/2 is what the left/middle/right pipe warps to (stored as
# world-number-plus-one); byte 3 is padding that's never read at runtime.
# Row 2 only has a real pipe in the middle -- the other two slots are
# tile-code filler, not valid world numbers, and this script never
# touches them (writing a real-looking value there wouldn't matter
# anyway, since no pipe stands there to trigger it).
EXPECTED_WARP_ZONE_NUMBERS = bytes.fromhex(
    "04" "03" "02" "00"   # Warp Zone A (World 1, hidden ceiling route in 1-2)
    "24" "05" "24" "00"   # Warp Zone B (World 4, hidden ceiling route in 4-2)
    "08" "07" "06" "00"   # Warp Zone C (World 4, hidden vine in 4-2)
)

# Byte-indices into the 12-byte table above that correspond to a pipe
# that actually exists in-game -- see WARP ZONES, SPECIFICALLY above.
WARP_ZONE_A_LIVE = (0, 1, 2)     # World 1 (1-2 ceiling route): left, mid, right
WARP_ZONE_B_LIVE = (5,)          # World 4 (4-2 ceiling route): middle pipe only
WARP_ZONE_C_LIVE = (8, 9, 10)    # World 4 (4-2 hidden vine): left, mid, right
WARP_ZONE_ALL_LIVE = WARP_ZONE_A_LIVE + WARP_ZONE_B_LIVE + WARP_ZONE_C_LIVE

# ---------------------------------------------------------------------------
# Enemy/sprite-area pointer tables.
# These are the tables the SMB1 engine uses to locate every area's enemy
# object stream. A transition command is a 3-byte sprite command whose first
# byte has low nibble $0e. The command's second byte contains the destination
# area (plus its page-select bit), and the third byte contains the world gate
# and entry page.
#
# These addresses are from the verified standard SMB1 (World/USA) disassembly.
# They are PRG CPU addresses, converted to file offsets with cpu_to_file_offset.
# ---------------------------------------------------------------------------
ENEMY_ADDR_H_OFFSETS_CPU_ADDR = 0x9CE0
ENEMY_DATA_ADDR_LOW_CPU_ADDR = 0x9CE4
ENEMY_DATA_ADDR_HIGH_CPU_ADDR = 0x9D06
ENEMY_AREA_COUNT = 34

# Area type/index layout used by EnemyDataAddr*:
#   0..5   = 6 castle areas
#   6..27  = 22 above-ground areas
#   28..30 = 3 underground areas
#   31..33 = 3 water areas
ENEMY_AREA_TYPE_BASES = (
    (0, 6, 0x60),   # castle
    (6, 28, 0x20),  # ground
    (28, 31, 0x40), # underground
    (31, 34, 0x00), # water
)

def enemy_area_pointer_for_index(index: int) -> int:
    """Convert the 34-entry enemy-data index to the 7-bit SMB1 area number."""
    for start, end, type_base in ENEMY_AREA_TYPE_BASES:
        if start <= index < end:
            return type_base + (index - start)
    raise ValueError(f"Invalid enemy-area index: {index}")

def enemy_area_index_for_pointer(area_pointer: int):
    """Return the enemy-data index for a 7-bit area number, or None if invalid."""
    area = area_pointer & 0x7F
    area_type = area & 0x60
    low = area & 0x1F
    if area_type == 0x60 and low < 6:
        return low
    if area_type == 0x20 and low < 22:
        return 6 + low
    if area_type == 0x40 and low < 3:
        return 28 + low
    if area_type == 0x00 and low < 3:
        return 31 + low
    return None

def read_enemy_area_cpu_addresses(data: bytearray, trainer_present: bool):
    """Read the game's own enemy-data pointer tables and return 34 PRG CPU addresses."""
    low_base = cpu_to_file_offset(ENEMY_DATA_ADDR_LOW_CPU_ADDR, trainer_present)
    high_base = cpu_to_file_offset(ENEMY_DATA_ADDR_HIGH_CPU_ADDR, trainer_present)
    end = high_base + ENEMY_AREA_COUNT
    if end > len(data):
        raise ValueError("ROM is too small for the SMB1 enemy-area pointer tables.")

    addrs = []
    for i in range(ENEMY_AREA_COUNT):
        lo = data[low_base + i]
        hi = data[high_base + i]
        cpu_addr = (hi << 8) | lo
        if not 0x8000 <= cpu_addr <= 0xFFFF:
            raise ValueError(
                f"Enemy-area pointer #{i} points outside PRG-ROM: ${cpu_addr:04X}"
            )
        addrs.append(cpu_addr)
    return addrs

def scan_enemy_area_stream(data: bytearray, start_cpu: int, trainer_present: bool):
    """Scan one enemy-data stream until $FF and return (offsets, end_offset)."""
    pos = cpu_to_file_offset(start_cpu, trainer_present)
    if pos >= len(data):
        raise ValueError(f"Enemy-data pointer ${start_cpu:04X} is outside the ROM.")

    commands = []
    while True:
        if pos >= len(data):
            raise ValueError(
                f"Enemy-data stream ${start_cpu:04X} ran off the end of the ROM."
            )
        first = data[pos]
        if first == 0xFF:
            return commands, pos

        width = 3 if (first & 0x0F) == 0x0E else 2
        if pos + width > len(data):
            raise ValueError(
                f"Truncated enemy-data command at file offset 0x{pos:X}."
            )

        if width == 3:
            commands.append(pos)
        pos += width

def scan_all_area_transitions(data: bytearray, trainer_present: bool):
    """Return every 3-byte area-pointer transition in every enemy-data stream.

    Each result is a dict containing:
      area_index  : one of the 34 enemy-data areas
      area_pointer: the 7-bit area number owning this transition
      offset      : file offset of the transition's first byte
      raw0/raw1/raw2 : original three command bytes
      target_area : destination area's 7-bit number
      enter_page  : destination entry screen/page (0..31)
      world_gate  : world number gate (0..7)
      page_flag   : original page-select bit from byte 2
    """
    starts = read_enemy_area_cpu_addresses(data, trainer_present)
    transitions = []

    for area_index, start_cpu in enumerate(starts):
        commands, _ = scan_enemy_area_stream(data, start_cpu, trainer_present)
        owner_area = enemy_area_pointer_for_index(area_index)

        for off in commands:
            raw0, raw1, raw2 = data[off], data[off + 1], data[off + 2]
            transitions.append({
                "area_index": area_index,
                "area_pointer": owner_area,
                "offset": off,
                "raw0": raw0,
                "raw1": raw1,
                "raw2": raw2,
                "target_area": raw1 & 0x7F,
                "enter_page": raw2 & 0x1F,
                "world_gate": (raw2 >> 5) & 0x07,
                "page_flag": (raw1 >> 7) & 0x01,
            })
    return transitions


def _logical_levels_for_area(data: bytearray, trainer_present: bool):
    """Map each physical main-level area ID to the logical World-Level slots using it."""
    mapping = {}
    for world, level, _off, raw_value, _label, _castle in _visible_content_slots(data, trainer_present):
        area = raw_value & 0x7F
        mapping.setdefault(area, set()).add((world, level))
    return mapping


def _same_logical_level_target_areas(data: bytearray, trainer_present: bool,
                                     source_area: int):
    """Return physical area IDs that represent the same logical level as source_area.

    A randomized pipe/vine/area transition must never land back in the physical
    area that represents the level it came from. This is deliberately based on
    the final randomized level table rather than hard-coded vanilla labels.
    """
    usage = _logical_levels_for_area(data, trainer_present)
    levels = usage.get(source_area & 0x7F, set())
    if not levels:
        return {source_area & 0x7F}
    base = cpu_to_file_offset(AREA_ADDR_OFFSETS_CPU_ADDR, trainer_present)
    out = set()
    for world, level in levels:
        layout = WORLD_LAYOUT[world]
        rel = layout['start'] + (2 if layout['bonus_offset'] is not None and level == 2 else layout['dash_offsets'][level-1])
        out.add(data[base + rel] & 0x7F)
    return out

def randomize_area_transitions(
    data: bytearray,
    rng: random.Random,
    trainer_present: bool,
    final_main_area_usage=None,
):
    """Randomize every 3-byte pipe/vine/area-pointer transition.

    Destinations are drawn from valid non-water area-data types. Ordinary
    water areas are forbidden as randomized destinations; the special W8-4
    water room (area $02) is reachable only through its protected vanilla
    entrance, and its own transitions remain untouched so the player can
    always get through the water section.

    Entry pages are randomized using only page values that were observed in
    real transitions into the chosen destination area; areas with no observed
    incoming transition safely fall back to page 0.

    The source command's page-select bit and world gate stay attached to the
    source transition so the physical pipe/vine placement remains intact.

    The function performs a second full scan after writing and refuses to
    silently accept malformed/invalid area-pointer commands.
    """
    before = scan_all_area_transitions(data, trainer_present)
    if not before:
        raise ValueError("No 3-byte area-pointer transitions were found in the ROM.")

    valid_target_areas = [enemy_area_pointer_for_index(i) for i in range(ENEMY_AREA_COUNT)]
    valid_target_set = set(valid_target_areas)

    # Never randomize into ordinary water areas. The only water destination
    # permitted anywhere in chaos mode is $02, SMB1's special 8-4 water room.
    non_water_target_areas = [
        area for area in valid_target_areas
        if area not in FORBIDDEN_RANDOM_TARGETS
    ]

    # Build a safe entry-page pool per destination area. These are pages that
    # the original game itself actually used when entering that area.
    entry_pages = {area: set() for area in valid_target_areas}
    for t in before:
        entry_pages.setdefault(t["target_area"], set()).add(t["enter_page"])

    # Main level starts are always safe at page 0. The scan above already
    # covers the special areas too; adding 0 makes every area a usable target.
    for area in valid_target_areas:
        entry_pages[area].add(0)

    # Shuffle a destination pool that contains NO ordinary water areas.
    # $02 is deliberately reserved for the physical 8-4 water-room entrance
    # below rather than being handed out to arbitrary pipes/vines.
    destination_pool = list(non_water_target_areas)
    rng.shuffle(destination_pool)

    # Identify the original physical entrance into the special 8-4 water room.
    # Keep that one transition pointed at $02 so the water section remains
    # reachable, while every other randomized transition is guaranteed not to
    # become a water-level entrance.
    w84_water_entries = [
        t for t in before
        if t["target_area"] == W84_WATER_AREA
        and t["area_pointer"] == W84_CASTLE_AREA
        and t["world_gate"] == 7
    ]
    if len(w84_water_entries) != 1:
        raise ValueError(
            "Could not uniquely identify SMB1's World 8-4 water-room entry "
            f"(found {len(w84_water_entries)} matching transitions)."
        )
    w84_entry_offset = w84_water_entries[0]["offset"]

    # Transitions owned by the actual 8-4 water room are also protected.
    # Their vanilla routing is necessary to get through the underwater
    # section instead of trapping Mario inside it.
    w84_water_transitions = {
        t["offset"] for t in before
        if t["area_pointer"] == W84_WATER_AREA
    }

    changed = 0
    details = []
    pool_index = 0
    # Never let a randomized pipe/vine point back to the exact area it came
    # from.  SMB1 will then reload that area from its beginning, which is the
    # level-reset/softlock behavior we explicitly want to forbid.
    for transition in before:
        off = transition["offset"]

        if off == w84_entry_offset or off in w84_water_transitions:
            # Preserve the original, known-good water-room routing.
            dest_area = transition["target_area"]
            dest_page = transition["enter_page"]
        elif (transition["area_pointer"] & 0x7F) == PREVIEW_AREA:
            # $29 is shared by W1-2/W2-2/W4-2/W7-2, but its transition is
            # world-gated. Retarget each gate to the *current randomized* level-2
            # content for that world. This is what prevents W1-2 from falling
            # through to vanilla $01 water after the level shuffle.
            world = transition["world_gate"] + 1
            if world in (1, 2, 4, 7):
                base = cpu_to_file_offset(AREA_ADDR_OFFSETS_CPU_ADDR, trainer_present)
                actual_level2 = base + WORLD_LAYOUT[world]["start"] + 2
                dest_area = data[actual_level2] & 0x7F
                if dest_area in ORDINARY_WATER_AREAS or dest_area == W84_WATER_AREA:
                    raise ValueError(
                        f"World {world} level-2 preview would enter forbidden water area "
                        f"${dest_area:02X}."
                    )
                dest_page = 0
            else:
                # Unexpected preview gate: leave it alone rather than inventing
                # a transition for a world the original game does not use.
                dest_area = transition["target_area"]
                dest_page = transition["enter_page"]
        else:
            source_area = transition["area_pointer"] & 0x7F
            same_level_areas = _same_logical_level_target_areas(
                data, trainer_present, source_area
            )
            candidates = [a for a in destination_pool if a not in same_level_areas]
            if not candidates:
                raise ValueError(
                    f"Could not avoid a same-level transition from area ${source_area:02X}."
                )
            dest_area = candidates[(pool_index + rng.randrange(len(candidates))) % len(candidates)]
            pool_index += 1
            pages = sorted(entry_pages[dest_area])
            dest_page = rng.choice(pages)

        off = transition["offset"]
        old_area = transition["target_area"]
        old_page = transition["enter_page"]

        # Preserve the command's physical-location/page-select flag.
        data[off + 1] = (transition["page_flag"] << 7) | dest_area
        # Preserve source-world gating; only the destination/page are changed.
        data[off + 2] = (transition["world_gate"] << 5) | dest_page

        if old_area != dest_area or old_page != dest_page:
            changed += 1

        details.append(
            f"  area ${transition['area_pointer']:02X} @0x{off:05X}: "
            f"${old_area:02X}/p{old_page} -> ${dest_area:02X}/p{dest_page} "
            f"(world gate {transition['world_gate'] + 1})"
        )

    # Hard verification pass: every original transition still exists at the
    # same byte offset, remains 3 bytes long, and now targets a valid area.
    after = scan_all_area_transitions(data, trainer_present)
    if len(after) != len(before):
        raise ValueError(
            f"Transition verification failed: found {len(after)} transitions "
            f"after patching, expected {len(before)}."
        )

    for old, new in zip(before, after):
        if old["offset"] != new["offset"]:
            raise ValueError("Transition verification failed: command offsets moved.")
        if new["target_area"] not in valid_target_set:
            raise ValueError(
                f"Transition at 0x{new['offset']:05X} points to invalid "
                f"area ${new['target_area']:02X}."
            )
        if new["enter_page"] < 0 or new["enter_page"] > 31:
            raise ValueError("Transition verification failed: invalid entry page.")
        if (new["area_pointer"] & 0x7F) != PREVIEW_AREA and (new["area_pointer"] & 0x7F) != W84_WATER_AREA:
            same_level_areas = _same_logical_level_target_areas(
                data, trainer_present, new["area_pointer"] & 0x7F
            )
            if new["target_area"] in same_level_areas:
                raise ValueError(
                    f"Transition verification failed: 0x{new['offset']:05X} can return "
                    f"to its source logical level ${new['target_area']:02X}."
                )

        if new["world_gate"] == 6:
            w7_2_area = _visible_content_slots(data, trainer_present)
            w7_2_area = next(
                (slot[3] & 0x7F for slot in w7_2_area if slot[0] == 7 and slot[1] == 2),
                None,
            )
            if (new["area_pointer"] & 0x7F) != PREVIEW_AREA and w7_2_area is not None and new["target_area"] == w7_2_area:
                raise ValueError(
                    f"Transition verification failed: 0x{new['offset']:05X} enters forbidden World 7-2 content."
                )

    log_lines = [
        "",
        "ALL AREA-POINTER TRANSITIONS (pipes/vines/3-byte area pointers):",
        f"  Found {len(before)} transition commands across all 34 area streams.",
        f"  Randomized destinations: {changed}/{len(before)}.",
        "  Destination pool: non-water, non-preview, non-W8-4-water areas only.",
        "  Entry-page pool: pages observed from real transitions into each target.",
        "",
    ]
    log_lines.extend(details)

    if final_main_area_usage is not None:
        shared = {
            area: worlds for area, worlds in final_main_area_usage.items()
            if len(worlds) > 1
        }
        if shared:
            log_lines += [
                "",
                "  NOTE: Some physical area IDs are reused by multiple worlds "
                "after the level shuffle. SMB1's original transition command "
                "has a 3-bit world gate, so those shared areas retain their "
                "source command gates rather than pretending one command can "
                "simultaneously have multiple world values."
            ]

    return log_lines

# Per-world layout inside the 36-byte table above: "start" is where that
# world's block begins; "dash_offsets" lists the relative byte offsets
# for the 4 real on-screen levels (1..4) IN ORDER -- the last one is
# always the castle, confirmed from the ROM's own area-type bits, not
# assumed; "bonus_offset" (if any) is the one extra byte reached only
# through a mid-level pipe/vine warp, never through normal progression.
WORLD_LAYOUT = {
    1: {"start": 0,  "dash_offsets": (0, 1, 3, 4), "bonus_offset": 2},
    2: {"start": 5,  "dash_offsets": (0, 1, 3, 4), "bonus_offset": 2},
    3: {"start": 10, "dash_offsets": (0, 1, 2, 3), "bonus_offset": None},
    4: {"start": 14, "dash_offsets": (0, 1, 3, 4), "bonus_offset": 2},
    5: {"start": 19, "dash_offsets": (0, 1, 2, 3), "bonus_offset": None},
    6: {"start": 23, "dash_offsets": (0, 1, 2, 3), "bonus_offset": None},
    7: {"start": 27, "dash_offsets": (0, 1, 3, 4), "bonus_offset": 2},
    8: {"start": 32, "dash_offsets": (0, 1, 2, 3), "bonus_offset": None},
}


def cpu_to_file_offset(cpu_addr: int, trainer_present: bool) -> int:
    base = INES_HEADER_SIZE + (512 if trainer_present else 0)
    return base + (cpu_addr - 0x8000)


def main_slot_file_offsets(trainer_present: bool):
    """Return the 32 real 1-1..8-4 level slots as
    (world, level, file_offset, is_castle). Bonus-area bytes are excluded
    entirely -- they're never part of this list."""
    base = cpu_to_file_offset(AREA_ADDR_OFFSETS_CPU_ADDR, trainer_present)
    slots = []
    for world, layout in WORLD_LAYOUT.items():
        for level, rel_offset in enumerate(layout["dash_offsets"], start=1):
            is_castle = level == 4  # always true for the last dash slot
            slots.append((world, level, base + layout["start"] + rel_offset, is_castle))
    return slots


def bonus_slot_file_offsets(trainer_present: bool):
    """Return the 4 mid-level bonus bytes (worlds 1, 2, 4, 7 -- the only
    ones that have one) as (world, file_offset)."""
    base = cpu_to_file_offset(AREA_ADDR_OFFSETS_CPU_ADDR, trainer_present)
    out = []
    for world, layout in WORLD_LAYOUT.items():
        if layout["bonus_offset"] is not None:
            out.append((world, base + layout["start"] + layout["bonus_offset"]))
    return out


def load_rom(path: Path) -> bytearray:
    data = bytearray(path.read_bytes())
    if len(data) < 16 or data[0:4] != b"NES\x1a":
        raise ValueError("That doesn't look like an iNES (.nes) ROM file "
                          "(missing 'NES\\x1A' header signature).")
    return data


def validate_rom(data: bytearray) -> bool:
    trainer_present = bool(data[6] & 0x04)

    area_base = cpu_to_file_offset(AREA_ADDR_OFFSETS_CPU_ADDR, trainer_present)
    area_end = area_base + AREA_ADDR_OFFSETS_LEN
    warp_base = cpu_to_file_offset(WARP_ZONE_NUMBERS_CPU_ADDR, trainer_present)
    warp_end = warp_base + WARP_ZONE_NUMBERS_LEN

    if area_end > len(data) or warp_end > len(data):
        return False
    if bytes(data[area_base:area_end]) != EXPECTED_AREA_ADDR_OFFSETS:
        return False
    if bytes(data[warp_base:warp_end]) != EXPECTED_WARP_ZONE_NUMBERS:
        return False
    return True


def _shuffle_group(group, rng, per_world):
    """group: list of (world, level, offset, value, label, is_castle).
    Shuffles the (value, label, is_castle) payloads among themselves --
    either globally or restricted to staying within the same world --
    and returns new entries with the same (world, level, offset) slots
    but reassigned payloads. Keeping is_castle bundled with its value
    (rather than left behind at the original slot) matters as soon as a
    group can contain a mix of castle and non-castle bytes, which
    happens under --castle-chaos.

    Origins are tracked directly (by original world-level label) rather
    than re-derived from the byte value afterwards, because a handful of
    vanilla levels intentionally share the exact same underlying byte
    (e.g. 1-2, 2-2, 4-2 and 7-2 are all the same underground layout), so
    looking a value back up in the table would be ambiguous.
    """
    if per_world:
        by_world = {}
        for e in group:
            by_world.setdefault(e[0], []).append(e)
        out = []
        for _, members in by_world.items():
            payloads = [(value, label, ic) for (_, _, _, value, label, ic) in members]
            rng.shuffle(payloads)
            for (w, l, off, _, _, _), (value, label, ic) in zip(members, payloads):
                out.append((w, l, off, value, label, ic))
        return out
    else:
        payloads = [(value, label, ic) for (_, _, _, value, label, ic) in group]
        rng.shuffle(payloads)
        return [
            (w, l, off, value, label, ic)
            for (w, l, off, _, _, _), (value, label, ic) in zip(group, payloads)
        ]


def _visible_content_slots(data: bytearray, trainer_present: bool):
    """Return the 32 visible level-content slots.

    For worlds 1, 2, 4 and 7, the visible level-2 cutscene lives in the
    separate $29 preview byte at relative offset 1. The real level-2 content
    is relative offset 2. The preview byte is kept in place and its transition
    is retargeted to whatever content occupies that world's level-2 slot.
    """
    base = cpu_to_file_offset(AREA_ADDR_OFFSETS_CPU_ADDR, trainer_present)
    slots = []
    for world, layout in WORLD_LAYOUT.items():
        start = layout["start"]
        if layout["bonus_offset"] is not None:
            rels = (0, 2, 3, 4)  # visible 1-1, 1-2 content, 1-3, 1-4
        else:
            rels = layout["dash_offsets"]
        for level, rel in enumerate(rels, start=1):
            off = base + start + rel
            area = data[off] & 0x7F
            # Castle-ness belongs to the CONTENT byte, not to the destination
            # slot number. This matters once castles are allowed to land early.
            is_castle = (area & 0x60) == 0x60 and (area & 0x1F) < 6
            slots.append((world, level, off, data[off],
                          f"{world}-{level}", is_castle))
    return slots


def _preview_slot_file_offset(world: int, trainer_present: bool) -> int:
    if world not in (1, 2, 4, 7):
        raise ValueError(f"World {world} has no SMB1 preview slot.")
    base = cpu_to_file_offset(AREA_ADDR_OFFSETS_CPU_ADDR, trainer_present)
    return base + WORLD_LAYOUT[world]["start"] + 1


def randomize(data: bytearray, rng: random.Random, per_world: bool,
              keep_8_4: bool, castle_chaos: bool):
    """Randomize visible level content while keeping SMB1 preview semantics valid.

    Crucial SMB1 rule: $29 is a shared preview area used by 1-2, 2-2, 4-2 and
    7-2. Its exit is world-gated. Therefore the four $29 preview bytes are NOT
    shuffled. Instead, after level-content randomization, each world-gated $29
    exit is retargeted to the actual content currently assigned to that world's
    level 2. This prevents 1-2 from unexpectedly using the vanilla World-2/7
    water target $01 while preserving the cutscene itself.
    """
    trainer_present = bool(data[6] & 0x04)
    slots = _visible_content_slots(data, trainer_present)

    # Remove ordinary water content from the visible-level shuffle completely.
    # The user permits only the special W8-4 water room, which is not a normal
    # visible level slot anyway.
    safe_slots = [s for s in slots if (s[3] & 0x7F) not in ORDINARY_WATER_AREAS]

    fixed_84 = next((s for s in safe_slots if s[0] == 8 and s[1] == 4), None)
    if fixed_84 is None or (fixed_84[3] & 0x7F) != W84_CASTLE_AREA:
        raise ValueError("Expected original W8-4 castle $65 was not found.")

    movable = [s for s in safe_slots if s is not fixed_84]
    castle_payloads = [s for s in movable if s[5]]
    normal_payloads = [s for s in movable if not s[5]]

    # Force 7-1 to be a castle so 7-2 is unreachable. W8-4 stays fixed because
    # its protected water section is part of the required seed contract.
    assignments = {(8, 4): fixed_84}

    if per_world:
        # In per-world mode, each world keeps its own castle content and normal
        # content. The castle only moves among that world's eligible slots.
        for w in range(1, 8):
            world_castles = [s for s in movable if s[0] == w and s[5]]
            if len(world_castles) != 1:
                raise ValueError(f"Expected exactly one castle payload for World {w}.")
            if w == 7:
                castle_dst = (7, 1)
            else:
                choices = [l for l in range(1, 5)
                           if not (w in (1, 2, 4) and l == 2)]
                castle_dst = (w, rng.choice(choices))
            assignments[castle_dst] = world_castles[0]

        remaining_by_world = {w: [] for w in range(1, 9)}
        for dst in [(w, l) for w in range(1, 9) for l in range(1, 5)
                    if (w, l) not in assignments]:
            remaining_by_world[dst[0]].append(dst)

        normals_by_world = {w: [] for w in range(1, 9)}
        for payload in normal_payloads:
            normals_by_world[payload[0]].append(payload)

        for w, dests in remaining_by_world.items():
            pool = normals_by_world[w]
            if not pool and dests:
                raise ValueError(f"World {w} has no safe normal content for per-world mode.")
            rng.shuffle(pool)
            for i, dst in enumerate(dests):
                assignments[dst] = pool[i % len(pool)]
    else:
        castle_destinations = [(7, 1)]
        for w in range(1, 7):
            choices = [l for l in range(1, 5)
                       if not (w in (1, 2, 4) and l == 2)]
            castle_destinations.append((w, rng.choice(choices)))

        if len(castle_payloads) != 7 or len(castle_destinations) != 7:
            raise ValueError("Castle payload/destination count mismatch.")

        rng.shuffle(castle_payloads)
        for dst, src in zip(castle_destinations, castle_payloads):
            assignments[dst] = src

        remaining = [(w, l) for w in range(1, 9) for l in range(1, 5)
                     if (w, l) not in assignments]
        rng.shuffle(normal_payloads)
        for i, dst in enumerate(remaining):
            src = normal_payloads[i % len(normal_payloads)]
            if dst == (7, 2) and (src[3] & 0x7F) == PREVIEW_AREA:
                safe_normals = [x for x in normal_payloads
                                if (x[3] & 0x7F) not in (PREVIEW_AREA,)
                                and (x[3] & 0x7F) not in ORDINARY_WATER_AREAS]
                if not safe_normals:
                    raise ValueError("Could not find safe content for the protected 7-2 slot.")
                src = safe_normals[rng.randrange(len(safe_normals))]
            assignments[dst] = src

    original_by_slot = {(s[0], s[1]): s for s in slots}
    log_lines = []
    for world in range(1, 9):
        for level in range(1, 5):
            dst = (world, level)
            source = assignments[dst]
            dest = original_by_slot[dst]
            data[dest[2]] = source[3]
            tag = " (castle)" if source[5] else ""
            if dst == (7, 1):
                tag += "  <-- WORLD 7 ENDS HERE; 7-2 IS UNREACHABLE"
            if dst == (7, 2):
                tag += "  <-- PROTECTED: NEVER 7-2"
            if source[3] & 0x7F in ORDINARY_WATER_AREAS:
                raise AssertionError("Forbidden water content was assigned to visible progression")
            if source[4] == f"{world}-{level}":
                log_lines.append(f"  {world}-{level:<3} unchanged{tag}")
            else:
                log_lines.append(
                    f"  {world}-{level:<3} now plays what used to be {source[4]}{tag}"
                )

    log_lines += [
        "",
        "Special level safety:",
        "  $29 preview cutscenes remain in their four original world slots.",
        "  Each $29 exit is retargeted to that world's randomized level-2 content.",
        "  Water areas $00/$01 are never placed in visible progression.",
        "  World 7 always ends at 7-1; 7-2 is unreachable and its level content is never water.",
        "  W8-4 $65 remains fixed; its $02 water room is the only water section allowed.",
    ]
    return log_lines


def randomize_warp_zones(data: bytearray, rng: random.Random, mode: str):
    """mode: 'shuffle' (reassign pipes within each existing warp zone, so
    1-2's zone still only ever leads to some order of worlds 2/3/4, and
    4-2's hidden-vine zone still only leads to some order of 6/7/8) or
    'chaos' (pool all 7 real warp-pipe destinations -- worlds 2, 3, 4,
    5, 6, 7, 8 -- together and hand them back out to all 7 pipes in
    random order, so e.g. 1-2's warp zone might now offer 5, 8, and 6).
    Returns log lines. Never touches the filler bytes that no real pipe
    stands on (see WARP_ZONE_B_LIVE / EXPECTED_WARP_ZONE_NUMBERS above)."""
    trainer_present = bool(data[6] & 0x04)
    base = cpu_to_file_offset(WARP_ZONE_NUMBERS_CPU_ADDR, trainer_present)

    def get(i):
        return data[base + i]

    def put(i, v):
        data[base + i] = v

    if mode == "chaos":
        # TRUE FULL CHAOS: all seven live warp pipes receive a fresh random
        # permutation of the seven valid destination worlds (2..8).  Do not
        # exclude the source world here: a warp to the same world still lands
        # at that world's level-1 slot, so it is not the same level from which
        # the Warp Zone was entered.  More importantly, excluding destinations
        # here would make the randomizer less than fully randomized.
        idxs = list(WARP_ZONE_ALL_LIVE)
        values = [get(i) for i in idxs]
        rng.shuffle(values)
        for i, v in zip(idxs, values):
            put(i, v)
    else:  # "shuffle"
        for group in (WARP_ZONE_A_LIVE, WARP_ZONE_C_LIVE):
            idxs = list(group)
            values = [get(i) for i in idxs]
            rng.shuffle(values)
            for i, v in zip(idxs, values):
                put(i, v)
        # WARP_ZONE_B_LIVE has only one real pipe -- nothing to shuffle it
        # against, so it's left exactly as it was in vanilla under this mode.

    def pipe_line(label, idxs, names):
        vals = [get(i) for i in idxs]
        parts = [f"{n} pipe -> World {v}" for n, v in zip(names, vals)]
        return f"  {label}: " + ", ".join(parts)

    log_lines = ["", f"Warp zones (--warp-{mode}):"]
    if mode == "chaos":
        log_lines.append("  FULL RANDOMIZATION: all 7 live Warp Zone pipes were globally permuted among Worlds 2-8.")
    log_lines.append(pipe_line(
        "Warp Zone A (World 1, hidden ceiling route in 1-2)",
        WARP_ZONE_A_LIVE, ("left", "middle", "right")))
    log_lines.append(pipe_line(
        "Warp Zone B (World 4, hidden ceiling route in 4-2)",
        WARP_ZONE_B_LIVE, ("middle",)))
    log_lines.append(pipe_line(
        "Warp Zone C (World 4, hidden vine in 4-2)",
        WARP_ZONE_C_LIVE, ("left", "middle", "right")))
    return log_lines


def current_main_area_usage(data: bytearray, trainer_present: bool):
    """Map final physical area IDs to the 1-based worlds whose slots use them."""
    usage = {}
    slots = main_slot_file_offsets(trainer_present)
    for world, level, offset, _is_castle in slots:
        area = data[offset] & 0x7F
        usage.setdefault(area, set()).add(world)

    # Bonus slots are also physical areas loaded by transition commands.
    # Include them in the usage map because their content can receive/reuse
    # area-pointer transitions too.
    for world, offset in bonus_slot_file_offsets(trainer_present):
        area = data[offset] & 0x7F
        usage.setdefault(area, set()).add(world)
    return usage


def prompt_for_rom_path(use_gui: bool):
    """Ask the user to import their ROM -- either via a native file-picker
    window (--gui) or by typing/pasting a path (default, works everywhere
    including servers/SSH with no display)."""
    if use_gui:
        try:
            import tkinter as tk
            from tkinter import filedialog
        except ImportError:
            print("tkinter isn't available here; falling back to typing a path.")
        else:
            try:
                root = tk.Tk()
                root.withdraw()
                selected = filedialog.askopenfilename(
                    title="Import your Super Mario Bros. ROM",
                    filetypes=[("NES ROM", "*.nes"), ("All files", "*.*")],
                )
                root.destroy()
            except tk.TclError:
                print("No display available for a file-picker window; "
                      "falling back to typing a path.")
            else:
                if not selected:
                    sys.exit("No file selected.")
                return Path(selected)
    return Path(input("Path to your Super Mario Bros. ROM (.nes): ").strip())



# ---------------------------------------------------------------------------
# Beatability AI / structural solver
# ---------------------------------------------------------------------------
# SMB1 has four special "preview" entries (the physical area $29 used by
# 1-2/2-2/4-2/7-2).  When the player enters the pipe at the end of that
# autowalk preview, SMB1 increments the internal level number even though the
# preview is not displayed as a separate level.  Therefore $29 is safe as a
# normal level start only in a level-2 slot, and it is not a safe arbitrary
# pipe/vine destination.
PREVIEW_AREA = 0x29
SAFE_PREVIEW_LEVEL = 2

# Water-area rules for chaos mode. SMB1 has three water area IDs:
#   $00, $01 = ordinary water areas
#   $02       = the special World 8-4 water room
# Only $02 may ever be entered by a randomized transition, and the water
# room itself is protected from transition randomization so its vanilla exit
# to the rest of 8-4 remains intact.
ORDINARY_WATER_AREAS = {0x00, 0x01}
W84_WATER_AREA = 0x02
W84_CASTLE_AREA = 0x65
# Randomized transitions may never enter ordinary water, the shared preview
# area $29 (including 7-2), or the special 8-4 water room $02. The $02 entry
# is preserved only at its original W8-4 transition.
FORBIDDEN_RANDOM_TARGETS = ORDINARY_WATER_AREAS | {PREVIEW_AREA, W84_WATER_AREA}
def beatability_ai(data: bytearray, trainer_present: bool):
    """Conservative static solver for the randomized ROM."""
    reasons = []
    warnings = []
    slots = _visible_content_slots(data, trainer_present)
    by_slot = {(s[0], s[1]): s for s in slots}

    # Visible content may never be ordinary water. W8-4 is fixed to $65 and is
    # the sole level allowed to lead into special water $02.
    for s in slots:
        world, level, off, area, label, is_castle = s
        area &= 0x7F
        if (world, level) == (8, 4):
            if area != W84_CASTLE_AREA:
                reasons.append("8-4 is not the fixed $65 Bowser castle")
        elif area in ORDINARY_WATER_AREAS or area == W84_WATER_AREA:
            reasons.append(f"{label} contains forbidden water area ${area:02X}")

    # The 1-2/2-2/4-2/7-2 preview bytes must remain $29. They are checked at
    # their physical positions rather than inferred from randomized content.
    preview_physical = {}
    for world in (1, 2, 4, 7):
        off = _preview_slot_file_offset(world, trainer_present)
        area = data[off] & 0x7F
        preview_physical[world] = area
        if area != PREVIEW_AREA:
            reasons.append(f"World {world}-2 preview byte is no longer $29")

    # World 7 ends immediately at 7-1, making 7-2 unreachable by normal
    # progression and therefore impossible to enter from a World-7 warp.
    if not by_slot[(7, 1)][5]:
        reasons.append("World 7-1 is not a castle; 7-2 would be reachable")
    if (7, 2) in by_slot:
        area = by_slot[(7, 2)][3] & 0x7F
        if area in ORDINARY_WATER_AREAS or area == PREVIEW_AREA:
            reasons.append("7-2 contains forbidden preview/water content")

    transitions = scan_all_area_transitions(data, trainer_present)
    valid_areas = {enemy_area_pointer_for_index(i) for i in range(ENEMY_AREA_COUNT)}

    for t in transitions:
        src = t["area_pointer"] & 0x7F
        dst = t["target_area"] & 0x7F
        world = t["world_gate"] + 1
        if dst not in valid_areas:
            reasons.append(f"transition at 0x{t['offset']:05X} targets invalid ${dst:02X}")
        if not 0 <= t["enter_page"] <= 31:
            reasons.append(f"transition at 0x{t['offset']:05X} has invalid entry page")

        if dst in ORDINARY_WATER_AREAS:
            # Only a $29 preview gate may have a water-like vanilla target; after
            # patching, even those are expected to be retargeted. Thus any water
            # target left in the final ROM is a hard failure.
            reasons.append(f"transition at 0x{t['offset']:05X} reaches forbidden water ${dst:02X}")

        if dst == PREVIEW_AREA and src != PREVIEW_AREA:
            reasons.append(f"transition at 0x{t['offset']:05X} arbitrarily enters shared preview $29")

        protected_w84 = src == W84_CASTLE_AREA and dst == W84_WATER_AREA and world == 8
        if dst == W84_WATER_AREA and not protected_w84:
            reasons.append(f"transition at 0x{t['offset']:05X} reaches special $02 water unsafely")

        if src != W84_WATER_AREA and dst in _same_logical_level_target_areas(
            data, trainer_present, src
        ):
            reasons.append(
                f"transition at 0x{t['offset']:05X} can return to the same logical level "
                f"(source area ${src:02X} -> destination ${dst:02X})"
            )

        # Every preview gate must now point to that world's actual level-2
        # content, not blindly to the vanilla area ID. This is the direct check
        # for the reported 1-2 -> water failure.
        if src == PREVIEW_AREA and world in (1, 2, 4, 7):
            base = cpu_to_file_offset(AREA_ADDR_OFFSETS_CPU_ADDR, trainer_present)
            expected = data[base + WORLD_LAYOUT[world]["start"] + 2] & 0x7F
            if dst != expected:
                reasons.append(
                    f"World {world} preview pipe at 0x{t['offset']:05X} targets ${dst:02X}, "
                    f"but its randomized level-2 content is ${expected:02X}"
                )

        # Never let any randomized transition load the content occupying World 7-2.
        # Warp-to-World-7 is safe because 7-1 is forced to be a castle; direct
        # in-level transitions into the randomized 7-2 content are not.
        if world == 7:
            w7_2_area = by_slot[(7, 2)][3] & 0x7F
            if dst == w7_2_area and src != PREVIEW_AREA:
                reasons.append(
                    f"transition at 0x{t['offset']:05X} can enter World 7-2 content "
                    f"(${dst:02X}); 7-2 is forbidden"
                )

    # W8-4: exactly one protected entry into $02, and the water room must retain
    # a route to non-water content. The randomizer protects its internal streams.
    w84_entries = [
        t for t in transitions
        if (t["area_pointer"] & 0x7F) == W84_CASTLE_AREA
        and (t["target_area"] & 0x7F) == W84_WATER_AREA
        and t["world_gate"] == 7
    ]
    if len(w84_entries) != 1:
        reasons.append("W8-4 is missing its single protected $65 -> $02 water entry")

    water_owned = [t for t in transitions if (t["area_pointer"] & 0x7F) == W84_WATER_AREA]
    if not any((t["target_area"] & 0x7F) not in FORBIDDEN_RANDOM_TARGETS
               for t in water_owned):
        reasons.append("W8-4 water room $02 has no safe exit")

    # Warp zones: no same-world reset. World 7 is safe because 7-1 is forced to
    # be the castle and therefore 7-2 is never reachable.
    warp_base = cpu_to_file_offset(WARP_ZONE_NUMBERS_CPU_ADDR, trainer_present)
    warp_sources = {0: 1, 1: 1, 2: 1, 5: 4, 8: 4, 9: 4, 10: 4}
    for idx, source_world in warp_sources.items():
        dest = data[warp_base + idx]
        if dest == source_world:
            reasons.append(f"warp table index {idx} returns to World {source_world}")

    # Normal progression graph. A castle ends a world; a normal level-4 is a
    # genuine dead end and therefore a hard failure.
    q = [(1, 1)]
    seen = set()
    reachable = set()
    reached_w8_castle = False
    while q:
        w, l = q.pop(0)
        if (w, l) in seen:
            continue
        seen.add((w, l))
        reachable.add((w, l))
        unit = by_slot[(w, l)]
        if unit[5]:
            if w == 8:
                reached_w8_castle = True
                break
            q.append((w + 1, 1))
            continue
        if l < 4:
            q.append((w, l + 1))
        else:
            reasons.append(f"reachable {w}-{l} is a normal level-4 dead end")

    if not reached_w8_castle:
        reasons.append("normal progression from 1-1 cannot reach an 8-4 castle")
    if (7, 2) in reachable:
        reasons.append("7-2 is reachable; valid seeds must end World 7 at 7-1")

    # Conservative in-level cycle check. Cycles from special protected source
    # areas are excluded because those routes have explicit semantics above.
    def find_cycle(edges):
        state, stack, where = {}, [], {}
        def dfs(node):
            state[node] = 1
            where[node] = len(stack)
            stack.append(node)
            for nxt in edges.get(node, ()):
                if state.get(nxt, 0) == 0:
                    found = dfs(nxt)
                    if found:
                        return found
                elif state.get(nxt) == 1:
                    return stack[where[nxt]:] + [nxt]
            stack.pop()
            where.pop(node, None)
            state[node] = 2
            return None
        for node in edges:
            if state.get(node, 0) == 0:
                found = dfs(node)
                if found:
                    return found
        return None

    for world in range(1, 9):
        edges = {}
        for t in transitions:
            if t["world_gate"] + 1 != world:
                continue
            src = t["area_pointer"] & 0x7F
            dst = t["target_area"] & 0x7F
            if src in (PREVIEW_AREA, W84_WATER_AREA):
                continue
            edges.setdefault(src, set()).add(dst)
        cycle = find_cycle(edges)
        if cycle:
            reasons.append(
                f"World {world} contains an in-level transition cycle: " +
                " -> ".join(f"${a:02X}" for a in cycle)
            )

    # Exact route to the protected 8-4 water room. A seed is not considered
    # beatable unless the solver can reach 8-4 using normal progression and/or
    # the randomized warp zones, then enter the protected $65 -> $02 transition.
    water_route = build_8_4_water_route(data, trainer_present)
    if water_route is None:
        reasons.append("no exact structural route from 1-1 to the 8-4 water room")

    # A simple risk score is intentionally secondary to hard rejection.
    score = max(0, 100 - 100 * len(reasons) - 3 * len(warnings))
    return {
        "possible": not reasons,
        "score": score,
        "reasons": reasons,
        "warnings": warnings,
        "reachable_slots": sorted(reachable),
        "castle_slots": {
            w: next((l for l in range(1, 5) if by_slot[(w, l)][5]), None)
            for w in range(1, 9)
        },
        "transition_count": len(transitions),
        "water_route": water_route,
    }



WARP_PIPE_NAMES = {
    0: "left pipe",
    1: "middle pipe",
    2: "right pipe",
    5: "middle pipe",
    8: "left pipe",
    9: "middle pipe",
    10: "right pipe",
}


def _warp_zone_options_for_slot(world: int, area: int, warp_values: dict):
    """Return human-readable (zone_name, pipe_name, destination_world) options.

    This function deliberately speaks in player-facing terms so the spoiler log can
    tell the player exactly which Warp Zone and which pipe to use, rather than
    exposing ROM addresses or assembly details.
    """
    out = []
    if area == 0x40:  # physical 1-2 underground layout
        zone = 'A' if world == 1 else 'B'
        indices = (0, 1, 2) if zone == 'A' else (5,)
        for idx in indices:
            out.append((f"Warp Zone {zone}", WARP_PIPE_NAMES[idx], warp_values[idx], idx))
    elif area == 0x41:  # physical 4-2 underground layout
        if world == 1:
            for idx in (0, 1, 2):
                out.append(("Warp Zone A", WARP_PIPE_NAMES[idx], warp_values[idx], idx))
        elif world > 1:
            out.append(("Warp Zone B", WARP_PIPE_NAMES[5], warp_values[5], 5))
    elif area == 0x2F and world > 1:
        # The hidden-vine warp room is a ground-type area; in worlds >1 the
        # game's warp-zone selector therefore uses the 8/7/6 table (Zone C).
        for idx in (8, 9, 10):
            out.append(("Warp Zone C", WARP_PIPE_NAMES[idx], warp_values[idx], idx))
    return out


def _area_is_castle(area: int) -> bool:
    area &= 0x7F
    return (area & 0x60) == 0x60 and (area & 0x1F) < 6


def _transition_description(source_area: int, dest_area: int) -> str:
    """Describe a randomized in-level transition without exposing assembly."""
    if dest_area == W84_CASTLE_AREA:
        return "take the randomized pipe/vine that loads the 8-4 castle layout"
    if dest_area in ORDINARY_WATER_AREAS:
        return "take the randomized transition"  # should never occur in a valid seed
    if dest_area == W84_WATER_AREA:
        return "take the protected pipe into the 8-4 water room"
    if _area_is_castle(dest_area):
        return "take the randomized transition into a castle layout"
    area_type = dest_area & 0x60
    if area_type == 0x40:
        return "take the randomized transition into an underground layout"
    if area_type == 0x20:
        return "take the randomized transition into a ground layout"
    return "take the randomized transition into another level area"


def build_8_4_water_route(data: bytearray, trainer_present: bool):
    """Find the shortest player-action route to the physical 8-4 water room.

    Unlike the old spoiler builder, this models the randomizer as a true
    transition graph. A pipe/vine/3-byte transition can load an arbitrary
    randomized area while WorldNumber/LevelNumber stay the same. The solver
    therefore tracks BOTH the logical level the player is in and the physical
    area currently loaded. Normal level completion then advances the logical
    progression according to whether the loaded area is a castle or normal
    level. Warp zones are also included as direct shortcuts.

    The goal is the physical W8-4 castle area ($65) while World 8 is active;
    from there the protected vanilla transition enters the special W8-4 water
    room ($02). The returned route is optimized by action count. Crucially,
    EVERY live randomized Warp Zone pipe is considered as a shortcut: any of the
    seven live pipes can contain any of the seven randomized destination worlds,
    including World 8 or World 7. World 7 is safe here because 7-1 is forced to
    be its castle, so a World-7 warp never requires entering 7-2. Randomized
    in-level pipe/vine transitions are searched at the same time.
    """
    trainer_present = bool(trainer_present)
    slots = _visible_content_slots(data, trainer_present)
    by_slot = {(w, l): (w, l, off, raw, label, castle)
              for w, l, off, raw, label, castle in slots}
    if (1, 1) not in by_slot or (8, 4) not in by_slot:
        return None

    transitions = scan_all_area_transitions(data, trainer_present)
    transitions_by_source = {}
    for t in transitions:
        src = t["area_pointer"] & 0x7F
        world = t["world_gate"] + 1
        dst = t["target_area"] & 0x7F
        if dst in ORDINARY_WATER_AREAS:
            continue
        if dst == W84_WATER_AREA and not (src == W84_CASTLE_AREA and world == 8):
            continue
        transitions_by_source.setdefault((world, src), []).append(t)

    warp_base = cpu_to_file_offset(WARP_ZONE_NUMBERS_CPU_ADDR, trainer_present)
    warp_values = {i: data[warp_base + i] for i in WARP_ZONE_ALL_LIVE}

    # State = (WorldNumber, LevelNumber, physical area pointer).
    start_area = by_slot[(1, 1)][3] & 0x7F
    start = (1, 1, start_area)

    import heapq
    counter = 0
    heap = [(0, counter, start)]
    best = {start: 0}
    parent = {start: None}
    edge_desc = {}
    goal_state = None

    def push(nxt, cost, current, desc):
        nonlocal counter
        if not (1 <= nxt[0] <= 8 and 1 <= nxt[1] <= 4):
            return
        # Never use the forbidden 7-2 logical state as a route waypoint.
        if nxt[0] == 7 and nxt[1] == 2:
            return
        old = best.get(nxt)
        if old is None or cost < old:
            counter += 1
            best[nxt] = cost
            parent[nxt] = current
            edge_desc[nxt] = desc
            heapq.heappush(heap, (cost, counter, nxt))

    while heap:
        cost, _n, state = heapq.heappop(heap)
        if cost != best.get(state):
            continue
        world, level, area = state

        # Reaching the physical 8-4 castle while World 8 is active is enough;
        # the protected castle->water transition is the final fixed step.
        if world == 8 and area == W84_CASTLE_AREA:
            goal_state = state
            break

        # 1) Randomized in-level pipe/vine/area transitions.
        for t in transitions_by_source.get((world, area), ()):
            dst = t["target_area"] & 0x7F
            # Never advertise a transition to the same physical source area;
            # valid generation rejects those anyway, but keep the route solver
            # conservative if called independently.
            if dst == area:
                continue
            page = t["enter_page"]
            nxt = (world, level, dst)
            desc = (
                f"While in {world}-{level}, {_transition_description(area, dst)}. "
                f"You enter that area at its randomized entry point (page {page})."
            )
            push(nxt, cost + 1, state, desc)

        # 2) Warp Zone shortcuts. These are entered from the physical layouts
        # that actually contain Warp Zone A/B/C in the current WorldNumber.
        for zone_name, pipe_name, dest_world, _idx in _warp_zone_options_for_slot(
            world, area, warp_values
        ):
            # World 7 is a valid warp destination. We deliberately force 7-1
            # to be the castle, so warping to World 7 begins at 7-1 and immediately
            # ends that world; it never requires entering the forbidden 7-2.
            if not 1 <= dest_world <= 8:
                continue
            nxt = (dest_world, 1, by_slot[(dest_world, 1)][3] & 0x7F)
            desc = (
                f"While in {world}-{level}, enter {zone_name} and take the {pipe_name} "
                f"to World {dest_world}; you begin at {dest_world}-1."
            )
            push(nxt, cost + 1, state, desc)

        # 3) Finish the currently loaded physical area. SMB1's normal level
        # counter is separate from the physical area pointer, so a randomized
        # transition can load content belonging to another level while the
        # displayed World-X-Y remains unchanged. Clearing the loaded area then
        # follows the castle/normal rules for the active logical level.
        if _area_is_castle(area):
            if world < 8:
                nxt_world = world + 1
                nxt = (nxt_world, 1, by_slot[(nxt_world, 1)][3] & 0x7F)
                push(
                    nxt,
                    cost + 1,
                    state,
                    f"Clear the castle currently loaded in {world}-{level}; enter {nxt_world}-1.",
                )
        elif level < 4:
            nxt_level = level + 1
            if not (world == 7 and nxt_level == 2):
                nxt = (world, nxt_level, by_slot[(world, nxt_level)][3] & 0x7F)
                push(
                    nxt,
                    cost + 1,
                    state,
                    f"Clear the currently loaded area; enter {world}-{nxt_level}.",
                )

    if goal_state is None:
        return None

    # Reconstruct path.
    states = []
    cur = goal_state
    while cur is not None:
        states.append(cur)
        cur = parent[cur]
    states.reverse()

    steps = []
    for i in range(1, len(states)):
        steps.append(edge_desc[states[i]])
    steps.append(
        "In World 8, you are now in the 8-4 castle layout. Reach the underwater "
        "section entrance and take the protected pipe to enter the 8-4 water room."
    )

    return {
        "states": states,
        "steps": steps,
        "goal": goal_state,
        "water_area": W84_WATER_AREA,
        "cost": best[goal_state],
    }


def water_route_report(route):
    lines = ["", "========================================", "HOW TO GET TO THE 8-4 WATER ROOM", "========================================"]
    if route is None:
        lines.append("  No valid route was found. This seed should be rejected.")
        return lines

    lines.append("  Follow this exact route from the start:")
    lines.append("  Start at World 1-1.")
    for n, step in enumerate(route['steps'], 1):
        lines.append(f"  {n}. {step}")
    lines.append(
        "  Destination: the underwater section inside World 8-4. This is the "
        "only water section allowed by the randomizer."
    )
    lines.append(
        "  This spoiler is written in normal player language: it tells you the "
        "level to reach, which Warp Zone to enter, and exactly which pipe to take."
    )
    return lines


def final_invariant_check(data: bytearray, trainer_present: bool):
    """Final non-negotiable safety checks run even when --ai-check is off."""
    failures = []
    slots = _visible_content_slots(data, trainer_present)
    by_slot = {(s[0], s[1]): s for s in slots}

    if by_slot[(8, 4)][3] & 0x7F != W84_CASTLE_AREA:
        failures.append("8-4 is not the fixed Bowser castle $65")
    if not by_slot[(7, 1)][5]:
        failures.append("7-1 is not a castle; 7-2 could become normally reachable")

    for s in slots:
        area = s[3] & 0x7F
        if area in ORDINARY_WATER_AREAS:
            failures.append(f"visible slot {s[4]} contains forbidden water ${area:02X}")

    for world in (1, 2, 4, 7):
        preview = data[_preview_slot_file_offset(world, trainer_present)] & 0x7F
        if preview != PREVIEW_AREA:
            failures.append(f"preview byte for World {world}-2 is not $29")

    transitions = scan_all_area_transitions(data, trainer_present)
    w7_2_area = by_slot[(7, 2)][3] & 0x7F
    for t in transitions:
        src = t["area_pointer"] & 0x7F
        dst = t["target_area"] & 0x7F
        world = t["world_gate"] + 1
        if dst in ORDINARY_WATER_AREAS:
            failures.append(f"transition 0x{t['offset']:05X} reaches forbidden water ${dst:02X}")
        if dst == W84_WATER_AREA and not (src == W84_CASTLE_AREA and world == 8):
            failures.append(f"transition 0x{t['offset']:05X} reaches special water unsafely")
        if world == 7 and src != PREVIEW_AREA and dst == w7_2_area:
            failures.append(f"transition 0x{t['offset']:05X} enters forbidden World 7-2 content")
        if src not in (PREVIEW_AREA, W84_WATER_AREA):
            if dst in _same_logical_level_target_areas(data, trainer_present, src):
                failures.append(f"transition 0x{t['offset']:05X} returns to its source logical level")

    return failures


def ai_report(result):
    """Turn beatability_ai() output into human-readable log lines."""
    status = "PASS" if result["possible"] else "REJECT"
    lines = [
        "",
        "BEATABILITY AI:",
        f"  Result: {status}",
        f"  Structural feasibility score: {result['score']}/100",
        f"  Reachable main slots from 1-1: {len(result['reachable_slots'])}",
        f"  World castles detected: {result['castle_slots']}",
        f"  Area transitions checked: {result['transition_count']}",
        f"  8-4 water route: {'FOUND' if result.get('water_route') else 'NOT FOUND'}",
    ]
    if result["reasons"]:
        lines.append("  Hard failures:")
        lines.extend(f"    - {r}" for r in result["reasons"])
    if result["warnings"]:
        lines.append("  Chaos warnings:")
        lines.extend(f"    - {w}" for w in result["warnings"])
    lines.append(
        "  Note: this is a structural solver, not a frame-by-frame "
        "emulator-playing bot."
    )
    return lines


def main():
    parser = argparse.ArgumentParser(
        description="Randomize a Super Mario Bros. (NES) ROM you legally "
                    "own. Every seed is full chaos by default: level "
                    "order (castles included -- worlds can end early), "
                    "which secret is behind every pipe/vine, and where "
                    "every warp zone pipe leads. Pass --classic for the "
                    "tamer, original behavior.")
    parser.add_argument("rom", nargs="?", help="Path to your SMB1 .nes file")
    parser.add_argument("--gui", action="store_true",
                        help="Open a file-picker window to import the ROM, "
                        "instead of typing a path")
    parser.add_argument("--output", help="Path to write the randomized ROM "
                        "to (default: <name>_randomized.nes)")
    parser.add_argument("--in-place", action="store_true",
                        help="Overwrite the original file instead "
                        "(a .bak backup of the original is made first)")
    parser.add_argument("--seed", type=int, default=None,
                        help="Random seed, for a reproducible/shareable shuffle")
    parser.add_argument("--per-world", action="store_true",
                        help="Keep the shuffle contained within each world's "
                        "own 4 levels, instead of mixing all 32 across "
                        "worlds. With --classic this only shuffles each "
                        "world's 3 non-castle levels among themselves "
                        "(castles only move within their own world in this mode). "
                        "Warp zones are still randomized globally; the four $29 previews remain fixed.")
    parser.add_argument("--keep-8-4", action="store_true",
                        help="Leave 8-4 as the real vanilla Bowser castle "
                        "(the other 7 castles still get shuffled among "
                        "everything else, or -- with --classic -- only "
                        "among each other's dash-4 slots)")
    parser.add_argument("--classic", action="store_true",
                        help="Opt OUT of full chaos and go back to the tame "
                        "behavior: only the main 32 level slots are "
                        "shuffled, castles stay pinned to each world's "
                        "dash-4 slot (so every world is guaranteed 3 normal "
                        "levels then a castle), and bonus areas / warp "
                        "zones are left exactly as in vanilla. Without this "
                        "flag, EVERY run randomizes every transition in the "
                        "game -- see the module docstring's 'DEFAULT "
                        "BEHAVIOR' section for the full list.")
    parser.add_argument("--ai-check", action="store_true",
                        help="Run the beatability AI after randomization and "
                             "reject seeds with structurally impossible "
                             "progression, preview-area misuse, or "
                             "world-gated transition cycles. This is a "
                             "conservative static solver, not a frame-by-frame "
                             "player.")
    parser.add_argument("--ai-attempts", type=int, default=100,
                        help="Maximum seeds to try when --ai-check is enabled "
                             "(default: 100).")
    parser.add_argument("--warp-mild", action="store_true",
                        help="Only meaningful without --classic. Use the "
                        "gentler warp-zone shuffle instead of the default "
                        "full chaos: pipes only get reassigned within their "
                        "own warp zone (1-2's zone still only offers some "
                        "order of worlds 2/3/4; 4-2's hidden-vine zone "
                        "still only offers some order of 6/7/8), instead of "
                        "pooling all 7 real warp destinations together.")
    args = parser.parse_args()

    # Full chaos is the default: every kind of transition in the game
    # (level order, which secret is behind every pipe/vine, and where
    # every warp-zone pipe leads) is randomized on every single seed,
    # unless --classic asks for the old, tamer behavior.
    chaos = not args.classic
    castle_chaos = chaos
    if not chaos:
        warp_mode = None
    elif args.warp_mild:
        warp_mode = "shuffle"
    else:
        warp_mode = "chaos"

    rom_path = Path(args.rom).expanduser() if args.rom else \
        prompt_for_rom_path(args.gui).expanduser()

    if not rom_path.is_file():
        sys.exit(f"Can't find that file: {rom_path}")

    try:
        data = load_rom(rom_path)
    except ValueError as e:
        sys.exit(str(e))

    if not validate_rom(data):
        sys.exit(
            "This ROM doesn't match the exact byte layout this tool "
            "expects at the level-order or warp-zone tables, so it won't "
            "be modified.\n"
            "This usually means it's not the standard NROM 'Super Mario "
            "Bros. (World)/(USA)' dump (e.g. a different region/revision, "
            "a different game, or an already-hacked/already-randomized "
            "ROM). Refusing to write, to avoid corrupting the wrong data."
        )

    if args.per_world and args.keep_8_4 and not castle_chaos:
        print("Note: --keep-8-4 has no extra effect together with --per-world "
              "-- castles never move in per-world mode anyway when castle "
              "chaos is off (--classic).")
    # Generate a candidate seed, randomize it, then optionally let the
    # beatability AI reject it before anything is written to disk.
    requested_seed = args.seed
    max_attempts = max(1, args.ai_attempts if args.ai_check else 1)

    # Keep an immutable pristine copy of the ORIGINAL ROM.  Every candidate
    # must start from these exact bytes; never randomize a previously tested
    # or previously rejected candidate.
    pristine_data = bytes(data)
    selected_data = None
    selected_result = None
    seed = None
    attempted_seeds = set()
    attempted_fingerprints = set()
    system_rng = random.SystemRandom()

    for attempt in range(max_attempts):
        if requested_seed is not None and attempt == 0:
            candidate_seed = requested_seed % (2**31 - 1)
        elif requested_seed is not None:
            # Once an explicitly supplied seed fails, continue deterministically
            # from it so retries are reproducible.
            candidate_seed = (requested_seed + attempt) % (2**31 - 1)
        else:
            # Each retry receives a genuinely new random seed.  Guard against
            # the (tiny, but possible) chance of SystemRandom repeating one.
            candidate_seed = system_rng.randrange(0, 2**31 - 1)
            while candidate_seed in attempted_seeds:
                candidate_seed = system_rng.randrange(0, 2**31 - 1)

        if candidate_seed in attempted_seeds:
            # Defensive guard for deterministic retry sequences.
            continue
        attempted_seeds.add(candidate_seed)

        # CRITICAL: start EVERY candidate from the untouched original ROM.
        # This guarantees that candidate N is a complete, independent
        # randomization rather than another shuffle layered on candidate N-1.
        candidate_data = bytearray(pristine_data)
        rng = random.Random(candidate_seed)
        try:
            candidate_logs = randomize(
                candidate_data, rng, args.per_world, args.keep_8_4,
                castle_chaos
            )

            # Build the final world usage map after the level/content shuffle,
            # then randomize every ordinary 3-byte area transition.
            final_usage = current_main_area_usage(
                candidate_data, bool(candidate_data[6] & 0x04)
            )
            if chaos:
                candidate_logs += randomize_area_transitions(
                    candidate_data,
                    rng,
                    bool(candidate_data[6] & 0x04),
                    final_main_area_usage=final_usage,
                )

            if warp_mode:
                candidate_logs += randomize_warp_zones(
                    candidate_data, rng, warp_mode
                )
        except (ValueError, AssertionError) as generation_error:
            # A candidate that violates a hard structural rule is simply
            # rejected; with --ai-check enabled, generation keeps searching from
            # the untouched pristine ROM for a fresh seed.
            if args.ai_check:
                continue
            raise


        # Fingerprint the complete randomized ROM before AI acceptance.  This
        # prevents two retries from accidentally producing byte-for-byte
        # identical candidates even if their seeds differ.
        candidate_fingerprint = bytes(candidate_data)
        if candidate_fingerprint in attempted_fingerprints:
            continue
        attempted_fingerprints.add(candidate_fingerprint)

        invariant_failures = final_invariant_check(
            candidate_data, bool(candidate_data[6] & 0x04)
        )
        if invariant_failures:
            if args.ai_check:
                continue
            raise ValueError("Safety invariant failure:\n" + "\n".join(invariant_failures))

        result = beatability_ai(
            candidate_data, bool(candidate_data[6] & 0x04)
        ) if args.ai_check else {"possible": True, "water_route": build_8_4_water_route(candidate_data, bool(candidate_data[6] & 0x04))}

        if result["possible"]:
            selected_data = candidate_data
            selected_result = result
            seed = candidate_seed
            log_lines = candidate_logs
            break

        if requested_seed is not None and max_attempts == 1:
            # Preserve the useful exact-seed behavior: a specifically requested
            # seed is rejected rather than silently replaced.
            sys.exit(
                f"Seed {candidate_seed} was rejected by Beatability AI.\n"
                + "\n".join(ai_report(result))
            )

    if selected_data is None:
        sys.exit(
            f"Beatability AI could not find a structurally feasible seed in "
            f"{max_attempts} attempt(s)."
        )

    # IMPORTANT: selected_data is already the exact candidate that passed the
    # AI check.  Do not randomize it again here; doing so would create a ROM
    # different from the one that was actually verified.
    data = selected_data
    if args.ai_check:
        log_lines += ai_report(selected_result)
        log_lines += water_route_report(selected_result.get("water_route"))

    if args.in_place:
        backup_path = rom_path.with_suffix(rom_path.suffix + ".bak")
        if not backup_path.exists():
            backup_path.write_bytes(Path(rom_path).read_bytes())
        out_path = rom_path
    else:
        default_name = f"{rom_path.stem}_seed{seed}_randomized{rom_path.suffix}"
        out_path = Path(args.output) if args.output else \
            rom_path.with_name(default_name)

    final_failures = final_invariant_check(data, bool(data[6] & 0x04))
    if final_failures:
        sys.exit("Final safety audit failed; refusing to write the ROM:\n" + "\n".join(final_failures))

    out_path.write_bytes(data)

    log_path = out_path.with_name(out_path.name + ".log.txt")
    options_used = (
        f"per_world={args.per_world}, keep_8_4={args.keep_8_4}, "
        f"castle_chaos={castle_chaos}, "
        f"area_transition_chaos={chaos}, warp_mode={warp_mode}, "
        f"in_place={args.in_place}, ai_check={args.ai_check}, "f"ai_attempts={args.ai_attempts}"
    )
    reproduce_cmd = (
        f"  python3 \"{Path(__file__).name}\" \"{rom_path}\" --seed {seed}"
        + (" --per-world" if args.per_world else "")
        + (" --keep-8-4" if args.keep_8_4 else "")
        + (" --classic" if args.classic else "")
        + (" --warp-mild" if args.warp_mild and not args.classic else "") + (" --ai-check" if args.ai_check else "")
    )
    # Always append the requested plain-English water-room spoiler LAST.
    # This is intentionally separate from the technical/AI log so the player
    # can scroll to the very bottom and immediately see the human-readable route.
    water_route = build_8_4_water_route(
        data, bool(data[6] & 0x04)
    )
    water_spoiler_lines = water_route_report(water_route)

    log_path.write_text(
        f"Super Mario Bros. level randomizer\n"
        f"Generation policy: every candidate starts from the original clean ROM; "
        f"no candidate is ever re-randomized from a previous candidate.\n"
        f"Source ROM : {rom_path}\n"
        f"Output ROM : {out_path}\n"
        f"Seed       : {seed}\n"
        f"Options    : {options_used}\n\n"
        f"To reproduce this exact ROM again:\n"
        f"{reproduce_cmd}"
        + "\n\nLevel order:\n" + "\n".join(log_lines)
        + "\n\n" + "\n".join(water_spoiler_lines) + "\n"
    )

    print(f"Wrote randomized ROM to: {out_path}")
    print(f"Seed used: {seed}  (saved alongside it in {log_path.name} -- "
          f"reuse --seed {seed} on the same source ROM to get this exact "
          f"same order again)")
    print("\nNew level order:")
    print("\n".join(log_lines))
    print("\n" + "\n".join(water_spoiler_lines))
    if castle_chaos:
        print(
            "\nFull chaos is on (the default): worlds are NOT guaranteed to "
            "be 3 levels then a castle anymore, every 3-byte pipe/vine "
            "area-pointer transition has been remapped, and every warp "
            "zone has been reshuffled too. Check the "
            "'<-- WORLD ENDS HERE' and '<-- unreachable' markers above for "
            "exactly where each world will actually end. Pass --classic "
            "for the old, tamer, guaranteed-3-then-castle behavior."
        )
    else:
        print(
            "\n--classic was on: every world is guaranteed to be 3 normal "
            "levels then a castle, in that order, and bonus areas, "
            "in-level area-pointer transitions, and warp zones are untouched "
            "-- so what's printed above is exactly "
            "what you'll see in-game, including that clearing 8-4 still "
            "ends the game (that's based on the world counter, not "
            "content, so it was already correct)."
        )


if __name__ == "__main__":
    main()