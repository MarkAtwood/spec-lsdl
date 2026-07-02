#!/usr/bin/env python3
"""
Generate homoglyph-map.json from Unicode confusables.txt (UTS #39).

Groups confusable characters into sets where all members map to the same
canonical target, filtered to Latin/Greek/Cyrillic scripts.
"""

import json
import re
from pathlib import Path
from collections import defaultdict

# Script ranges
SCRIPT_RANGES = {
    'Latin': [
        (0x0041, 0x007A), (0x00C0, 0x00FF), (0x0100, 0x017F), (0x0180, 0x024F),
        (0x1E00, 0x1EFF), (0x2C60, 0x2C7F), (0xA720, 0xA7FF), (0xAB30, 0xAB6F),
    ],
    'Greek': [(0x0370, 0x03FF), (0x1F00, 0x1FFF)],
    'Cyrillic': [
        (0x0400, 0x04FF), (0x0500, 0x052F), (0x2DE0, 0x2DFF),
        (0xA640, 0xA69F), (0x1C80, 0x1C8F),
    ],
}

def get_script(cp):
    for script, ranges in SCRIPT_RANGES.items():
        for start, end in ranges:
            if start <= cp <= end:
                return script
    return None

def parse_confusables(path):
    """Parse confusables.txt into mapping of source -> target skeleton."""
    mappings = {}
    with open(path, 'r', encoding='utf-8') as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith('#'):
                continue
            match = re.match(r'([0-9A-F]+)\s*;\s*([0-9A-F ]+)\s*;', line)
            if match:
                source = int(match.group(1), 16)
                # Target is a sequence of codepoints (skeleton)
                target = tuple(int(t, 16) for t in match.group(2).split())
                mappings[source] = target
    return mappings

def main():
    tools_dir = Path(__file__).parent
    confusables_path = tools_dir / "confusables.txt"
    output_path = tools_dir / "homoglyph-map.json"

    mappings = parse_confusables(confusables_path)

    # Group by target skeleton, filter to our scripts
    groups = defaultdict(set)
    for source, target in mappings.items():
        script = get_script(source)
        if script:
            # Use target as key, include source in group
            groups[target].add(source)
            # Also add target chars if in our scripts
            for t in target:
                if get_script(t):
                    groups[target].add(t)

    # Filter to groups with cross-script confusables
    cross_script_groups = []
    for target, members in groups.items():
        scripts = set()
        for cp in members:
            s = get_script(cp)
            if s:
                scripts.add(s)
        if len(scripts) > 1:  # Cross-script confusables
            cross_script_groups.append({
                "target": "".join(chr(c) for c in target if c < 0x10000),
                "target_codepoints": [f"U+{c:04X}" for c in target],
                "members": sorted([
                    {"char": chr(cp) if cp < 0x10000 else f"U+{cp:04X}",
                     "codepoint": f"U+{cp:04X}",
                     "script": get_script(cp)}
                    for cp in members
                ], key=lambda x: x["codepoint"]),
                "scripts": sorted(scripts)
            })

    # Sort by number of members (most interesting first)
    cross_script_groups.sort(key=lambda g: -len(g["members"]))

    result = {
        "source": "Unicode confusables.txt (UTS #39)",
        "version": "17.0.0",
        "description": "Cross-script confusable character groups for Latin/Greek/Cyrillic",
        "total_groups": len(cross_script_groups),
        "groups": cross_script_groups
    }

    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(result, f, indent=2, ensure_ascii=False)

    print(f"Generated {output_path}")
    print(f"Total cross-script confusable groups: {len(cross_script_groups)}")

    # Print top groups
    print("\nTop confusable groups:")
    for g in cross_script_groups[:10]:
        chars = " ".join(m["char"] for m in g["members"])
        print(f"  {chars} ({', '.join(g['scripts'])})")

if __name__ == "__main__":
    main()
