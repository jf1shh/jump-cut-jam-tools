# Possible concept: water balloon physics in UE 5.8

Research date: 2026-10-29. Source: a `/deep-research` run (5 search angles, 20 sources fetched, 25 claims
put through 3-vote adversarial verification: 22 confirmed, 3 refuted). Confidence levels below are the
run's own.

**Status: a possible concept only, not a decision.** Whether it fits depends on the theme revealed
2026-11-11. It suits readings like splash, pressure, fragile, wet, fill-up or throw. This is research
notes only. No gameplay, levels or art for it exist or may exist before the contest window opens
(Rule 7(h)).

## Why it might be worth it

- One familiar verb (throw) with a physical twist (how full the balloon is changes how it flies,
  wobbles and bursts). That matches the "twist a known genre's core verb" pattern in
  `mechanics_and_genre_ideas.md`.
- It reads instantly in a 30–60 s video: wobble on throw, squash, burst, splash, wet mark.
- The cheap version of every piece (shader wobble, speed threshold, particle splash, decal) can be built
  in Blueprint in a day, with Niagara Fluids as an optional upgrade.

## The physics to approximate

| Stage | What really happens | Game approximation | Confidence |
|---|---|---|---|
| Wobble (in flight, small hits) | Latex tension pulls surface waves back like surface tension on a drop; waves closely follow linear theory | Damped spring or sine wobble in World Position Offset; small-amplitude only | high |
| Squash and recover | Impact behaves like a liquid-drop impact; kinetic energy becomes elastic energy, then pressure makes it retract and maybe bounce | Squash scale/WPO keyed off impact speed, spring back | high |
| Burst decision | Bursts above a critical speed that drops as pre-stretch (fullness) rises | `Burst if ImpactSpeed > BaseThreshold * f(Fullness)`, f falling with fullness; tune by hand, papers give no game numbers | high |
| Burst sequence | Skin snaps back (shear instability) → water spikes (Richtmyer–Meshkov) → gravity slumps it into a spreading puddle | Three VFX beats: skin-retraction flash, spike splash, spreading decal/puddle | medium (one 2-page source) |

Sources: Lund & Dalziel, "Bursting water balloons", J. Fluid Mech. 756 (2014)
<https://resolve.cambridge.org/core/journals/journal-of-fluid-mechanics/article/bursting-water-balloons/A9C7346C0A035E27F4A48CB1E8F1C251>;
their 2011 video abstract <https://arxiv.org/pdf/1110.3320>; Jambon-Puillet, Jones & Brun, Nature
Physics 16 (2020), via <https://engineering.princeton.edu/news/2020/03/19/water-balloon-physics-high-impact-science>.

## UE 5.8 tools, cheapest first

- **WPO wobble and squash** (medium): vertex-shader World Position Offset, vertex colour masks the
  strength, velocity/impact fed in as material parameters. Works with Nanite. Visual only, collision
  does not change. <https://forums.unrealengine.com/t/fake-physics-effect-driven-by-vertex-color/371868>
  - Fab plugin **Woziva Shape Cage** packages this for static meshes (`MF_ShapeCage`, box/sphere/curtain
    cages). UE 5.6–5.8, Windows only; performance claims are the vendor's. A sourced asset, so it is
    not scored and must be listed (Rule 15(c)).
    <https://forums.unrealengine.com/t/woziva-shape-cage-mesh-deformer-crush-boxes-squash-balls-close-curtains/2746634>
- **Spring jiggle on a skeletal mesh** (medium): Physics Asset Editor constraints with soft swing
  stiffness/damping, or AnimDynamics / Spring Controller / Control Rig springs. Enable Soft Swing
  Constraint and set swing to Limited. Needs bones.
  <https://www.wayline.io/blog/jiggle-physics-implementation-guide>
- **Chaos Cloth pressure skin** (high that the API exists, untested as a projectile): `Set Pressure` on a
  Chaos Clothing Interactor (Vector2D input; units undocumented) inflates a closed cloth shell and can
  deflate it on burst. Also in C++ (`UChaosClothingInteractor::SetPressure`) and Python.
  <https://dev.epicgames.com/documentation/unreal-engine/BlueprintAPI/ClothingSimulation/SetPressure>
- **Chaos Flesh: avoid** (medium): real FEM soft body, but experimental, built for muscles, costly live,
  simulates solid volumes not a thin skin. The unified Cloth+Flesh solver in the 5.8 release notes did
  not ship. <https://dev.epicgames.com/documentation/unreal-engine/chaos-flesh-overview>
- **Visible slosh** (low): the free UTC_LiquidShader fakes liquid in a closed mesh from tick-to-tick
  motion. Targets 5.2/5.3, unmaintained; 5.8 untested.
  <https://github.com/UniversalToolCompiler/UTC_LiquidShader/wiki/UE5-Dynamic-Liquid-Shader:-Tutorial>
- **Splash** (high): Niagara Fluids 2D FLIP is the cheaper fit and Epic says it suits splashes, not pools.
  Shallow Water for puddles. 3D water is a PIC/FLIP grid solver, not SPH (rule-of-thumb PIC/FLIP ratio
  0.75–0.95). Colliders include static meshes, Geometry Collections and depth maps.
  <https://dev.epicgames.com/documentation/en-us/unreal-engine/fluid-simulation-in-unreal-engine---overview>
- **Niagara Fluids cost** (medium): can eat a big share of the frame (one 12 ms example), still Beta in
  5.8, and the default Medium scalability can hide it entirely. Profile in Standalone. With several
  balloons popping at once, plain sprite/mesh particles plus a decal are safer.
  <https://80.lv/articles/working-with-niagara-fluids-to-create-water-simulations>
- **Multiplayer** (high; only if we go multiplayer, which the plan advises against): not Default physics
  replication (clients snap back); Predictive Interpolation for server-owned balloons; degrades at high
  ping and speed. <https://dev.epicgames.com/documentation/en-us/unreal-engine/networked-physics-overview>

## Suggested build order if the theme fits

1. Projectile Blueprint with a `Fullness` float; throw arc and speed from it.
2. WPO wobble material (`M_Balloon` + instances) driven by velocity, and squash on hit.
3. Burst rule from impact speed and fullness.
4. Burst VFX in three beats (`NS_BalloonBurst`): retraction flash, spike splash, puddle decal.
5. Only if time and frame budget allow: Niagara Fluids 2D FLIP splash, then Cloth pressure skin.

## Not found or not verified

- No shipped Unreal game, Fab asset or Epic tutorial with water balloons.
- No Geometry Collection / Chaos destruction setup for the burst. The claim that skin retraction fits
  better than debris was refuted 0–3, so it is open.
- No wet decal or wetness-mask workflow (deferred decal vs Runtime Virtual Texture vs material wetness).
- No per-balloon performance numbers beyond the 12 ms fluid example.
- Open: is a Cloth-pressure skin stable and cheap enough for 10+ thrown balloons? How should burst
  position replicate under latency?
