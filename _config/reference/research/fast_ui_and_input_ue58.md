# Menus, HUD and input in an hour in UE 5.8: Python generation, menu flow, gamepad focus, Enhanced Input, template licensing

Research date: 2026-10-29. Method: 14 searches and 24 page fetches against Epic's 5.8 Python API reference,
5.8 release notes, Common UI docs, Epic forum threads and a few third-party guides, after reading RULES.md, the
two earlier research notes, the mechanic toolkit, mock-jam-findings-4 (Tooling gotchas) and the mock jam 5
handoff. Nothing here was run in the editor. Every Python name below was checked against the 5.8 Python API
pages unless marked **[unconfirmed]**. The Python pages carry the banner "Unreal Python 5.8 (Experimental)".

**Status: research notes only.** No UI, Blueprint or level is built or implied by this note. Scripts and tools
may be prepared before the window; gameplay, levels and art may not (Rule 7(h)).

**Takeaway.** Python can build the widget tree of a menu, HUD or end screen in one script. 5.8 documents
`unreal.EditorUtilityLibrary.add_source_widget(widget_blueprint, widget_class, widget_name, widget_parent_name)`,
so the node-by-node MCP work is not needed. Python cannot wire the logic: the pages for `WidgetTree`,
`WidgetBlueprint` and `Button` list no way to add graph nodes or bind `on_clicked`. The fastest reliable route
is one Python "UI kit" script that creates the Widget Blueprints and sets text, colours and anchors, plus a
very small, fixed set of Blueprint graphs for button clicks, game-over and restart, written once and reused.
Use plain UMG with explicit focus for a jam. Common UI is a real setup cost (viewport client, two data tables,
controller data assets). Add it only if the game needs an on-screen button-prompt bar or a back stack. Epic
template content is allowed but unscored and must be listed. The 2026 rules text is the only authority on how.

## 1. Generating UMG Widget Blueprints from editor Python (question a)

