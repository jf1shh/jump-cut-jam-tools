# JUMP CUT dev log: how it was made

Team Second Unit. Solo entry by Jared Fisher. Theme: "Director's Cut". Made in Unreal Engine 5.9 for the 2026 Epic AI MegaJam. This is my entry for the Glass Box prize, so this page covers how the game got built as well as what it is.

I worked with a team of AI agents (Claude, through Claude Code). They wrote almost all of the code and ran the tests. I made the calls and played the game, and I submit it by hand.

## How the team worked

- Me: I pick what the game is, accept or reject what comes back, play it, and submit it.
- The hub: one Claude session I talk to. It does not write the game. It plans, hands out jobs, reads the results, and tells me what needs my call.
- The lead: a Claude Opus session that writes the game code and works in the Unreal Editor through Epic's Unreal MCP plugin. (A plugin is an add-on. This one lets an agent click and build inside the editor.)
- Helpers: short-lived Claude sessions for one job each: a design spec, a review, a docs fix. Claude Haiku did read-only audits, read files and logs, and wrote project notes and status files. Claude Fable took the hardest review calls.
- The test handheld: a Windows handheld on my desk. A separate Claude session runs on it. It runs each new build with scripted keys and takes screenshots and video. It reports pass or fail.
- The trailer: its clips were recorded by a scripted bot playing the real build, so every take is clean and repeatable. The edit only adds the cuts between clips, two title cards with their sounds, and a music bed.
- Version control: the game lives on Diversion. Every test build is a numbered commit, and a build that passes gets a "good build" tag, so a bad change can always be rolled back to the last good one.

In a build test, the lead makes a numbered build of the game. The handheld packages it into a zip, starts it, plays a script, and checks the log for lines like "results screen shown". If everything passes, the build is called CLEAN. If not, the list of problems goes back to the lead.

[IMAGE from the final capture: "the cut", the hold look, then the frame right after release]

## Day 0: Wed Nov 11

Before the window: Epic revealed the theme, "Director's Cut", on the 11 AM PT kickoff stream. The contest window did not open until 9 PM PT. In between, the agents wrote idea notes against the theme and I picked one. At 1:31 PM I said "Yes, lock it" and Jump Cut became the design doc. It was text only: no project, no level, no code, no art. The agents then wrote a prep pack from it (shot lists, HUD sketches, a metric sheet per scene, a data table) and made 17 labelled reference pictures. Every one of those pictures says "PRE-JAM REFERENCE, NOT A GAME ASSET" across the bottom and none is in the game. All of this, plus the tools and scripts built in the weeks before, is listed in the pre-jam declaration ([OWNER-FILL: link to the pre-jam declaration post, once you have posted it on Sunday]).

At 9 PM the window opened. The Unreal project was created at 9:03 PM. The first C++ files landed at 9:04. The project set-up, a plain blockout level (gray shapes), a press-to-start screen, and a sky. The jam plan said work until 1 AM, then sleep until 8:30.

Who did what: The agents had written the set-up scripts and checklists before the jam; those tools are in the pre-jam declaration. Every game file, level, Blueprint, mesh, sound and line of gameplay code was made after 9 PM. The lead built the blockout. I watched and answered questions.

The decision I made: "Yes, lock it." Three concepts were scored, then a review tried to break them. Jump Cut scored 23 of 35 on a realistic build, against 20 and 19 for the others.

There were some initial hiccups with the tooling and workflows, so I was a bit nervous. I didn't get much sleep the night before, so I was very tired, but also excited to build.

## Thu Nov 12 (day 1)

What got built: most of Scene 1. A car drives down a road. Hold to look, release to cut. Driving a stunt clean scores up to +3. Cutting scores nothing and spends one piece of film. A crash gives one free retake. Each result gets a stamp: WIDE, CLOSE, PERFECT, CUT. A wrap screen shows points and stars. Music and sound effects came later that day, from a synth script (more below). I also added a title screen and a quit key.

Who did what: The lead wrote the code. The handheld ran builds B5 to B9 and sent back reports. Helpers wrote the look guide and the plan for Scenes 2 and 3. I read each report and said go or fix.

