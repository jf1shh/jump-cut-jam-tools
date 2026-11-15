---
tier: epic
source: the editor's own describe_toolset output, hub 50 run 2026-11-09 (tools listed, none called)
updated: 2026-11-09
---

# Cheat sheet: PCG through MCP (PCGToolset)

Toolsets `PCGToolset.PCGToolset` (30 tools, describe 34,035 chars) and `PCGToolset.PCGSpatialToolset` (names only).
No PCG tool was called here: UNTESTED in use. `*` = required.

## Tip: build a graph in this order (from the tool names)
1. `CreateGraph(name*, path)`.
2. `ListNativeNodes(bCommonOnly)`, then `GetNativeNodeSchema(nodeName*)` for the node you want.
3. `AddNode(graph*, nativeNodeType*, nodeName*, jsonParams*, nodeTitle*, nodeComment*, xPositionIdx, yPositionIdx)`.
4. `ConnectNodePins(fromNode*, fromPinLabel*, toNode*, toPinLabel*)`.
5. Put it in the level: `SpawnGraphInstance(graph*, name*, transform*, jsonParams*)`, then `ExecuteGraphInstance(pCGVolume*)`.
- **Why:** the schema call tells you the `jsonParams` shape; guessing it is the usual first failure.
- **How to check:** `GetGraphStructure(graph*)` lists the nodes and links; `GetNodeDataView(pCGVolume*, node*, pinLabel, attributeName*)` shows output points.

## Tip: edit and tidy
`UpdateNode`, `RemoveNode`, `DisconnectNodePins`, `SetGraphParams`, `SetGraphInstanceParams(pCGVolume*, jsonParams*)`,
`AddSubgraphNode`, `ListAvailableSubgraphs`, `DrawSpline(actorLabel*, actorTag*, bRedraw*, bClosedSpline*)`, comment-box tools.
- **Why:** several tools require all of their arguments, even ones that look optional (`DrawSpline`, `AddNode`'s title and comment).
- **How to check:** a missing-argument error lists the required names.

## Tip: save a scatter as a template (lesson 2.16)
Claim from a video, UNTESTED: keep one working graph and reuse it through `SpawnGraphInstance` with new params.
