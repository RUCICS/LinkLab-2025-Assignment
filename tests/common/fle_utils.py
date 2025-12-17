#!/usr/bin/env python3
import re

_DYN_RELOC_PATTERN = re.compile(
    r"^❓:\s*\.(dynrel|dynabs64|dynabs32)\(\s*([\w.$@]+)\s*([+-])\s*([0-9A-Fa-fxX]+)\s*\)$"
)

_TYPE_MAP = {
    "dynabs32": 0,  # R_X86_64_32
    "dynrel": 1,    # R_X86_64_PC32
    "dynabs64": 2,  # R_X86_64_64
}


def _parse_addend(value: str) -> int:
    value = value.strip()
    if value.lower().startswith("0x"):
        value = value[2:]
    try:
        return int(value, 16)
    except ValueError:
        return int(value, 10)


def extract_dynamic_relocs(fle_json):
    """Extract dynamic relocations that are embedded inside sections."""
    relocs = []
    for section_name, lines in fle_json.items():
        if not isinstance(lines, list):
            continue
        for line in lines:
            if not isinstance(line, str):
                continue
            match = _DYN_RELOC_PATTERN.match(line.strip())
            if not match:
                continue
            reloc_type = match.group(1)
            symbol = match.group(2)
            sign = match.group(3)
            literal = match.group(4)

            addend = _parse_addend(literal)
            if sign == "-":
                addend = -addend

            relocs.append({
                "section": section_name,
                "symbol": symbol,
                "addend": addend,
                "type": _TYPE_MAP[reloc_type],
            })
    return relocs