What broke:
- Build B8 failed after 78 minutes. Microsoft's compiler stopped on one local variable named `Slot`. It hid a name inside the engine's own code. The Linux compiler on my desktop did not care, so my Linux checks were green. The lead renamed it. Lesson: the Linux compiler passing says nothing about the Windows one. The ship script now runs a short Windows compile check first. It takes about 23 seconds.
- A run showed a stunt crashing. A finer test (smaller time steps) showed the game was fine. The crash was timing noise in the test.
- Window size: on the handheld's sharp screen, the window opened smaller than asked (960 by 536). The fix: tell the engine to respect high-DPI screens. It held: from test build 11 the window opens full size on the handheld. [SOURCE NEEDED]
- Picture quality: test builds were captured at 1600 by 1000, below the 1080p the rules ask for. The fix: the handheld now records the game itself at its native 1920 by 1200, and the video is cut to 1920 by 1080 with thin black bars at the sides, so nothing on screen gets cropped. The B10 capture came in at 1920 by 1200. [SOURCE NEEDED]
- An open network port: build 63 (B9) passed, but the game was listening on a network port, left over from the engine's debug trace tool. A stranger could get a firewall pop-up as the first thing they see. Build 64 compiles that tool out. The Unreal MCP plugin stays editor-only, so it is not in the shipped game.

The decision I made: No more posting to itch until the very end. Nothing goes up, not even the private test page, until one upload on Sunday that I do by hand.

[IMAGE from the final capture: the PERFECT stamp]

B10 test (build 65): this build adds a "SECOND UNIT presents" card at launch, hints that change with keyboard or gamepad, and no open ports. B10 did not come back clean, so the page video moved to a later build.

Later that day, test build 11 fixed the window (full size on the handheld) and turned off one heavy rendering feature (Nanite) on weak graphics chips, with the same look. Test build 12 fixes the CLOSE stamp and adds stunt sounds, a loudness limiter and the first Scene 1 look (real props, a dashed-lane road, a studio skyline). [B12 RESULT: clean or not, and what the handheld showed]

## Fri Nov 13 (day 2)

What got built: Thursday night and Friday went in numbered builds. B13 to B13c added a curved road, an opening ramp, a Director's Cut take with a clapper slate, wide shots that earn no film, and a cut in on-screen text (I said it was "way too busy with a lot of text"). Friday I added a hold cue: while you hold Space, the screen says what letting go does and what holding on does. Then a stick fix for controllers, a heavier lane change, a setting so any controller can steer, and a log of every key press for the friends who play tonight. The music became two 70s-style funk tracks. After I heard them I said "Use these". In the evening: clearer cut words, a rule that cuts for you if you are still holding at the end, and a water tower that leans while its false front falls.

What broke, and how it was found:
- The handheld stopped taking input at 09:13. The game window would not come to the front and "last input" read zero. The agents ruled out stick drift by measurement. The cause was never identified, so tests ran on keys sent as window messages. That is not a human keyboard, and the notes say so.
- Performance failed its floor: 23.0 frames a second (1% low, Development build) against a 26.1 floor.
- At 18:50 the packaged game would not compile. The day's outdoor-light code used an editor-only call. The compile check had only built the editor. It now builds the game too.
- At 20:15 I asked whether the game was being saved to Diversion and GitHub. It was not: the last Diversion save was 05:27, with 116 files unsaved. I said "Yes, push it", and a save went in at 20:30.
- Agents that had never seen the game read the pictures of each build and said what a new player would do. Three of them failed at the same three places on the build I played: the must-cut cue, a crash that gives no reason, and a mid-air "[E]" prompt nobody had taught. So that build failed the new-player gate.

