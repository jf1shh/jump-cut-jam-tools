---
tier: epic
source: https://dev.epicgames.com/documentation/en-us/unreal-engine/blueprints-visual-scripting-in-unreal-engine
updated: 2026-11-06
---

# Blueprint basics for a jam

## Tip: know the four gameplay classes
- **Why:** Game Mode holds rules and defaults (which Pawn, which HUD). Pawn or Character is the thing you control.
  Player Controller handles input and possession. Game State and Player State hold shared and per-player data.
- **How to check:** World Settings > Game Mode Override; the Pawn must be possessed (`DefaultPawnClass` or Auto Possess).

## Tip: pick a Pawn with movement built in
- **Why:** a bare `Pawn` has no movement component, so `AddMovementInput` does nothing (our mock jam 5 bug).
  `Character` has CharacterMovement; `DefaultPawn` has FloatingPawnMovement.
- **How to check:** the pawn moves in Play-In-Editor.

## Tip: choose how Blueprints talk
- **Why:** direct references are simple; Blueprint Interfaces avoid hard links; Event Dispatchers let one actor
  broadcast; Cast checks a class. Avoid casting every frame.
- **How to check:** Reference Viewer shows hard dependencies.

## Tip: Construction Script versus BeginPlay
- **Why:** Construction Script runs in the editor when you change an actor (good for layout); BeginPlay runs at game start.
- **How to check:** add a `Print String` in each and watch when it fires.

## Tip: data in tables, not in graphs
- **Why:** Data Tables, Data Assets, enums and structs keep tuning numbers out of spaghetti and easy to edit.
- **How to check:** change one row and the behaviour changes with no graph edits.

## Tip: Enhanced Input for controls
- **Why:** Input Actions plus a Mapping Context rebind cleanly for keyboard and gamepad.
- **How to check:** `showdebug enhancedinput`.

## Tip: compile, save, keep graphs small
- **Why:** big graphs are slow to build over MCP and review; move heavy logic to C++ (see `CLAUDE.md`).
- **How to check:** a graph that needs scrolling is a candidate for functions, macros or C++.

## Tip: our convention is C++ for logic-heavy systems (owner decision from the Epic MCP webinar, not run by us)
- **Why:** big Blueprint graphs are slow to build over MCP and hard to review (see `CLAUDE.md` in this repo).
- **How to check:** many branches or loops? Write C++ with thin `UFUNCTION` hooks.
