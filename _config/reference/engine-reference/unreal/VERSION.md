# Unreal Engine — Version Reference

| Field | Value |
|-------|-------|
| **Engine Version** | Unreal Engine 5.9.0-preview-1 ("UE 5.9 MegaJam Preview", commit `acf0265`), built from source, 2026-11-10 |
| **Fallback** | Unreal Engine 5.8.4 (hotfix of 5.8) stays the fallback if 5.9 proves unusable. Sections below that say 5.8 still hold for 5.8.4 |
| **Installed at pin time** | 5.9.0-preview-1 built from source (Build.version 5.9.0, Changelist 0, not a promoted build); 5.8.4 also installed. The editor on Linux needs `SDL_VIDEODRIVER=x11` under Wayland |
| **Release Date** | 5.9 Preview: 2026-11-09 (Epic forum announcement); 5.8.0: June 2026; 5.8.3: September 2026 |
| **Project Pinned** | 5.8 on 2026-10-17; moved to 5.9.0-preview-1 on 2026-11-10 (owner decision), 5.8.4 as fallback |
| **Last Docs Verified** | 2026-11-10 (5.9 Preview release notes, Epic MCP / Python / Assistant docs, forum thread, source diff and live editor run; see `ue59-release-notes.md`); 2026-10-17 (release timeline, 5.8 release notes, and the 5.8 changes recorded in this directory); 2026-02-13 (rest of directory, written against 5.7) |
| **LLM Knowledge Cutoff** | May 2025 |

## Knowledge Gap Warning

The LLM's training data likely covers Unreal Engine up to ~5.3. Versions 5.4
through 5.8 introduced significant changes that the model does NOT know about
(5.4 and 5.5 predate the cutoff but are not reliably covered). Always
cross-reference this directory before suggesting Unreal API calls.

## Installed-Version Gap Warning

The warning above is one-directional — it covers the **model** knowing less than
this pin. The reverse gap is real and `/setup-engine` §3 creates it deliberately
("pin the newer one and upgrade later"): this reference can sit **ahead of the
installed editor**, and an agent citing it correctly then emits APIs that do not
compile locally. **Check `Installed at pin time` above before trusting a
version-qualified claim** — `NOT DETERMINED` means the gap is unknown, not absent.

## Post-Cutoff Version Timeline

| Version | Release | Risk Level | Key Theme |
|---------|---------|------------|-----------|
| 5.6 | Jun 2025 | MEDIUM | Large open worlds at 60 Hz (Hardware Ray Tracing Lumen performance, Fast Geometry Streaming plugin, Experimental), MetaHuman Creator in the engine, in-editor animation and rigging tools |
| 5.7 | Nov 2025 | HIGH | PCG production-ready, Substrate production-ready (on by default for new projects), MegaLights Beta, in-editor AI Assistant (Experimental) |
| 5.9 Preview | Nov 2026 | HIGH | AI/agent workflows: Unreal MCP starts with the editor, Toolsets, Unreal Assistant with external agents, Unreal Canvas (Experimental); Lumen World Cache, Adaptive Voxel OIT, Dynamic Wind; Unreal Animation Framework; experimental Web (WebGPU) target; Windows SDK 26100 preferred. Preview: about a week of development and short QA. See `ue59-release-notes.md` |
| 5.8 | Jun 2026 | HIGH | MegaLights production-ready, Iris replication production-ready, Mesh Terrain (Experimental), Lumen Lite (Beta), Enhanced Input and Common UI unified, MCP Server plugin (Experimental), C++20 minimum, WASAPI default audio backend on Windows, multi-pass deferred default on mobile |

## Unreal Engine 5 Releases Before the Cutoff

These two predate the May 2025 cutoff, so they are not post-cutoff. The Knowledge
Gap Warning above still applies to them: treat their APIs as unconfirmed until
checked against this directory.

| Version | Release | Risk Level | Key Theme |
|---------|---------|------------|-----------|
| 5.4 | Apr 2024 | HIGH | Motion Matching production-ready, Choosers, animation authoring (Modular Control Rig, Sequencer rework), Nanite Tessellation (Experimental), Motion Design mode |
| 5.5 | Nov 2024 | HIGH | MegaLights introduced, Substrate moves to Beta, Sequencer animation authoring, mobile game development, many features reach production-ready |

