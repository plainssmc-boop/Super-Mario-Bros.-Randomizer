import subprocess
import sys
import unittest
from pathlib import Path

import smb1_chaos_randomizer as randomizer


ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "smb1_chaos_randomizer.py"


class RandomizerCoreTests(unittest.TestCase):
    def test_enemy_area_pointer_round_trip(self):
        for index in range(randomizer.ENEMY_AREA_COUNT):
            pointer = randomizer.enemy_area_pointer_for_index(index)
            self.assertEqual(
                randomizer.enemy_area_index_for_pointer(pointer),
                index,
                f"area index {index} did not round-trip through pointer 0x{pointer:02X}",
            )

    def test_enemy_area_pointer_rejects_out_of_range_indices(self):
        for index in (-1, randomizer.ENEMY_AREA_COUNT):
            with self.assertRaises(ValueError):
                randomizer.enemy_area_pointer_for_index(index)

    def test_cpu_to_file_offset_accounts_for_header_and_trainer(self):
        self.assertEqual(randomizer.cpu_to_file_offset(0x8000, False), 16)
        self.assertEqual(randomizer.cpu_to_file_offset(0x8000, True), 16 + 512)
        self.assertEqual(randomizer.cpu_to_file_offset(0x9CBC, False), 16 + 0x1CBC)

    def test_expected_table_sizes_match_declared_lengths(self):
        self.assertEqual(
            len(randomizer.EXPECTED_AREA_ADDR_OFFSETS),
            randomizer.AREA_ADDR_OFFSETS_LEN,
        )
        self.assertEqual(
            len(randomizer.EXPECTED_WARP_ZONE_NUMBERS),
            randomizer.WARP_ZONE_NUMBERS_LEN,
        )

    def test_main_slots_cover_all_32_visible_level_positions(self):
        slots = randomizer.main_slot_file_offsets(False)
        self.assertEqual(len(slots), 32)
        self.assertEqual(len({offset for _, _, offset, _ in slots}), 32)
        self.assertEqual({world for world, _, _, _ in slots}, set(range(1, 9)))
        self.assertTrue(all(1 <= level <= 4 for _, level, _, _ in slots))

    def test_bonus_slots_are_only_in_expected_worlds(self):
        bonus = randomizer.bonus_slot_file_offsets(False)
        self.assertEqual([world for world, _ in bonus], [1, 2, 4, 7])

    def test_cli_help_runs_without_a_rom(self):
        completed = subprocess.run(
            [sys.executable, str(SCRIPT), "--help"],
            cwd=ROOT,
            check=False,
            capture_output=True,
            text=True,
        )
        self.assertEqual(completed.returncode, 0, completed.stderr)
        self.assertIn("--ai-check", completed.stdout)
        self.assertIn("--warp-mild", completed.stdout)


if __name__ == "__main__":
    unittest.main()
