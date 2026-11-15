# Mock jam 10 brief: water balloon

Plan: `stages/00_prep/references/mock-jams-10-14-plan.md`. Slot: Sat Nov 7 21:00 PT to Sun Nov 8 07:00 PT, overnight (8-10 h, hard stop 10 h = 07:00; no sliding into the day).
Overnight: the owner starts the loop before bed; do not block on an owner ask (log it in the findings doc and keep going).
Findings file: `stages/00_prep/output/mock-jam-findings-10.md`.

**Rule 7(h):** run only in the throwaway `~/Projects/megajam-mock`, and delete it after. No gameplay,
level, art, audio or game code from this mock may be reused in the real entry. Only tooling fixes and the
findings doc come back.

## Theme reveal (read at T+0)

> **WATER BALLOON.** Make a game about a balloon full of water.

## Game idea seed

You carry a fat water balloon through a small rooftop garden. It sloshes as you move and sags where you
squeeze it. Drop it on a dry plant to water it, but if it hits a hard edge it bursts and you lose water.
Water every plant before the balloon runs dry.

## Physics and material focus

Slosh (water mass shifting inside a shell), splash on impact, burst when stress passes a limit.
Translucent rubber material with a wet look. Keep it cheap: a spring-damped blob plus Niagara splash, not a
real fluid sim.

## Readiness gap to prove: 1c + 6d (editor launch from the real jam loop)

The mock must be started the way the real jam is: owner runs `HANDOFF_MAX_RESTARTS=300 proj start megajam-mock`.
The lead agent is then **not** a ticket worker, so the ticket guard should not apply. Inside that loop:

1. `lemonade unload`, then `gpu-preflight` prints `CLEAR`.
2. Launch the editor with the exact line from `stages/00_prep/references/jam-day-runbook.md` section 2 (own `systemd-run` scope,
   `-ModelContextProtocolStartServer -ModelContextProtocolPort=8010 -nosplash`).
3. `ss -ltnp | grep :8010` shows the editor, and `curl -s -o /dev/null -w '%{http_code}\n' http://127.0.0.1:8010/mcp`
   prints `405`.
4. Record every command the harness or guard denied, with the exact text. If any denial is a guard rule, list
   the rule so the hub can fix it before mock 11.

## Pass / fail gates

- [ ] PASS 1c: editor launched by the loop's agent, port 8010 up, `405` printed. FAIL if the guard blocks it.
- [ ] PASS 6d: no guard denial on editor launch, `systemd-run`, or Saved/Logs copy. List any denial as FAIL.
- [ ] Greybox plays: slosh, splash and burst all visible.
- [ ] Windows package built on the Legion and pushed to `jf1shh/megajam-pretest:win64`; `butler status` shows it processed.
- [ ] 30-60 s video recorded (OBS on the Legion).
- [ ] Time stayed within 10 h wall clock. Lemonade restored at ctx 32768.
- [ ] Findings written to `stages/00_prep/output/mock-jam-findings-10.md`: what passed, what failed, minutes per phase, bugs, tooling fixes.
- [ ] `~/Projects/megajam-mock` deleted after the findings merge.