Release dates verified 2026-10-17 against Epic's release announcement threads:
5.4 (Apr 23, 2024) https://forums.unrealengine.com/t/unreal-engine-5-4-released/1817064,
5.5 (Nov 12, 2024) https://forums.unrealengine.com/t/unreal-engine-5-5-released/2117936,
5.6 (Jun 3, 2025) https://forums.unrealengine.com/t/unreal-engine-5-6-released/2538952,
5.7 (Nov 12, 2025) https://forums.unrealengine.com/t/unreal-engine-5-7-released/2673913,
5.8 (Jun 17, 2026) https://forums.unrealengine.com/t/unreal-engine-5-8-released/2729274.
Hotfixes 5.8.1 (Jul 28, 2026), 5.8.2 (Aug 25, 2026) and 5.8.3 (Sep 22, 2026):
https://forums.unrealengine.com/t/5-8-3-hotfix-released/2833315. Key themes come
from the same threads and from the 5.7 and 5.8 release notes (Verified Sources below).

## Major Changes from UE 5.3 to UE 5.8

### Breaking Changes
- **Substrate Material System**: New material framework (replaces legacy materials); new projects created in 5.7+ have it enabled automatically
- **PCG (Procedural Content Generation)**: Production-ready, major API changes
- **MegaLights**: New lighting system for many shadow-casting dynamic lights; production-ready in 5.8
- **Animation Authoring**: New rigging and animation tools
- **C++20 minimum (5.8)**: `CppStandardVersion.Cpp14` and `Cpp17` are obsolete and no longer compile
- **5.8 API removals**: deprecated animation, Control Rig and Live Link symbols from 5.0-5.6 removed; PhysicsMover removed from Mover in favour of ChaosMover — see `breaking-changes.md`

### New Features (Post-Cutoff)
- **MegaLights**: Dynamic lighting at massive scale (production-ready in 5.8)
- **Substrate Materials**: Production-ready modular material system (5.7)
- **PCG Framework**: Procedural world generation (production-ready in 5.7)
- **Iris**: Replication system, production-ready in 5.8
- **Lumen Lite (5.8, Beta)**: Medium-quality GI setting, the default on current-generation handheld consoles
- **Mesh Terrain (5.8, Experimental)**: Mesh-based terrain beyond heightfield landscapes
- **Enhanced Virtual Production**: MetaHuman integration, deeper VP workflows
- **Animation Improvements**: Better rigging, blending, procedural animation
- **AI Assistant (5.7)**: In-editor AI help (Experimental)
- **MCP Server (5.8)**: Editor plugin that lets agentic AI systems connect to the Unreal Editor (Experimental)

### Deprecated Systems
- **Legacy Material System**: Migrate to Substrate for new projects
- **Old PCG API**: Use new production-ready PCG API (5.7+)
- **Raw Input plugin (5.8)**: Deprecated in favour of the Game Input for Windows plugin
- **`UE_LOG` (5.8)**: Still supported; Epic says it "will eventually be deprecated" and asks for `UE_LOGF`

## Verified Sources

- UE 5.9 Preview release notes: https://dev.epicgames.com/documentation/en-us/unreal-engine/unreal-engine-5-9-release-notes
- UE 5.9 Preview forum thread: https://forums.unrealengine.com/t/2852840
- UE 5.9 details, tags and the 5.8.4 to `acf0265` diff: `ue59-release-notes.md` in this folder
- Official docs: https://dev.epicgames.com/documentation/en-us/unreal-engine/unreal-engine-5-8-documentation?application_version=5.8
- UE 5.8 release notes: https://dev.epicgames.com/documentation/en-us/unreal-engine/unreal-engine-5-8-release-notes?application_version=5.8
- UE 5.8 release thread: https://forums.unrealengine.com/t/unreal-engine-5-8-released/2729274
- UE 5.8.3 hotfix: https://forums.unrealengine.com/t/5-8-3-hotfix-released/2833315
- UE 5.7 release notes: https://dev.epicgames.com/documentation/en-us/unreal-engine/unreal-engine-5-7-release-notes
- What's new in 5.7: https://dev.epicgames.com/documentation/en-us/unreal-engine/whats-new
- UE 5.7 announcement: https://www.unrealengine.com/en-US/news/unreal-engine-5-7-is-now-available
- UE 5.5 blog: https://www.unrealengine.com/en-US/blog/unreal-engine-5-5-is-now-available
- Migration guides: https://dev.epicgames.com/documentation/en-us/unreal-engine/upgrading-projects-to-newer-versions-of-unreal-engine
- Engine source, read from a UE 5.8.1 install on 2026-10-17: `Engine/Source/Programs/UnrealBuildTool/System/CppCompileEnvironment.cs` (C++ standard), `Engine/Source/Runtime/RenderCore/Private/RenderUtils.cpp` (Substrate defaults)
