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


    def test_recursive_preview_preserves_subfolder(self):
        with tempfile.TemporaryDirectory() as td:
            root=Path(td)
            inner=root/"models"/"latest"
            inner.mkdir(parents=True)
            (inner/"a.safetensors").write_bytes(b"model")
            events=[]
            result=organize(root,dry_run=True,recursive=True,
                            resolver=lambda digest:"Checkpoint",on_progress=events.append)
            self.assertEqual(result["planned"],1)
            self.assertFalse((root/"Checkpoint").exists())
            self.assertIn("Checkpoint",events[0][-1])
            self.assertIn("models",events[0][-1])

    def test_recursive_apply_does_not_reprocess_classified_folders(self):
        with tempfile.TemporaryDirectory() as td:
            root=Path(td)
            source=root/"models"
            source.mkdir()
            (source/"model.bin").write_bytes(b"data")
            (root/"LORA").mkdir()
            (root/"LORA"/"already.bin").write_bytes(b"old")
            result=organize(root,dry_run=False,recursive=True,
                            resolver=lambda digest:"LORA")
            self.assertEqual(result["moved"],1)
            self.assertEqual((root/"LORA"/"models"/"model.bin").read_bytes(),b"data")
            self.assertEqual((root/"LORA"/"already.bin").read_bytes(),b"old")
            again=organize(root,dry_run=False,recursive=True,offline=True)
            self.assertEqual(again["found"],0)

    def test_offline_skips_unknown_without_resolver(self):
        with tempfile.TemporaryDirectory() as td:
            root=Path(td)
            (root/"first.ckpt").write_bytes(b"data")
            def fail_resolver(digest):
                raise AssertionError("offline must never access the network")
            report=organize(root,dry_run=True,offline=True,resolver=fail_resolver)
            self.assertEqual(report["unresolved"],1)

    def test_recursive_symlink_directory_is_never_followed(self):
        with tempfile.TemporaryDirectory() as td, tempfile.TemporaryDirectory() as outside:
            root=Path(td)
            (Path(outside)/"model.bin").write_bytes(b"outside")
            try:
                (root/"link").symlink_to(outside,target_is_directory=True)
            except (OSError, NotImplementedError):
                self.skipTest("No symlink privileges")
            result=organize(root,dry_run=True,recursive=True,
                            resolver=lambda digest:"LORA")
            self.assertEqual(result["found"],0)


if __name__=="__main__":
    unittest.main()
