from __future__ import annotations

import os
import stat
import tempfile
import unittest

from file_metadata_extractor_tools import extract_metadata


class TestExtractMetadata(unittest.TestCase):
    def setUp(self) -> None:
        self._dir = tempfile.mkdtemp(prefix="fme_")
        self.addCleanup(self._cleanup)

    def _cleanup(self) -> None:
        # Best-effort; files created during a test are removed in-test.
        for entry in os.listdir(self._dir):
            full = os.path.join(self._dir, entry)
            if os.path.islink(full) or os.path.isfile(full):
                os.unlink(full)
        os.rmdir(self._dir)

    def test_regular_file_keys(self) -> None:
        p = os.path.join(self._dir, "a.txt")
        with open(p, "w") as fh:
            fh.write("hello")
        md = extract_metadata(p)
        self.assertEqual(
            set(md.keys()),
            {"size", "mtime", "ctime", "mode", "uid", "gid", "is_symlink"},
        )

    def test_regular_file_size(self) -> None:
        p = os.path.join(self._dir, "a.txt")
        with open(p, "w") as fh:
            fh.write("hello world")
        md = extract_metadata(p)
        self.assertEqual(md["size"], len("hello world"))

    def test_regular_file_uid_gid(self) -> None:
        p = os.path.join(self._dir, "a.txt")
        open(p, "w").close()
        md = extract_metadata(p)
        self.assertEqual(md["uid"], os.geteuid())
        self.assertEqual(md["gid"], os.getegid())

    def test_regular_file_not_symlink(self) -> None:
        p = os.path.join(self._dir, "a.txt")
        open(p, "w").close()
        md = extract_metadata(p)
        self.assertFalse(md["is_symlink"])
        self.assertFalse(stat.S_ISLNK(md["mode"]))

    def test_directory_not_symlink(self) -> None:
        md = extract_metadata(self._dir)
        self.assertFalse(md["is_symlink"])
        self.assertTrue(stat.S_ISDIR(md["mode"]))

    @unittest.skipUnless(
        os.name == "posix",
        "symlinks are only meaningful on POSIX",
    )
    def test_symlink_is_symlink(self) -> None:
        target = os.path.join(self._dir, "target")
        open(target, "w").close()
        link = os.path.join(self._dir, "link")
        os.symlink(target, link)
        md = extract_metadata(link)
        self.assertTrue(md["is_symlink"])
        self.assertTrue(stat.S_ISLNK(md["mode"]))

    @unittest.skipUnless(
        os.name == "posix",
        "symlinks are only meaningful on POSIX",
    )
    def test_symlink_target_missing(self) -> None:
        # A dangling link is still stat-able via lstat; we must not raise.
        link = os.path.join(self._dir, "dangling")
        os.symlink(os.path.join(self._dir, "nonexistent"), link)
        md = extract_metadata(link)
        self.assertTrue(md["is_symlink"])

    @unittest.skipUnless(
        os.name == "posix",
        "symlinks are only meaningful on POSIX",
    )
    def test_symlink_size_is_link_size_not_target(self) -> None:
        target = os.path.join(self._dir, "target.txt")
        with open(target, "w") as fh:
            fh.write("x" * 4096)
        link = os.path.join(self._dir, "link")
        os.symlink(target, link)
        md = extract_metadata(link)
        # lstat reports the length of the link target *path*, not the size
        # of the file the link points to. Ensure we used lstat, not stat.
        self.assertNotEqual(md["size"], 4096)

    def test_nonexistent_path_raises_oserror(self) -> None:
        with self.assertRaises(OSError):
            extract_metadata(os.path.join(self._dir, "does_not_exist"))

    def test_path_bytes(self) -> None:
        p = os.path.join(self._dir, "a.txt")
        open(p, "w").close()
        md = extract_metadata(p.encode("utf-8"))
        self.assertEqual(md["size"], 0)

    def test_pathlike(self) -> None:
        p = os.path.join(self._dir, "a.txt")
        open(p, "w").close()
        md = extract_metadata(os.PathLike and __import__("pathlib").Path(p))
        self.assertEqual(md["size"], 0)

    def test_values_match_os_stat(self) -> None:
        p = os.path.join(self._dir, "a.txt")
        with open(p, "w") as fh:
            fh.write("abc")
        md = extract_metadata(p)
        info = os.stat(p, follow_symlinks=False)
        self.assertEqual(md["size"], info.st_size)
        self.assertEqual(md["mtime"], info.st_mtime)
        self.assertEqual(md["ctime"], info.st_ctime)
        self.assertEqual(md["mode"], info.st_mode)
        self.assertEqual(md["uid"], info.st_uid)
        self.assertEqual(md["gid"], info.st_gid)


if __name__ == "__main__":
    unittest.main()
