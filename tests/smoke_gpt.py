"""Manual smoke test (spends ChatGPT quota, ~5 min): one plain grey cube through the GPT provider.

Usage: python3 tests/smoke_gpt.py <abs-out.png>   (not part of the unit-test run)
"""
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "scripts"))
import providers as P  # noqa: E402

out = sys.argv[1]
r = P.generate_concept("gpt", "a plain matte grey cube on a white background, studio lighting",
                       out, P.default_providers())
print(r["provider"], f"{r['seconds']:.0f}s", os.path.getsize(out), "bytes")
