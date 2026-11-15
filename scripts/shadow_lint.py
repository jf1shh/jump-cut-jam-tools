#!/usr/bin/env python3
"""shadow_lint: flag locals/params named like inherited UE members (MSVC C4458).

Linux clang accepts `const X* Slot = ...` inside a UWidget method; MSVC (Windows
packaging) rejects it with C4458 because it hides UWidget::Slot. This is a cheap
textual check so we find it on Linux before a 78-minute Windows package fails.

Usage: shadow_lint.py [--self-test] [PATH ...]   (default: ~/Projects/megajam-game/Source)
Exit 1 if any hit.
"""
import re
import sys
from pathlib import Path

# Common inherited members of UWidget/UUserWidget/AActor/UActorComponent/APawn/etc.
RISKY = [
    "Slot", "Visibility", "Cursor", "ToolTipText", "RenderOpacity", "RenderTransform",
    "bIsEnabled", "Tags", "Instigator", "RootComponent", "Padding", "ColorAndOpacity",
]
NAMES = "|".join(sorted(set(RISKY)))
# `<type tokens> [*&] Name` followed by = ; ( , ) or : (range-for), not a member access.
DECL = re.compile(
    r"(?<![\w.>:])(?:const\s+)?[A-Za-z_][\w:<>,\s]*?[\s*&]+(?P<n>%s)\s*(?:=|;|,|\)|\{|:(?!:))" % NAMES
)
SKIP_START = re.compile(r"^\s*(return|else|case|delete|new|throw|goto|using|typedef|#)\b")


def scan_text(text, label="<text>"):
    hits = []
    for i, line in enumerate(text.splitlines(), 1):
        code = line.split("//")[0]
        # free function signatures (col 0, no Class::) cannot hide a member
        if code[:1] not in (" ", "\t", "") and "::" not in code.split("(")[0]:
            continue
        if "shadow-ok" in line or (label.endswith("JCTrace.cpp") and "FString Tags;" in code):
            continue  # JCTrace is a plain struct, not an AActor
        if not code.strip() or SKIP_START.match(code):
            continue
        # only lines with a type before the name; need whitespace/*/& before the identifier
        m = DECL.search(code)
        if not m:
            continue
        # reject assignments like `Foo->Slot = x` (handled by lookbehind) and `x = Slot;`
        pre = code[: m.start("n")]
        if "=" in pre and not re.search(r"[(,]\s*[^=]*$", pre):
            continue
        # require a type-looking token right before the name
        if not re.search(r"[\w>]\s*[*&]*\s*$", pre):
            continue
        hits.append((label, i, line.strip(), m.group("n")))
    return hits


def scan_paths(paths):
    hits = []
    for p in paths:
        p = Path(p).expanduser()
        files = [p] if p.is_file() else sorted(p.rglob("*.cpp"))
        for f in files:
            if f.suffix != ".cpp":
                continue
            hits += scan_text(f.read_text(errors="replace"), str(f))
    return hits


def self_test():
    bad = [
        "\tif (const TSoftObjectPtr<USoundBase>* Slot = Tun->SoundSlots.Find(X))",
        "\tUCanvasPanelSlot* Slot = Cast<UCanvasPanelSlot>(W->Slot);",
        "void UFoo::Bar(float Visibility)",
        "\tFMargin Padding = FMargin(1);",
    ]
    good = [
        "\tif (const TSoftObjectPtr<USoundBase>* StingerSlot = Tun->SoundSlots.Find(X))",
        "W->Slot = nullptr;",
        "return Slot;",
        "X = Slot;",
        "// UCanvasPanelSlot* Slot = nullptr;",
        "Foo(Slot);",
    ]
    ok = True
    for s in bad:
        if not scan_text(s):
            print("MISSED:", s)
            ok = False
    for s in good:
        if scan_text(s):
            print("FALSE POSITIVE:", s)
            ok = False
    print("self-test", "PASS" if ok else "FAIL")
    return 0 if ok else 1


def main(argv):
    if "--self-test" in argv:
        return self_test()
    paths = [a for a in argv if not a.startswith("-")] or ["~/Projects/megajam-game/Source"]
    hits = scan_paths(paths)
    for f, n, line, name in hits:
        print(f"{f}:{n}: local/param '{name}' may hide an inherited member (MSVC C4458): {line}")
    print(f"shadow_lint: {len(hits)} hit(s)")
    return 1 if hits else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
