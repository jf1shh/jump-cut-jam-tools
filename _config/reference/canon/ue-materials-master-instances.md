---
tier: epic
source: https://dev.epicgames.com/documentation/en-us/unreal-engine/instanced-materials-in-unreal-engine
updated: 2026-11-06
---

# Master materials and material instances

## Tip: one master material, many instances
- **Why:** parameters in the master (colour, roughness, texture inputs) become sliders in each `MI_` instance. Changes
  are instant and cheap, and many objects share one compiled shader.
- **How to check:** right-click the master > Create Material Instance, edit parameters with no recompile wait.

## Tip: name every input a parameter
- **Why:** unnamed constants cannot be changed in an instance.
- **How to check:** the Details panel of the instance lists all the parameters you expect.

## Tip: static switches multiply shaders
- **Why:** each static switch combination is a separate compile and permutation. Keep them few.
- **How to check:** watch the "compiling shaders" count after adding a switch.

## Tip: texture packing
- **Why:** we use `T_..._ORM` (occlusion, roughness, metallic in one texture's RGB) to cut texture samples; naming is in `CLAUDE.md`.
- **How to check:** set the texture as Masks (no sRGB) so the data channels read correctly.

## Tip: a vertex-colour look is a legitimate shortcut
- **Why:** `Vertex Color` node plus a Lerp of two colour parameters needs no texture (see `ai3d-postprocess`).
- **How to check:** the mesh has a colour attribute and the material shows it.

## Tip: imported glTF materials are instances of a plugin master
- **Why:** see `jam-import-and-materials` for the Nanite flag trap.
- **How to check:** open the instance and read its parent chain.

## Tip: our convention is one master material per hero look (owner decision, not run by us)
- **Why:** consistent bake and retopo, and fewer shader permutations (see `CLAUDE.md` naming).
- **How to check:** hero meshes use `MI_` instances of one `M_` parent.
