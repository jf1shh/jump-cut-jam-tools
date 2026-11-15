# Conventions (re-export)

> Canonical source: `CLAUDE.md` (naming prefixes, Blueprint vs C++) and `AGENTS.md` (project facts and agent rules). Edit those, not this file.

## Quick reference

- Unreal content prefixes: `BP_` Blueprint, `WBP_` widget, `M_` material, `MI_` instance, `SM_` static mesh, `SK_` skeletal mesh, `T_` texture (`_D`, `_N`, `_ORM`), `A_` animation, `S_` sound, `L_` level, `NS_` Niagara.
- Blueprint first; C++ only when `CLAUDE.md` says so.
- Docs: every new document lives in `stages/NN_*/references` or `output/`, or in `_config/`; add its row to `_config/CANON.md`. No new top-level doc folders.
- Stage files: `stages/NN_name/CONTEXT.md` is the contract; produced files go in that stage's `output/`.
- Rule numbers (Official Rules) are cited as "Rule 7(h)" and so on; digest in `RULES.md`.