What the agents got wrong, and how it was caught:
- The hub told me a pad-hint bug was confirmed within a minute of the lead reporting it. The lead had written that the code cause was not yet read. The lead read the code and corrected itself six minutes later. A caveat someone attaches to their own finding is not for the next person to drop.
- A planned patch would have drawn gold corners during the hold. A hub read the clock code first: the cut window ends before the gold, so players would have been taught to release on gold, into the action worth +0. The patch was killed.
- Documents had called the star cap a retake cap all night. The code counts crashes.
- Break-it reviews of the friends' build found two real bugs. The stick fix would have blocked lane changes on worn controllers, and the play log wrote to disk on every key press. Both were fixed and attacked again.
- The Windows handheld's own runner refused to launch one build under its safety check. The hub could not talk it past that; I typed the OK myself.

The Legion runs: B13b passed its break-it run (16 launches, no crash, no soft-lock). The friends' build passed all main rows, four screenshots at the real screen size and 34 break-it cases over 41 launches, with no game crash. One case failed: a fast lane tap can be lost for a frame. I chose "Send as is". I played it on the handheld's own controller and said "done stick feels great lock it in": 38 stick lane changes, none ignored. The stick is now locked.

Decisions I made: I kept the AI music, with the credit line on the page. The terms are unclear on one point, and a written question to the platform's support is drafted. [OWNER-CHECK: say in your words whether you sent that question and whether fal answered. Do NOT keep this sentence unless you sent it. If fal says no, the game goes back to the code-made loops.] I also said "players even me I am making this game need cues and hints in order to understand". The three friends got the build that evening.

Page facts that were wrong: before I sent the page, a helper listed what was really inside the packaged Windows build and compared it with the page text. The page said no AI made the music; the music tracks in the build are AI-generated (ElevenLabs Music, through fal). It also said the Rodin water tower was left out of the game; it is in the build. A free plywood texture (CC0, Poly Haven) was in the build but not on the sourced-assets list. All three were fixed. Lesson: check the page against the package, not against my notes.

The HUD icons: I asked a Claude helper for a set of simple icons as vector code, looked at three versions, and told the hub "go with your v3 pick". Eleven icons ship in the build; no image model drew them.

[IMAGE from the final capture: the PERFECT stamp]

## Sat Nov 14 (day 3, so far)

From midnight to about 11 AM, the saves ran from 118 to 161. I said "i want you to hit 30/35", and "good night keep working and dont stop no idleness".

What got built: save 118 is about telling the player what to do. Every stunt you can steer past or cut now shows both choices with their buttons for the whole window: the lane action, and under it "or hold to cut". The old cause was that the lane cue turned off once the car was in the safe lane. Save 119 polished the tower. Then, in order: crashes that follow the car's momentum, a dry causeway where the ford was, ground and road looks made in the engine (the build's one sourced texture is Poly Haven plywood, CC0, on the ramp wedges and the set walls you crash into), a rebuilt wrap screen with less text, a new sound mix, a cut grade, a movie replay of your kept cuts, and crash hit-stop and camera kick. The Director's Cut now means one thing: your own cuts, driven. The Legion's own safe gate passed on the build I played (47 launches, close-crash 15 of 15, break-it 16 with 0 fail).

My overnight rule, in the words I typed: "things have to make logical sense....if a car impacts something on the ground it probably shouldnt flip, if its not in the air". So a car that hits something on the road stops hard and slides, and only a car in the air tumbles. I chose scoring option B, answered "Yes, grade the cut", and said "No, keep C" to a no-crash B. After playing, I said "textures and materials wil definitely need more polish but great work over night the game is looking much better!" and "that's a wrap end screen still has too much text though".

What broke:
- A prompt box painted with no words. It looks the same with every switch off, so it is in the base code. It is not fixed yet.
- The canal wall material never compiled: a custom shader used the reserved word `line`. Walls are matte concrete, lighter than planned.
- About two thirds of the far cliffs drew the engine's default grey, because a material was made from a material that Unreal refuses as a parent. A fix is cut and reviewed.
- The wet ford failed its look three times, so the ruling was to stop after two tries and ship a dry road through a pond.
- The oncoming truck slid sideways, then crabbed up to 64 degrees and lurched from 0 to 14 m/s in half a second. Both were rejected. A third version is in review.

