"""Minimal Source 2 VPK (pak01) reader for Dota 2."""
from __future__ import annotations

import os
import struct
import zlib


def _cstr(buf: bytes, pos: int) -> tuple[str, int]:
    end = buf.index(b"\x00", pos)
    return buf[pos:end].decode("utf-8", "replace"), end + 1


class VPK:
    def __init__(self, dir_vpk: str):
        self.dir_vpk = dir_vpk
        self.base = os.path.dirname(dir_vpk)
        with open(dir_vpk, "rb") as f:
            data = f.read()
        sig, version, tree_size = struct.unpack_from("<III", data, 0)
        if sig != 0x55AA1234:
            raise ValueError(f"bad vpk signature {sig:#x} in {dir_vpk}")
        self.version = version
        self.header_size = 28 if version == 2 else 12
        self.data_start = self.header_size + tree_size
        tree = data[self.header_size : self.data_start]
        entries: dict[str, tuple[int, int, int, int]] = {}
        pos = 0
        while True:
            ext, pos = _cstr(tree, pos)
            if ext == "":
                break
            while True:
                path, pos = _cstr(tree, pos)
                if path == "":
                    break
                while True:
                    name, pos = _cstr(tree, pos)
                    if name == "":
                        break
                    _crc, _pre, _arch, _off, _len, _term = struct.unpack_from("<IHHIIH", tree, pos)
                    pos += 18
                    if _term != 0xFFFF:
                        raise ValueError(f"bad terminator at {path}/{name}.{ext}")
                    if _pre:
                        pos += _pre
                    entries[f"{path}/{name}.{ext}"] = (_arch, _off, _len, _crc)
        self.entries = entries
        self._handles: dict[int, object] = {}

    def _archive_path(self, idx: int) -> str:
        if idx == 0x7FFF:
            return self.dir_vpk
        return os.path.join(self.base, f"pak01_{idx:03d}.vpk")

    def read(self, path: str) -> tuple[bytes, bool]:
        """Return (data, crc_ok) for an entry path."""
        arch, off, length, crc = self.entries[path]
        h = self._handles.get(arch)
        if h is None:
            h = self._handles[arch] = open(self._archive_path(arch), "rb")
        h.seek(off if arch != 0x7FFF else self.data_start + off)
        data = h.read(length)
        return data, (zlib.crc32(data) & 0xFFFFFFFF) == crc

    def close(self) -> None:
        for h in self._handles.values():
            h.close()
        self._handles.clear()
