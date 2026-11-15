---
tier: epic
source: the editor's own describe_toolset output, hub 50 run 2026-11-09 (tools listed, none called)
updated: 2026-11-09
---

# Cheat sheet: Niagara through MCP (NiagaraToolsets)

Five toolsets: `NiagaraToolsets.NiagaraToolset_{Info,Component,Blueprint,System,Assets}`. Only `_System` was
described (278,098 chars, far too big to read whole; the claim of about 250K tokens in a video is the same order
of size). Names and arguments below come from that describe; no Niagara tool was called. UNTESTED in use.
`*` = required.

## Tip: read the schema before writing values
- **Why:** nearly every setter takes a nested data object. The schema getters say its shape.
- **How to check:** call the matching `Get...Schema` first: `GetSystemSchema()`, `GetEmitterSchema()`,
  `GetRendererSchema(rendererClass*)`, `GetModuleSchema(moduleReference*)`, `GetStackInputSchema(inputReference*)`,
  `GetDataInterfaceSchema(dataInterfaceClass*)`.

## Tip: build order (from the tool names, UNTESTED)
1. `CreateNiagaraSystem(assetName*, assetPath*, templateSystem*)`: start from a template.
2. `AddEmitter(system*, templateEmitter*, emitterName*)`.
3. `AddModule(moduleLocationRef*, moduleAsset*)`, `AddRenderer(newRendererLocation*, rendererClass*)`.
4. Set values: `SetEmitterData`, `SetSystemData(system*, systemData*)`, `SetRendererData`, `SetStackInputData(stackInputRef*, inputData*)`,
   `AddSetParametersModule`, `SetModuleEnabled(moduleRef*, bEnabled*)`.
5. Check: `GetStackIssues(system*)` and `GetSystemCompileState(system*)`; `ApplyStackIssueFix(system*, issueId*, fixId*)`.
- **How to check:** the compile state reads clean and `GetSystemSummary(system*)` lists the emitters you added.

## Tip: read tools
`GetSystemData`, `GetEmitterSummary`, `GetEmitterTopology`, `GetModuleTopology`, `GetModuleInputValues`,
`GetAvailableDynamicInputs(type*)`, `GetUserVariables`, `AddUserVariables`, `RemoveModule/Emitter/Renderer`.
- **Why:** an effect is a few small layers; ask for a batch and keep the few that read (lesson 2.18, UNTESTED).
- **How to check:** `mx.py describe NiagaraToolset_System --grep NAME`. Never print the whole cache.
