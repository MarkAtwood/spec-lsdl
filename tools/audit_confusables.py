#!/usr/bin/env python3
"""
Audit LSDL coverage against Unicode confusables.txt (UTS #39).

Filters to Latin/Greek/Cyrillic script confusables and checks
which pairs are defined in our LSDL library.
"""

import re
import sys
from pathlib import Path
from collections import defaultdict

# Script ranges we care about
SCRIPT_RANGES = {
    'Latin': [
        (0x0041, 0x007A),  # Basic Latin
        (0x00C0, 0x00FF),  # Latin-1 Supplement
        (0x0100, 0x017F),  # Latin Extended-A
        (0x0180, 0x024F),  # Latin Extended-B
        (0x1E00, 0x1EFF),  # Latin Extended Additional
        (0x2C60, 0x2C7F),  # Latin Extended-C
        (0xA720, 0xA7FF),  # Latin Extended-D
        (0xAB30, 0xAB6F),  # Latin Extended-E
    ],
    'Greek': [
        (0x0370, 0x03FF),  # Greek and Coptic
        (0x1F00, 0x1FFF),  # Greek Extended
    ],
    'Cyrillic': [
        (0x0400, 0x04FF),  # Cyrillic
        (0x0500, 0x052F),  # Cyrillic Supplement
        (0x2DE0, 0x2DFF),  # Cyrillic Extended-A
        (0xA640, 0xA69F),  # Cyrillic Extended-B
        (0x1C80, 0x1C8F),  # Cyrillic Extended-C
    ],
}

def get_script(cp):
    """Return script name for a codepoint, or None if not in our scope."""
    for script, ranges in SCRIPT_RANGES.items():
        for start, end in ranges:
            if start <= cp <= end:
                return script
    return None

def parse_confusables(path):
    """Parse confusables.txt and return list of (source_cp, target_cps, type)."""
    confusables = []
    with open(path, 'r', encoding='utf-8') as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith('#'):
                continue
            # Format: source ; target(s) ; MA/SL # comment
            match = re.match(r'([0-9A-F]+)\s*;\s*([0-9A-F ]+)\s*;\s*(MA|SL)', line)
            if match:
                source = int(match.group(1), 16)
                targets = [int(t, 16) for t in match.group(2).split()]
                conf_type = match.group(3)
                confusables.append((source, targets, conf_type))
    return confusables

def get_lsdl_chars(lib_dir):
    """Extract all defined characters from LSDL files."""
    chars = set()
    char_pattern = re.compile(r"^([^\s#@=]+)\s+[A-Z]", re.MULTILINE)
    cp_pattern = re.compile(r"cp:U\+([0-9A-Fa-f]+)")

    for lsdl_file in Path(lib_dir).glob("*.lsdl"):
        content = lsdl_file.read_text(encoding='utf-8')
        for line in content.split('\n'):
            line = line.strip()
            if not line or line.startswith('#') or line.startswith('@'):
                continue
            # Look for cp: tag
            cp_match = cp_pattern.search(line)
            if cp_match:
                chars.add(int(cp_match.group(1), 16))
            # Also try to get the literal character
            if line and not line[0].isspace():
                first_char = line[0]
                if ord(first_char) > 127:  # Non-ASCII
                    chars.add(ord(first_char))
    return chars

def main():
    tools_dir = Path(__file__).parent
    lib_dir = tools_dir.parent / "lib"
    confusables_path = tools_dir / "confusables.txt"

    if not confusables_path.exists():
        print(f"Error: {confusables_path} not found", file=sys.stderr)
        sys.exit(1)

    print("=" * 70)
    print("UNICODE CONFUSABLES AUDIT (UTS #39)")
    print("=" * 70)
    print()

    # Parse confusables
    all_confusables = parse_confusables(confusables_path)
    print(f"Total confusables in Unicode: {len(all_confusables)}")

    # Filter to Latin/Greek/Cyrillic pairs
    lgs_confusables = []
    for source, targets, conf_type in all_confusables:
        source_script = get_script(source)
        if not source_script:
            continue
        # Check if any target is in our scripts
        for target in targets:
            target_script = get_script(target)
            if target_script and target_script != source_script:
                lgs_confusables.append((source, target, source_script, target_script))

    print(f"Latin/Greek/Cyrillic cross-script confusables: {len(lgs_confusables)}")
    print()

    # Get LSDL coverage
    lsdl_chars = get_lsdl_chars(lib_dir)
    print(f"Characters defined in LSDL: {len(lsdl_chars)}")
    print()

    # Analyze coverage
    both_defined = []
    source_only = []
    target_only = []
    neither = []

    for source, target, src_script, tgt_script in lgs_confusables:
        src_in = source in lsdl_chars
        tgt_in = target in lsdl_chars
        entry = (source, target, src_script, tgt_script)
        if src_in and tgt_in:
            both_defined.append(entry)
        elif src_in:
            source_only.append(entry)
        elif tgt_in:
            target_only.append(entry)
        else:
            neither.append(entry)

    print("-" * 70)
    print("CONFUSABLE PAIR COVERAGE")
    print("-" * 70)
    print(f"Both characters defined:    {len(both_defined):4d} (can compare geometry)")
    print(f"Source only defined:        {len(source_only):4d}")
    print(f"Target only defined:        {len(target_only):4d}")
    print(f"Neither defined:            {len(neither):4d}")
    print()

    # Group by script pair
    print("-" * 70)
    print("BY SCRIPT PAIR (both defined)")
    print("-" * 70)
    script_pairs = defaultdict(list)
    for source, target, src_script, tgt_script in both_defined:
        key = f"{src_script}-{tgt_script}"
        script_pairs[key].append((source, target))

    for pair, entries in sorted(script_pairs.items()):
        print(f"{pair}: {len(entries)} pairs")
    print()

    # Show sample confusables
    print("-" * 70)
    print("SAMPLE CONFUSABLE PAIRS (both defined in LSDL)")
    print("-" * 70)
    print(f"{'Source':8} {'Target':8} {'Scripts':20} Characters")
    print("-" * 70)
    for source, target, src_script, tgt_script in both_defined[:30]:
        src_char = chr(source) if source < 0x10000 else f"U+{source:04X}"
        tgt_char = chr(target) if target < 0x10000 else f"U+{target:04X}"
        print(f"U+{source:04X}   U+{target:04X}   {src_script:8}->{tgt_script:8}  {src_char} ↔ {tgt_char}")

    if len(both_defined) > 30:
        print(f"... and {len(both_defined) - 30} more")
    print()

    # Summary
    print("=" * 70)
    print("SUMMARY")
    print("=" * 70)
    coverage = len(both_defined) / len(lgs_confusables) * 100 if lgs_confusables else 0
    print(f"Confusable pair coverage: {len(both_defined)}/{len(lgs_confusables)} ({coverage:.1f}%)")
    print()
    print("These pairs can be tested for geometric equivalence in LSDL.")

if __name__ == "__main__":
    main()
