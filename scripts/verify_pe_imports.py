"""
Verify PE imports of built _tkblend*.pyd on Windows to ensure direct link to Tk DLL is active.
"""

import glob
import struct
import sys


def main() -> None:
    pyd_files = glob.glob("tkblend/_tkblend*.pyd")
    if not pyd_files:
        print("Error: Could not find _tkblend*.pyd in tkblend/", file=sys.stderr)
        sys.exit(1)

    pyd_path = pyd_files[0]
    print(f"Inspecting PE imports for: {pyd_path}")

    with open(pyd_path, "rb") as f:
        data = f.read()

    e_lfanew = struct.unpack_from("<I", data, 0x3C)[0]
    magic = struct.unpack_from("<H", data, e_lfanew + 24)[0]

    if magic == 0x20B:
        import_rva, import_size = struct.unpack_from("<II", data, e_lfanew + 24 + 120)
    else:
        import_rva, import_size = struct.unpack_from("<II", data, e_lfanew + 24 + 104)

    num_sections = struct.unpack_from("<H", data, e_lfanew + 6)[0]
    opt_header_size = struct.unpack_from("<H", data, e_lfanew + 20)[0]
    section_offset = e_lfanew + 24 + opt_header_size

    def rva_to_offset(rva: int):
        for i in range(num_sections):
            sec = section_offset + i * 40
            sec_vsize, sec_va, sec_raw_size, sec_raw_offset = struct.unpack_from(
                "<IIII", data, sec + 8
            )
            if sec_va <= rva < sec_va + max(sec_vsize, sec_raw_size):
                return sec_raw_offset + (rva - sec_va)
        return None

    imports = []
    curr = rva_to_offset(import_rva)
    while curr is not None and curr + 20 <= len(data):
        orig_first_thunk, ts, fchain, name_rva, first_thunk = struct.unpack_from(
            "<IIIII", data, curr
        )
        if name_rva == 0:
            break
        name_offset = rva_to_offset(name_rva)
        if name_offset:
            name = data[name_offset : data.find(b"\x00", name_offset)].decode(
                "ascii", errors="ignore"
            )
            imports.append(name.lower())
        curr += 20

    print(f"Imported DLLs: {imports}")
    assert any(
        "tk86" in imp or "tk" in imp for imp in imports
    ), f"Expected direct link to Tk DLL in PE imports, found: {imports}"
    print("Verified: Direct link to Tk is active in PE imports.")


if __name__ == "__main__":
    main()
