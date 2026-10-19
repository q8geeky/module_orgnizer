import tempfile
import unittest
from pathlib import Path
from organizer_core import organize,sha256_file,unique_destination,load_cache


class OrganizerTests(unittest.TestCase):
    def test_hash_and_dry_run(self):
        with tempfile.TemporaryDirectory() as td:
            p=Path(td)
            file=p/"thing.safetensors"
            file.write_bytes(b"abc")
            result=organize(p,dry_run=True,resolver=lambda digest:"LORA")
            self.assertEqual(result["planned"],1)
            self.assertTrue(file.exists())
            self.assertFalse((p/"LORA").exists())
            self.assertEqual(sha256_file(file),"ba7816bf8f01cfea414140de5dae2223b00361a396177a9cb410ff61f20015ad")

    def test_unknown_file_unchanged(self):
        with tempfile.TemporaryDirectory() as td:
            p=Path(td)
            f=p/"unknown.PT"
            f.write_bytes(b"stuff")
            result=organize(p,dry_run=False,resolver=lambda digest:None)
            self.assertEqual(result["unresolved"],1)
            self.assertTrue(f.exists())

    def test_move_with_collision(self):
        with tempfile.TemporaryDirectory() as td:
            p=Path(td)
            (p/"LORA").mkdir()
            (p/"LORA"/"m.bin").write_bytes(b"old")
            (p/"m.bin").write_bytes(b"new")
            result=organize(p,dry_run=False,resolver=lambda digest:"LORA")
            self.assertEqual(result["moved"],1)
            self.assertEqual((p/"LORA"/"m.bin").read_bytes(),b"old")
            self.assertEqual((p/"LORA"/"m_1.bin").read_bytes(),b"new")
            self.assertIn(sha256_file(p/"LORA"/"m_1.bin"),load_cache(p/".module_organizer_cache.json"))

    def test_name_collision_counter(self):
        with tempfile.TemporaryDirectory() as td:
            p=Path(td)
            (p/"file.pt").write_bytes(b"one")
            self.assertEqual(unique_destination(p,"file.pt").name,"file_1.pt")


if __name__=="__main__":
    unittest.main()