| Finding | Confidence | Basis | Source |
|---|---|---|---|
| `unreal.EditorUtilityLibrary.add_source_widget(widget_blueprint, widget_class, widget_name, widget_parent_name) -> Widget` exists in 5.8. It "creates a new widget and adds it to the Widget Blueprint's widget tree". The parent must be a Panel Widget, or empty if the tree is empty, in which case the new widget becomes the RootWidget. | High that it exists; medium that it behaves as described | Epic doc | [EditorUtilityLibrary Python](https://dev.epicgames.com/documentation/en-us/unreal-engine/python-api/class/EditorUtilityLibrary), [Blueprint node page](https://dev.epicgames.com/documentation/unreal-engine/BlueprintAPI/EditorScripting/WidgetBlueprint/AddSourceWidget) |
| The same class has `find_source_widget_by_name(widget_blueprint, widget_name) -> Widget` and `convert_to_editor_utility_widget(widget_bp)`. | High | Epic doc | EditorUtilityLibrary Python (above) |
| The Blueprint-node page for Add Source Widget lists only three inputs (no parent name). The Python page lists four. Which engine version added the parent argument is not stated. | Medium | Epic doc | Both pages above |
| `unreal.WidgetTree` has no documented methods or properties in 5.8, only a constructor. `unreal.WidgetBlueprint` documents no `widget_tree` property and no methods. Do not try to construct widgets and attach them to a tree yourself. A March 2025 forum post tried exactly that (new `Button`, `CanvasPanel`, `EditorUtilityWidgetBlueprint`) and asked how to connect the canvas to the blueprint. It got no reply. | High on the doc gap; the forum post is a user report | Epic doc, user report | [WidgetTree](https://dev.epicgames.com/documentation/en-us/unreal-engine/python-api/class/WidgetTree), [WidgetBlueprint](http://dev.epicgames.com/documentation/en-us/unreal-engine/python-api/class/WidgetBlueprint), [forum](https://forums.unrealengine.com/t/umg-python/2372164) |
| Creating the asset: `unreal.WidgetBlueprintFactory` is a `Factory` with editor properties `parent_class`, `blueprint_type`, `edit_after_new`. A third-party MCP tool sets `parent_class = unreal.UserWidget`, then calls `AssetTools.create_asset(name, package_path, unreal.WidgetBlueprint, factory)` and saves. The `create_asset` signature is general Python editor scripting, not re-read for 5.8. | Medium | Epic doc, third-party | [WidgetBlueprintFactory](https://dev.epicgames.com/documentation/en-us/unreal-engine/python-api/class/WidgetBlueprintFactory), ChiR24 Unreal_mcp `ui.ts` (the exact URL later returned 404; seen in search snippet only) |
| `unreal.EditorAssetLibrary` has `duplicate_asset(src, dst)`, `rename_asset`, `save_asset(path, only_if_is_dirty=True)`, `save_loaded_asset`, `does_asset_exist`, `load_asset`. | High | Epic doc | [EditorAssetLibrary](https://dev.epicgames.com/documentation/en-us/unreal-engine/python-api/class/EditorAssetLibrary) |
| `unreal.TextBlock` exposes editor properties `text`, `font`, `color_and_opacity`, `justification`, plus `set_text()`. `set_text` wipes any text binding. `unreal.Button` has `is_focusable`, `background_color`, `is_enabled`. The Button page marks `is_focusable` read-only in one place and read-write in another, so test the setter. | High on names, medium on writability | Epic doc | [TextBlock](https://dev.epicgames.com/documentation/en-us/unreal-engine/python-api/class/TextBlock), [Button](https://dev.epicgames.com/documentation/en-us/unreal-engine/python-api/class/Button) |
| `Button.on_clicked` is listed only as a typed event property. No page shows binding a callable. A Python callback would not exist in a packaged game anyway, because editor Python does not ship. Click handling has to be a Blueprint graph (or C++). | High (inference from docs and Python's editor-only status) | Epic doc, inference | Button page above |
| Slot layout (anchors, padding, alignment) is set through the child's `slot` object (for example a canvas slot). The slot class names and setters were not checked this session. | Low | inference | none **[unconfirmed]** |
| Duplicating a template widget works only if a template exists. Rule 7(h) forbids pre-built game UI assets. Duplicating a widget made during the window (for example, HUD → pause menu) is fine. `duplicate_asset` then `find_source_widget_by_name(...).set_text(...)` is the cheap way to make the second and third screens. | Medium | Epic doc, inference | EditorAssetLibrary, EditorUtilityLibrary pages |
| Editor Utility Widgets (`EditorUtilityWidgetBlueprintFactory`, `convert_to_editor_utility_widget`) are editor tools only and do not ship. They are useful only as a button panel that launches the UI-kit script. | Medium | Epic doc, inference | [EUW factory](https://dev.epicgames.com/documentation/en-us/unreal-engine/python-api/class/EditorUtilityWidgetBlueprintFactory) |

What is and is not possible, in one line: **possible** = create the asset, add widgets in a tree, name them, set
their properties, save; **not possible or not documented** = construct a tree by hand, bind events, add graph
nodes, compile-and-read errors (compile may work through a Blueprint editor library; not checked).

## 2. Minimal menu → play → win/lose → restart flow (question b)

Pattern (all steps are standard Blueprint nodes; the order is inferred from Epic's pause-menu tutorial and forum advice):

1. **Boot map = menu map.** The `PlayerController` (or GameMode `BeginPlay`) creates `WBP_MainMenu`, `Add to Viewport`, then `Set Input Mode UI Only` with `In Widget to Focus` = the Play button, and `Set Show Mouse Cursor` = true. Do not pause the game in the menu map; a UI Only mode is enough.
2. **Play button.** `Remove from Parent` (self) first, then `Set Input Mode Game Only`, `Set Show Mouse Cursor` = false, then start gameplay (either spawn on the same map, or `Open Level`).
3. **Win/lose.** One function `EndGame(bWon)` on the GameMode: create `WBP_EndScreen`, set its text from `bWon`, `Add to Viewport`, `Set Input Mode UI Only` with focus on Restart, show cursor, `Set Game Paused` = true.
4. **Restart.** Before anything else: `Set Game Paused` = false, `Remove from Parent` the end screen, `Set Input Mode Game Only`, hide the cursor, **then** `Open Level` (current level name). The controller is recreated on level load, so the mode is reset anyway, but doing it explicitly is cheap.

| Finding | Confidence | Basis | Source |
|---|---|---|---|
| Epic's pause-menu tutorial removes the widget, then unpauses, then sets Game Only. | Medium (4.26 page) | Epic doc, older version | [Creating a Pause Menu (4.26)](https://docs.unrealengine.com/4.26/ko/InteractiveExperiences/UMG/HowTo/CreatePauseMenu) |
| Bug "input stuck after closing menu": Set Input Mode Game Only does not remove the widget, so a click re-focuses it and the mode flips to Game and UI. Fix: remove or hide the widget first, then Game Only, then Show Mouse Cursor = false. Confirmed by the poster on 2026-10-14. Poster said UE 5.3, so older than 5.8. | Medium | user report | [forum thread](https://forums.unrealengine.com/t/set-input-mode-to-game-only-not-working/2839895) |
| Camera only follows the mouse after a click: check Project Settings → Input → Default Viewport Mouse Capture Mode. | Low | user report | same thread, [bugnet.io](https://bugnet.io/blog/fix-unreal-userwidget-input-mode-not-cleared-on-remove) |
| Gamepad focus fails if (1) buttons are not focusable, (2) input mode is Game Only, (3) nothing has initial focus, (4) auto-navigation cannot resolve the layout. Delaying focus by one tick helps when it fails silently. | Medium | third-party | [bugnet.io](https://bugnet.io/blog/fix-unreal-umg-widget-focus-not-working-gamepad) |
| "Menu not shown" (our mock jam 5 bug) was not diagnosed in the handoff. The usual causes are: the widget was created but never added to the viewport, the class reference is empty or the `_C` class path is wrong, a `Collapsed`/`Hidden` visibility, a lower Z-order behind another widget, or the node ran on a pawn/actor in a map with no PlayerController. | Low | inference | search results (no single source) |
| Reported crashes on `Open Level` come from UE4-era threads. Reloading the current level by name has been the stable variant in those threads. A `RestartLevel` console command left the pawn uncontrollable in one thread. Prefer `Open Level`. | Low | user report, older versions | [UE answers threads](https://answers.unrealengine.com/questions/378838/view.html) |
| Input Actions have a `trigger_when_paused` property, so a Pause or Restart action can fire while paused. | High | Epic doc | [InputAction](http://dev.epicgames.com/documentation/en-us/unreal-engine/python-api/class/InputAction) |

Safest owner-visible rule: **each place that sets `UI Only` has a matching place that undoes it**, and the end
screen's Restart button is tested with the gamepad on the Legion Go S, not only with the mouse.

## 3. Gamepad navigation: plain UMG vs Common UI (question c)

| Finding | Confidence | Basis | Source |
|---|---|---|---|
| Plain UMG needs: focusable buttons, a UI-capable input mode, one explicit initial focus (`Set Input Mode UI Only` with the focus widget, or `Set Keyboard Focus`/`Set User Focus` after `Add to Viewport`), and explicit neighbours when the layout is irregular (Navigation panel, or `SetNavigationRuleExplicit`). For a 1-column menu of 2–4 buttons, default navigation normally works. | Medium | third-party | bugnet.io; [Epic forum: navigate UMG buttons](https://forums.unrealengine.com/t/navigate-umg-buttons-with-gamepad/426449) |
| `UserWidget` in 5.8 has `is_focusable`, `desired_focus_widget` with `set_desired_focus_widget(widget)`, focus-event properties and a `navigation` property. `set_focus`, `set_user_focus` and `get_desired_focus_target` are not on its Python page (they exist in C++/Blueprint; Python names not confirmed). | High on what is listed | Epic doc | [UserWidget](https://dev.epicgames.com/documentation/en-us/unreal-engine/python-api/class/UserWidget) |
| Mouse use can drop focus. Workaround seen in forums: remember the last input device and re-focus the first button only when nothing is focused. | Low | user report | search results |
| Common UI 5.8 setup per Epic: set Game Viewport Client Class to `CommonGameViewportClient`; create an Input Action Data Table (row struct `CommonInputActionDataBase`); create a Blueprint on `CommonUIInputData` holding Click and Back rows and assign it in Project Settings → Game → Common Input Settings → Input Data; create one `CommonInputBaseControllerData` Blueprint per input type/gamepad and add them under Platform Input, with the default gamepad name matching one of them; optional Common Style assets. | High | Epic doc | [Common UI quickstart (5.8)](https://dev.epicgames.com/documentation/en-us/unreal-engine/common-ui-quickstart-guide-for-unreal-engine) |
| That quickstart does not cover enabling the plugin, input config of activatable widgets or root-layout setup. Those steps need other pages. | High | Epic doc | same |
| Common UI uses a synthetic analog cursor: a gamepad Accept becomes a synthetic mouse click if no action binding claims it. Wrong viewport client class, or a custom action router, breaks it. | High | Epic doc | [Common UI input technical guide](https://dev.epicgames.com/documentation/unreal-engine/commonui-input-technical-guide-for-unreal-engine) |
| 5.8 unifies Enhanced Input and Common Input/UI ("removes the need for duplicate data assets") and adds an Input Debugger. Whether the data-table steps above are still required in 5.8 was **not** checked. The quickstart page is 5.8-titled and still describes them. The release-notes text was read only for the first 100,000 of 357,000 characters. | Medium | Epic doc | [5.8 release notes](https://dev.epicgames.com/documentation/en-us/unreal-engine/unreal-engine-5-8-release-notes) |
| Reported 5.7 problem: pressing all four shoulder inputs while moving the stick lets a user navigate off the buttons. The poster traced it to analog-cursor code compiled only in non-shipping builds. No fix or staff reply. | Low | user report | [forum thread](https://forums.unrealengine.com/t/common-ui-navigation-can-be-completely-broken-while-using-gamepad/2741169) |
| No standalone Epic "Common UI sample" was found. Lyra uses Common UI, but the Lyra doc page has no setup walkthrough and it is not a small copy-paste source. | Medium | Epic doc | [Lyra page](https://dev.epicgames.com/documentation/en-us/unreal-engine/lyra-sample-game-in-unreal-engine) |

**Verdict for a jam (inference):** plain UMG. Our UI is three screens with 1–3 buttons each. Common UI pays off
for a back stack, per-device button icons and a layered HUD/menu root. All of that costs more than the hour
we budget, and its Python-scripting story is unchecked (it needs C++-backed `CommonActivatableWidget` and
`CommonButtonBase` classes; creating those through Python was not checked). Revisit only if a theme needs
rebindable controls or icon prompts.

## 4. Enhanced Input from Python (question d)

| Finding | Confidence | Basis | Source |
|---|---|---|---|
| Assets are created through `unreal.InputAction_Factory` (editor property `input_action_class`) and `unreal.InputMappingContext_Factory`, passed to `AssetTools.create_asset`. No page shows a full working call. A search for `InputActionFactory` (no underscore) returned a 404; the names with underscore exist. | Medium | Epic doc | [InputAction_Factory](https://dev.epicgames.com/documentation/en-us/unreal-engine/python-api/class/InputAction_Factory), [InputMappingContext_Factory](https://dev.epicgames.com/documentation/en-us/unreal-engine/python-api/class/InputMappingContext_Factory) |
| `unreal.InputAction` editor properties include `value_type`, `triggers`, `modifiers`, `consume_input`, `trigger_when_paused`. The page marks `value_type` both read-only and read-write, so test the setter. | High on names | Epic doc | [InputAction](http://dev.epicgames.com/documentation/en-us/unreal-engine/python-api/class/InputAction) |
| `unreal.InputMappingContext.map_key(action, to_key) -> EnhancedActionKeyMapping`, plus `unmap_key`, `unmap_all_keys_from_action`, `unmap_all`. That is how to bind keyboard and gamepad keys to the same action. How to build an `unreal.Key` value (for example for Gamepad Face Button Bottom) was not confirmed. | High on `map_key`; none on key construction | Epic doc | [InputMappingContext](https://dev.epicgames.com/documentation/en-us/unreal-engine/python-api/class/InputMappingContext) |
| Triggers and modifiers (for example Negate, Swizzle for WASD to a 2D axis) are objects set through the `modifiers` array. Class names and constructors were not checked. | Low | inference | none **[unconfirmed]** |
| Adding the context at runtime: `EnhancedInputLocalPlayerSubsystem.add_mapping_context(mapping_context, priority, options)` exists in the Python docs, but the page does not say it is callable in a packaged game. In a shipped game, do it in Blueprint (`Get Enhanced Input Local Player Subsystem` → `Add Mapping Context`) on `BeginPlay`. | Medium | Epic doc, inference | [EnhancedInputLocalPlayerSubsystem](https://dev.epicgames.com/documentation/en-us/unreal-engine/python-api/class/EnhancedInputLocalPlayerSubsystem) |
| A no-Blueprint alternative: `UEnhancedInputDeveloperSettings` has `DefaultMappingContexts` (array of `FDefaultContextSetting`), applied by default to the local-player subsystem. It is saved to `DefaultInput.ini` (class is `Config=Input, defaultconfig`, shown in the editor as "Enhanced Input"). A script could set it by Python settings access **[unconfirmed]** or by editing the config file. | Medium | Epic doc | [UEnhancedInputDeveloperSettings](https://dev.epicgames.com/documentation/unreal-engine/API/Plugins/EnhancedInput/UEnhancedInputDeveloperSettings) |
| Epic's variant templates already ship Enhanced Input with gamepad mappings (from the earlier note). Adding the mapping context by default setting removes the `BeginPlay` node for new characters. | Medium | Epic doc | [ue_fast_build_assets_shipping.md](ue_fast_build_assets_shipping.md) |

## 5. Epic templates and samples under the sourced-asset rule (question e)

What the rules say (RULES.md, already settled): sourced assets "must be licensed and listed, and will not be
reviewed or scored" (Rule 15(c)); AI-generated content is not a sourced asset; gameplay, levels and art must
be made during the window (Rule 7(h)); gameplay must exceed Epic's starter templates (Rule 7(d), (e)).

| Item | Use it? | Basis | Notes and source |
|---|---|---|---|
| Starter Content | Yes, declared | Epic doc | The EULA search snippet treats Starter Content as "Licensed Technology", and a product is royalty-free if it has no engine code and no Starter Content "in source format". The EULA page itself returned 403 to the fetch tool, so the exact wording is unread. [EULA](https://www.unrealengine.com/en-US/eula) |
| Third Person / Top Down / Variant templates (Mannequin, template blueprints, Enhanced Input assets) | Yes, declared; do not count as original | Epic doc, inference | Variants are in [ue_fast_build_assets_shipping.md](ue_fast_build_assets_shipping.md). Gameplay must go beyond them (Rule 7(d), (e)). |
| Game Animation Sample | Yes, declared, heavy | Epic doc | The page says its animation assets "you can use in your own project", with migrate/export steps. No licence text on the page. [GASP](https://dev.epicgames.com/documentation/en-us/unreal-engine/game-animation-sample-project-in-unreal-engine) |
| Lyra | Avoid for a one-hour UI | Epic doc, inference | Page says its UI features are modular. No licence statement on the page. Big migration, huge dependency tree. [Lyra](https://dev.epicgames.com/documentation/en-us/unreal-engine/lyra-sample-game-in-unreal-engine) |
| Fab / Marketplace assets | Not covered by the EULA; each has its own licence | Epic doc | EULA snippet says Fab assets "are not Licensed Technology". Check each listing's licence. |

**How to declare (proposal, inference).** The submission needs the "sourced (non-original) assets noted"
field (RULES.md, Rule 1(d), 15(c)). The 2026 forum thread says "Declare any prompts, scripts, or assets you
made before the jam" and nobody has answered whether Starter Content and templates count. So: keep a
`SOURCED_ASSETS.md` in the repo with one row per item (name, source URL, licence, folder path, date added,
what it is used for), copy the table into the itch.io page and dev log, and state "UE 5.8 Third Person template
content and Starter Content, Epic, EULA" explicitly. Put every sourced item under one `Content/Sourced/` folder
(or note the paths) so nothing original is mixed in. Pre-window scripts need their own list of "prepared before
the window" (name, commit hash, date), which also matches Rule 7(h)'s version-control history request.

## What this means for our pipeline

1. **Replace node-by-node UMG calls with one Python entry point** (`ui_kit.py`, editor-side, run through the
   `runreal`-style Python route or the Epic MCP Python tool). Data in, assets out:
   - Input: a small JSON spec (screen name → widgets with name, class, parent, text, colour, anchor), written
     during the window from the theme. Script content stays generic; no theme text is baked in beforehand.
   - Steps: `create_asset` with `WidgetBlueprintFactory` (`parent_class = UserWidget`) → `add_source_widget`
     in the order Canvas → Vertical Box → TextBlock/Button → `find_source_widget_by_name` → set properties →
     `save_loaded_asset`. Return the asset paths and the widget names as JSON, so the agent never guesses a name.
   - Test it **now** (pre-window) against a throwaway project, with sample strings only. That is a tool, not a
     game asset. Delete the throwaway output afterwards.
2. **Fix the wiring with a fixed Blueprint recipe** (the graphs Python cannot make): button `OnClicked` → remove
   widget, set input mode, start or restart; `EndGame(bWon)`; `BeginPlay` → show menu. Write this once as
   exact MCP/BlueprintTools call lists keyed by the widget names `ui_kit.py` returns. This is the part that
   failed with guessed parameter names. Record the working parameter names in a cheat sheet.
   Alternative to test: C++ base classes with `meta=(BindWidget)` so the Python tool only needs to match
   widget names and the graph work disappears. It needs a C++ compile on Linux and the editor restart rule
   from the earlier note. Whether a generic menu base class counts as "script/tool" or "gameplay code" under
   Rule 7(h) is for the owner (or an organiser answer) to decide. **Do not write it before asking.**
3. **A "diagnose why the menu is not shown" checker** (read-only, safe to prepare): after PIE starts, log
   whether the widget exists, is in the viewport, its visibility, the player controller's input mode and cursor
   state, and the focused widget. This turns the mock-jam-5 bug into a 30-second check.
4. **Input kit** (`input_kit.py`): create `IA_Move`, `IA_Look`, `IA_Jump`, `IA_Pause` etc. and one `IMC_Default`
   with keyboard and gamepad keys on the same actions via `map_key`. Add the context through
   `DefaultMappingContexts` or one `BeginPlay` node.
5. **Controller test is part of the done criteria**: menu is reachable and Restart works on the Legion Go S
   with no mouse.

## Gaps

- No 5.8 page shows a full working `add_source_widget` call. Its parent-name argument and whether child
  widgets keep stable names across saves are untested.
- Slot layout from Python (anchors, offsets, alignment) and Python construction of `unreal.Key`, triggers and
  modifiers are unconfirmed.
- Whether any Python or editor library can add Blueprint graph nodes without MCP was not checked.
- The EULA text itself (403), the Lyra and GASP licence terms, and the 2026 official rules text on templates
  and Starter Content were not read. The 5.8 release notes were read only to character 100,000.
- Whether 5.8 Common UI still needs the data tables, and which Common UI classes Python can create.
- The cause of the mock jam 5 "menu not shown" bug is unknown.
- ChiR24 `ui.ts` and the forum "restart" threads are third-party or UE4-era.

## Next checks before Nov 11

1. In a throwaway project (CPU-only, no GPU tool): `dir(unreal.EditorUtilityLibrary)`, then run
   `add_source_widget` with Canvas → VerticalBox → TextBlock + Button; print the returned names.
2. In the same project, test property setters flagged above: `Button.is_focusable`, `InputAction.value_type`,
   widget slot anchors.
3. Run `input_kit.py` to create `IA_*` and `IMC_*` assets through the factories; try
   `unreal.EnhancedInputDeveloperSettings` access **[class name unconfirmed]**.
4. Build the one-screen smoke test on Windows and the Legion Go S: menu → play → lose → restart with gamepad
   only. Time it; the target is under 20 minutes from empty project.
5. Ask in the jam Discord/forum, or read the itch.io rules page, for how Starter Content and template assets
   must be listed, and whether a generic C++ UI base class prepared before the window is allowed.
6. Read the remaining 5.8 release-notes text for UMG, Python and template changes.

## Caveats

- Everything here is documentation reading; no API call was run. The Python docs are labelled "Experimental"
  and show several Read-Write/Read-Only contradictions.
- Menu-flow steps are an assembled recipe from a 4.26 tutorial and forum posts (some UE 4 and 5.3), not an
  Epic 5.8 page. Test in 5.8.
- Third-party blogs (bugnet.io and similar) are hypotheses to test, not authority.
- Licence and declaration notes are not legal advice. The official rules and EULA decide.
