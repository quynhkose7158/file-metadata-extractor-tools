# file-metadata-extractor-tools

Returns size, mtime, ctime, mode, owner uid, and gid for a path in a single `os.stat` call wrapped as a dict.

```python
from file_metadata_extractor_tools import extract_metadata

md = extract_metadata("/etc/hosts")
print(md["size"], md["uid"], md["is_symlink"])
```

## Why

One stat call per path is the point. Every extra `os.stat` or `os.path.getsize` is another round-trip to the filesystem; if you're walking a tree of tens of thousands of files the constant factor matters. This wrapper makes the single-call contract explicit in the type signature so callers don't accidentally re-stat.

The trade-off: we use `follow_symlinks=False` (i.e. `lstat`) unconditionally. For symlinks the reported size is the length of the link path, not the target's size, and `is_symlink` is included so callers can tell the cases apart. If you want the target's metadata, `os.stat` it yourself — this library deliberately does not follow links.

Errors are not caught. A missing path raises `OSError` through `extract_metadata`; soft-failure wrappers belong at the call site where the caller knows whether an absent file is expected.

## Edge cases

- **Broken symlinks**: `lstat` succeeds where `stat` would raise; `is_symlink` is `True` and `size` is the path length.
- **Bytes and `PathLike` inputs**: both accepted, matching `os.stat`.
- **`ctime` semantics**: on POSIX this is inode-change time, on Windows it is creation time. The key is the same; the meaning is OS-dependent and not normalised here.

## Performance

The window keeps a bounded buffer, so `push` is constant time and memory does not
grow with the length of the stream. `peak` and `trough` are linear in the window
size, which is the trade that keeps `push` cheap.