What the agents got wrong, and how it was caught: after each batch of patches, three fresh agents read pictures of the build, with no notes, and answer per shot "what do I do, and which button". An agent that tries to break the patch reads it first. Reading 2 (pictures of save 120) scored 15 of 35 from a cold red-team; before it was 16. Reading 3 failed shot 7 for 2 of 3 readers. Reading 4 showed that "STAY CENTER > RIGHT" reads as do nothing. Reading 6 failed shot 7 for 3 of 3 and shot 3 for 2 of 3. "EARLY DODGE +0" showed up when a player steered safely as told. A cue text said a must-cut was free, and it was not. A looker comparing stills with a patch on and off caught a car floating on a teal lake and ripple rings drawn on dry asphalt. Break-it reviews caught a touch tap on the menu that switched glyphs to keyboard and a latch that kept a bright "STEER RIGHT" after a fast press. Two saves went in over a looker's "STOP", on purpose, because the fault was in the base code and not the patch. One hub counted its own memory 200K too low and was caught by the context guard.

The first friend's log, from the Friday build: 3.5 minutes, both scenes finished, 32 crashes. Early moves crash him. I answered "Clearer cue". Lanes and hazard timing stay locked, and a wait-then-now cue is ordered.

Still open at about 11 AM: the horizon fix and one shortened HUD line go in the next batch. The oncoming truck has to pass review or it is out. A reading on the newest build, a switch list and the README checks are owed. The wait-then-now cue is not built. A Windows Shipping build has not been run: the Linux compile is running, and Windows comes after a new handheld package. The plan is a twin cut at 13:00, a handheld pass from 14:15 to 15:00, and the freeze at 17:00. [OWNER-CHECK: keep "Still open" until the freeze, then replace it with what shipped.]

From 11 AM to about 12:15 the saves ran 163 to 165, and I stopped adding features. Save 163 fixed the HUD badge at 16:9; small overlaps remain at 4:3 and at 16:10 with the keyboard. Save 164 is the "Clearer cue" I asked for: WAIT, then a bar, then NOW. A looker still said BAD, for four small drawing faults. Save 165 put "DIRECTOR'S CUT" and "N OF M STUNTS CUT" on the wrap card, cut the hold down to one cue, and gave the oncoming truck lamps and a 1.0 s brake. 161 tests pass, 0 fail.

I also added a rule: anything that moves needs a real-life physics reason, and a "makes sense" review runs as a gate. Its first run was still going at 11:26. The handheld's safe gate passed on the test build (33 launches, 0 fail); scene 1 ran 13.81 ms median, scene 2 14.26 ms. I dropped a HUD clamp follow-up because redoing it changed nothing. Left for after the jam: the water tower falls too fast, props jump at a crash, and the front wheels do not steer.

