# Numeric feel spec (one page, fill with numbers)

Adjectives ("snappy", "floaty") are not a spec. Fill every row with a number and a unit, or write `TBD` and tune
it by play. Numbers measured from a reference game are fine as targets; no content copied (Rules 8, 15(d)).
All values then live on the Settings actor (`04-settings-and-test-room.md`).

| Item | Value | Unit | Source (measured / guessed) |
|---|---|---|---|
| Max run speed | | cm/s | |
| Ground accel to max | | s | |
| Stop time | | s | |
| Jump apex height | | cm | |
| Time to apex | | s | |
| Fall gravity multiplier | | x | |
| Coyote time | | s | |
| Jump buffer | | s | |
| Air control | | 0-1 | |
| Hit stop | | ms | |
| Camera shake on hit | | cm, s | |
| Attack cancel window after hit frame | | ms | |

Tune loop: play, write one short note, change one number, replay. Log the count of tuning rounds
(the mock run records it). Claim that controls need many rounds: UNTESTED.