The last four fixes (effects follow slow-motion, the car's pitch eases on the ramp, the light-rig tripod gets casters and a winch, and a polish for the cue faults) are in test. The final save is due 12:50 and the Shipping cut is planned for 13:00, after one Windows check on the final tree.

The final save, 166, went in at 12:34, 16 minutes before its target. Effects now follow slow-motion, the car's pitch eases on the ramp, the drums get a kicker plank, and the cue text is cleaned up. The light-rig tripod's tow line, winch and casters ship switched off: its look said STOP because a line ran across the lanes. A review of the whole diff said ship with fixes and found no code blocker; one fix, a Windows compile of the final tree, is still open. That compile finishes about 12:58, the Shipping cut is expected about 13:05, the handheld pass comes after it, and the freeze is at 5 PM.

The Windows check of save 166 was green at 12:47 and I gave the cut word at 12:48, 12 minutes before the planned 13:00. The Development twin package finished at 12:54 (764.8 MB). The first package named Shipping was really a Development build, because a script variable was lost; comparing file hashes caught it at 13:00. The real Shipping package of save 166 is now proven: 562.1 MB, a different exe hash from the Development twin, and the build log says Shipping config. A hand start of it is still owed. On pictures of 166, first-time readers got 7 of 7 on keyboard, all pictures and gamepad (an earlier gamepad 1 of 7 was a picture-kit artifact). The judge-style red team gave about 19.5 of 35, up from 18, and the main loss is too many words and rules on screen. The physics-sense pass still judges 25 of 61 moving things wrong. A text-only candidate, a four-line HOW TO PLAY card and DIRECTOR'S CUT on the wrap card, waits; if it is not ready by 13:40, 166 ships as it is.

After the cut I allowed one more save, text only, because the judge-style review said the top loss was too many words on screen. Save 167 has a four-line HOW TO PLAY card (the old one was 105 to 135 words) and shows DIRECTOR'S CUT once, on the wrap card, as a key row. Save 166 stays packaged as the fallback, and 167 ships only if it reads no worse. Three fresh readers per side, card only, scored 9 of 15 on both. Crash went from 0 of 3 to 2 of 3 and Director's Cut from 0 to 1 of 3, but the cut question fell from 3 of 3 to 0 of 3, because the cut cost is no longer on the card. I accepted that for a much shorter card. Both 167 packages are proven (Development twin 764.9 MB, Shipping 562.1 MB with a different exe hash and Shipping config in the build log). The handheld check of 167 is still running, with a target of 14:20; if it is red or late, 166 ships.

This afternoon, saves 168 and 169 were both drawing-only. Save 168 (14:56:56) gave the text boxes rounded corners and made the text fit, after I saw words bleed out of a box and old text under new text at the last stunt. Save 169 (15:45:34) added a second box fix, including the wrap card showing dimmed under the pause menu, and the credits line I chose: "Design and direction: SECOND UNIT. Code: Claude (AI)". The end announcer said "Check the gate!" and I heard "check re day"; it is not queued in 168 and a clearer re-record only happens if I ask for it back.

I also asked for arrows instead of text for which way to go (left in the top left of the box, right in the top right, centre in the top middle), a logo and icon that look much stronger, and a 70s retro-cool, a bit funky look. I picked logo A, SPLICE, because it goes best with the game art we already had.

What did not work: the stunt 7 cue. A looker and a fresh reader found it unclear on saves 167, 168 and 169, three saves in a row. The three steps run together as one line, no key or stick is named, and "OR HOLD (A) TO CUT" has no main instruction before the "OR". Save 169 did not make it worse, and it did not fix it. Next is save 170 with the arrows, then logo A, then overnight polish, the Sunday 11:00 freeze, and submitting at 17:11 PT on Sunday.

From 16:00 to 17:00, save 169 failed its picture check and I did not get it. At 16:10 and 4:3 the WAIT and NOW tags were gone at stunt 7, so it was held and save 168 stayed the safe build. I played 168 on the Legion and said "Played fine".

Then I gave a new rule: "i dont think i need to playtest anymore you have agents who can playtest it for us at this point". From now on the agents do the playtesting: hand runs on the Legion with keyboard and pad, a deliberate miss and a retake, lookers, fresh readers, and a sound check from a capture. I also asked what screen sizes the game supports. Only 1920x1080, 1920x1200 and 1440x1080 had been tested, and the Legion cannot show more, so I ordered checks on the desktop, off-screen: 2560x1440 first, then 2560x1080, 3440x1440 and 3840x2160. None has run yet.

The arrows for save 170 went through rounds 2, 3, 3b and 3c, with the credits fit alongside. Round 2 put the press numbers in fixed slots and a key beside every owed press. Round 3 made only one NOW show at a time. Round 3b fixed a RIGHT cue that sat top-left at 16:9 and a stunt 3 press that lost its WAIT tag. Round 3c fixed a wrong test assertion that the break-it review of 3b found. Every break-it review said GO with fixes or GO. On round 2, two fresh readers with no notes passed stunt 7 for the first time in four saves: all eight keys named, two RIGHTs in order, hold-to-cut separate. Save 170 is not saved yet; the whole stack still has to go through the chain, the lookers and the readers.

Next is the save 170 chain, the save word and the Legion gate, then the screen-size checks, then the logo and icon as save 171.

From 17:00 to 18:00, save 170 went in, with the arrows and the credits fit. It passed its picture checks: lookers at 16:10, 16:9 and 4:3 found no STOP, and two fresh readers with no notes were 9 of 9 on direction and key, with stunt 7 passing. One looker had flagged the crash retakes missing WAIT and NOW tags, so I had both re-shot before the save. The save script also had a slip: it failed the file check on later deltas, nothing was committed, the lead agent fixed it and saved at 17:38. Everything in it only changes drawing; nothing moves differently. A screen-size check at 2560x1440, 2560x1080, 3440x1440 and 3840x2160 found no STOP. It did find small items: tiny key letters on the wrap card at 2560x1080, a star badge that loses contrast on the white trailer, and the pause menu hints about 2000 px apart on the widest screen. Those go to the last polish pass. The 4K crash run captured only 6 stills, so that size is thinner than the rest.

Both packages of 170 were cut by 17:53 and its Legion gate started: keyboard stunt 7 was perfect, the gamepad run passed a touch late, and the other batches were running at 18:06. Save 171, the new logo and icon, passed its chain and its three lookers, but it is not handed out until a break-it review of the logo patch is weighed (none existed when I checked) and its own Legion gate passes. One frame of the logo, the exit from the title to HOW TO PLAY, was not sampled.

An Opus agent played the red-team judge on 170 from about 47 stills, with no motion and no sound. It scored about 17.5 of 35 (14.5 of 30 without audio). It said a crash on an empty striped pad leaves the car undamaged, so cutting can outscore driving, that the lane strip reads as cryptic glyphs, and that the world looks like a greybox. The arrows stay. The rules text and an E = STUNT row go to polish, and the scoring is locked, so that finding is my call. I asked at 17:27 to start prework on the polish: patches P1 and P2 are written by Opus agents and not yet in a build, and P3 has a brief and no author.

For the submission, the zip will be the Development build, because the rules say so. The video host is YouTube. I sent the music licence question to the fal support address myself at 17:43 and nothing has come back. A fallback with code-made music is ready but not applied. I decide by Sunday about 08:30 PT.

From 18:00 to 18:39, I answered a few cards. On the red-team's scoring finding I said "No, keep scoring", so scoring stays locked. The YouTube video will be Public. The game credits had lost the designer's name, and I said "Put my name back"; the line is "Design and direction: <the designer's name>. Code: Claude (AI)". The zip is named `SecondUnit_JumpCut.zip`. I also asked for seconds on the TV board countdown, going yellow and then red toward the deadline, and an agent built it (a pull request that was still open at 18:39).

Save 171, the new logo and icon, was saved at 18:04 and cut at 18:19. Its break-it review said GO and its exit look had no STOP, which closed the unsampled frame by code. It still needs its short Legion gate. Save 170's gate had three of four batches passed by 18:39. Two wander runs failed at first because the first arrow flips between done and live as the car changes lane while it wanders. An agent read the code and found that is by design, since the game checks the car's lane every frame, so the hub reworded the check: the arrows, keys and step count must not change, but the first step's state may follow the lane. The fourth batch was running on a fresh runner.

Save 172 (171 plus two Opus-written polish patches, P1 and its fixes D1) was applied to the live tree but not saved. Its chain was green at 18:31 (191 tests pass, 0 fail) and its stills were still being taken at 18:39. The credits-name patch and a reworked P2 are not saved and the credits-name patch is not yet compiled. P3 is written but untested. Submission prep has not started. The music licence still has no answer, and I decide by Sunday about 08:30 PT.

From 19:00 to 19:39, save 171 passed its full Legion gate and save 172 was saved. The 171 gate ran in two parts on two fresh runners: the first batch was clean, and the last row at 19:35 was a full pass with no STOP and nothing foreign on screen. The Explorer icon passed, and the running icon passed after one rerun, so Alt-Tab shows the new icon. One optional dev-only check was not seen. The test shortcut now points at the Shipping build of 171. Save 172 (171 plus P1 and its fixes D1) was saved at 19:35, with its chain green (191 tests pass, 0 fail) and no STOP at four desktop sizes and three aspects. The star under the score plate, the lighter STUNT plate and a charcoal ring round three key caps were accepted for this save only; the plate fix is owed and blocks the freeze. Its cut was still running at 19:39.

I told the hub I was signed in to PBRgen in my desktop Chrome and to use it as much as possible, so the game looks amazing, and I said I believe Unreal can handle complex materials. A Sonnet helper read the PBRgen terms (recorded as ok on the licence row) and started on five backlot material sets and then three car sets, using only credits the account already had. How far it got is not in the log. A wave-2 plan from an Opus agent, with six packages (UI spacing, effects, scenery, materials and lighting, water, paint), was accepted at 19:02. The scenery kit is done, with no AI: 8 kit types and 11 MB of the 60 MB budget. A water patch is in with its review started. Nothing from wave 2 is imported or built yet, and none of it has a performance number.

Six effect sheets were made with fal flux/schnell (16 calls, about $0.05). Three failed the looker and were rebuilt; at 19:39 Smoke and Splash passed and Dust still failed, so the helper went back to Dust alone. Nothing is imported until a fresh looker passes it, and the rebuilt sheets have not been tried in the engine. A records pull request merged at 19:31 with the PBRgen licence row and 29 asset log rows, 6 of them marked generated but not imported.

The hub accepted a freeze list of nine switches, with rulings on each. The build type is still open: the freeze review leans toward the smaller Shipping zip (412.1 MB against 478.6 MB), but that reverses my own earlier "dev mode it is", so it comes to me on one card and nothing changes until I answer. The zip proof on the stage zip has not run. Master control passed from hub 187 to hub 188 at 19:24, and a new lead agent started at about 19:37. The schedule of imports and saves 175 to 177 overnight is an estimate, and any package not imported by 23:30 does not ship.

From 19:40 to 22:13, save 172 went through its full Legion gate and passed at about 22:09: four batches, a hand-run rerun and a test of the DIRECTOR'S CUT pad that reloads the scene with a cut stunt back. Before that, a Shipping hand run showed no wrap card because the test driver pressed the retake keys about half a second early; that was a bug in the test, not the game, and it was fixed for the next runner. At 19:48 I answered "shipping build", so the jam zip is the Shipping build; Shipping writes no log, which means a crash on a judge's machine would leave nothing to read.

I told the hub to use the Meshy and Rodin credits, named the team jf1shh, and said Meshy has to go through its web page in Chrome (the API refused with HTTP 402). Seven props were picked, four from Meshy and three from Rodin. The Rodin licence depends on a paid plan I still have to confirm before I submit. I clicked my Fable reset and bought $100 of usage credits at about 20:43; the reset gave back 35 points of the weekly limit, and I told the hub to stay on Fable and give each job to the cheapest model that fits. Five planned saves were folded into three. Save 175 had no stop at any screen size, the new water stayed on after a 12-pair look against 173 (2 better, 10 same, 0 worse), and flames showed up once a dedicated shot was taken; its save word came just after 22:05. The scenery props (B) failed their scratch import, so they are out of the last import and out of save 177. At 21:52 to 21:56 I ordered the star icon moved and then "remove all boxes": solid icons and text with drop shadows, behind a switch with fallbacks, for save 177. After 22:05 I asked about stopping all tests (the hub kept them running behind the polish), named three UI references and asked for a small settings menu if it fits. Not done at 22:13: the 175 Legion gate, import job 2 and save 177. Time and cost figures in the log are estimates.

[AFTER Nov 14: agents fill the rest that evening from the build ledger: why the ship candidate was frozen at 5 PM PT (after that, bug fixes only), and what the handheld showed on the last pass.]

## Sun Nov 15 (day 4, to 5:59 PM PT)

- Checks on the save 179 build (23:13 Saturday to 00:25 Sunday PT), all by AI helpers: one screen looker over eight screen sizes and both icon fallback levels, with no stop; a water A/B against save 175 (the walled ford reads better); three fresh readers with no game context, who read the end card the same as before; and a settings test on the live build (music off is saved and a new boot starts with it off; music on brings the volume back).
- The owner's words, verbatim: "i think we need to remove most if not all of the boxes and use icons that look cool instead" and "i mean not transparent just shadows so you can still see them" (typed Saturday 21:47 to 21:56 PT); "oh yeah wow we need a settings menu probably if we can fit it" (Saturday, about 22:10 PT); "no it looks good proceed" (on the preview stills; the wrap card ships with no panel behind it).
- 04:06 PT: the film-set backlot props were in no build until now. Two causes (a mesh clean-up step and a sand-reach sample) are fixed in save 183, and the game's own log now places 246 props. The Legion test is running; no result yet. Save 182 stays the ship candidate. An art kit of 28 pictures was drawn in code.
- 04:57 PT: save 183 passed its one Legion test and is the ship candidate. The game's log places 246 props. On the handheld it runs about 1 ms a frame (5 %) slower than save 182.

[AFTER Nov 15: agents fill this from the build ledger: the last bug fixes, the final test result, the final video capture, and the time you pressed Submit.]

[OWNER-FILL card 2: the last day before submitting, in your words (interview Q4, asked about 16:15 PT Sunday).]

[IMAGE from the final capture: the THAT'S A WRAP card with PLAY THE DIRECTOR'S CUT]

## What AI made and what it didn't

What AI made:
- The director's 17 short voice lines, such as "CUT!" and "That's a wrap!" (Google Gemini text-to-speech, through fal).
- Music generated with ElevenLabs Music (via fal.ai) (2 tracks).
- The 11 HUD icons, written as vector (SVG) code by a Claude Sonnet helper.
- One more prop, a second water tower, from Hyper3D Rodin, also from a concept image. You see it beside the road in Scene 1.
- The game code and editor set-up (Claude, through Claude Code and Epic's Unreal MCP plugin).
- Concept images for sets, props and the hero car (FLUX.1 [schnell], on fal). These are labelled concept art. One more FLUX image ships in the game: a city-skyline backdrop texture, edited afterwards by script. The cover and banner start from one of them. The recolour to a cream car, the title and the text are done by script.
- Six 3D prop meshes (studio light, clapper sign, barrel, water tower, prop truck, camera crane) in Meshy, from concept images, using the jam's partner credits. Five of them are placed in the game's two scenes: the studio light, barrel, water tower, prop truck and camera crane. More props were started the same way.
- The hero car you drive, also from a concept image, in Meshy. I picked it from the candidate cars on Nov 12.

![Model render, not an in-game shot: the Meshy hero car from the side, cream with red stripes](devlog-img/hero_car_meshy_side_render.png)
*Model render (Blender), not a game screenshot. In-game shots come from the next test build.*

![Model render, not an in-game shot: the Meshy hero car from behind, at the game's chase-camera angle](devlog-img/hero_car_meshy_chasecam_render.png)
*Same car from the game's chase-camera angle, in the game's lighting. Also a Blender model render.*

- The design specs, the test runs, and the first drafts of this page.

What AI did not make:
- The 38 sound effects: scripts I had the agents write generate them with plain math. The 4 interface sounds come from Kenney's free CC0 pack.
- The decisions: concept, cover, what ships and what to cut from scope were mine.
- The playtesting by hand, and the submission.

Tried and left out:
- Before the window, Cursor's built-in image tool (it reports no model name) made the 17 pre-jam reference pictures for the prep pack. Each is marked "PRE-JAM REFERENCE, NOT A GAME ASSET"; none is in the game or on this page.
- I tried GPT image once for concept images. It returned nothing, and I use none of it.
- No local AI models ran during the jam.

A correction: an earlier version of my notes said Rodin made the prop meshes. That was wrong. Meshy made six of the seven, and the one Rodin mesh, a second water tower, is in the game.

## What was hard, and what I'd do differently

The hardest part is always thinking I should be doing more, or orchestrating better. The AI agent playtest surprised me by memorizing the first level.

[OWNER-FILL card 2: two or three honest lines. Ideas to react to: the Windows compile check should have existed on day one; a long package on a handheld is a slow way to find a naming bug; how you split work between agents.]
