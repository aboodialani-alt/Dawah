# Overnight work, 8 October 2026

Everything here is separate from your live work. Your original DA and the original board are untouched. Nothing was posted or published to anyone. All three artifacts are private to you.

## Open these first

| What | Link | Why open it |
|---|---|---|
| **DA Next** (redesigned library) | https://claude.ai/artifact/WJXJPTBJz7NazA5Rh6Uqap | Start here. Paste an attack into the big box on the front page. Press `/` anywhere to search. |
| **Studio Board** (redesigned flow) | https://claude.ai/artifact/QwPSGhfMwvpR2NUdnvtrww | Overview, Pipeline, Claims, Style lab, Accounts. The Style lab is the answer to "define Style B and C". |
| Original DA (unchanged) | https://claude.ai/artifact/CkgK9pwT8k1VKn1mWbkqF4 | For comparison. |
| Original board (unchanged) | https://claude.ai/artifact/L9eDUUn5eEz7dWt1DBu8db | For comparison. |

## What is new in DA Next

- **Attack finder** on the front page: paste what they said, get the objection the library already answers, with the verified reply. 329 attacks are indexed.
- **Command palette** on every page (`/` or Ctrl/Cmd+K).
- **Study tracks**: five ordered paths (hadith, prophethood, Quran preservation, modern attacks, debater's toolkit). I picked the steps by title, so check the order suits you.
- **Per-argument tools**: queue for video, copy brief, copy link, and "Draft a reel" (Claude writes a script in Style A, B or C using only that argument's own text, then lists every claim it used).
- **Reading modes**: Skim (thesis and one-breath only), Full, Drill (attacks first, answers hidden).
- **Attacks and answers as a conversation** instead of a list.
- **Drill room**: 570 cards (329 attacks, 241 practice prompts) with spaced repetition. You can type your answer and have Claude grade it against the model answer.
- **Review desk**: the six drafted additions and your three open questions. Accept, decline or request changes on each. The decisions are saved to the shared database so I can apply exactly what you chose.
- **Video queue**: arguments you line up for reels. Shared, so I can read it and plan from it.
- **Citation audit** (new page, linked from the front page): all 259 hadith references in the library looked up in the open dataset by number, set against the library's sentence, with each grader's verdict. 15 have graders who disagree (for example Tirmidhi 3194, 2733 and 113) and 2 are graded weak by every grader listed (Nasa'i 3269 and Tirmidhi 3620, the Bahira story, graded munkar). It is a lookup, not a ruling, and Bukhari and Muslim carry no grade in the dataset. `audit.py` regenerates it. The same page also checks all 153 Arabic Quran quotations against the Uthmani text: 105 match word for word, 42 differ only by modern spelling or by quoting part of a verse, and none has different words.
- **Reviewer note layer**: the Mongols and Baghdad entry carries a note that its identification of Baghdad is an interpretation and that three details were unverified. The library text itself is not changed.
- Light and dark themes, phone layout, keyboard keys on part pages: `j` and `k` move between arguments, `x` marks studied, `q` queues.

The text of all 252 arguments is exactly as in your DA. Only the presentation and the new tools were added.

## What is new in Studio Board

- **Overview**: both fronts as a six-stage belt, "Needs you" decisions, what Claude did, results chart by script style, weekly rhythm ring.
- **Pipeline**: drag cards between stages or use the buttons. Each video card has results fields (views at 48h, likes, saves, shares, comments, followers) and two Claude buttons: hook ideas, and an objection check.
- **Claims radar**: every attack worth answering, with priority and the library argument that answers it. **Intake**: paste a transcript or post and Claude extracts the claims, matches each to a library argument, and flags **library gaps** (claims the library cannot answer yet).
- **Style lab**: Styles A, B and C with reel anatomy bars, second-by-second beats, rules and the evidence behind each.
- **Accounts**: the eight accounts with Meedro numbers and a fit rating from me.

## What the Meedro analysis found (16 reels read in full, 24 Ali Amery reels, 100 recent titles)

- Of 16 reels analysed, 8 were split-screen formats: median 3.7x outlier score, including the top reel (6.0x) and 5 of the top 10.
- Talking-head reels had a median of 4.5x, but they are mostly personal stories and one skit, and several carry a call to action. They do not fit your no-call-to-action rule.
- Ali Amery: reels of 2.5 minutes or less score about twice as well as reels over 6 minutes. Most of his reels are long.
- Question hooks with the same line in capitals on screen appear in several of the best reels from @korrathetaymi and @bro_yusuf_11.
- A 10-second skit on "hadith acceptors" got 5.0x. Humor on your topic works when it is short.
- The strongest English reference, @orthodoxmuslim, opens its best reels (65 to 98 seconds, 8x to 11x) with a **specific demand for evidence** ("is there anybody in the first 200 years who...") over a split screen with a capitals topic label. Its titles also use mocking frames ("GETS SILENCED", "CAUGHT", "GOT COOKED"). Style B takes the structure and drops that tone.
- Full per-reel data is in `style-data/reels.json`.

All of this is a small sample read from titles and Meedro's own breakdowns. It is a hypothesis until your own 48-hour numbers confirm it.

## First two script drafts (ready to review, not recorded)

- `scripts/B1-hadith-written-early.md`: English, Style B, about 58 seconds. "Who was writing hadith while the Prophet ﷺ was alive?"
- `scripts/A1-hadith-muslim-3004-ar.md`: Arabic, Style A, about 2 minutes. Reads the whole of Muslim 3004, including the half critics leave out, then ends on a dilemma for critics who reject hadith.

Both quote only references I checked against the open hadith dataset, give the exact wording, and carry an objection check. Both need a real clip or post from the person making the claim. I also found that the library's own Hammam figures (138 and 98) and "whole Sahifa in the Musnad" could not be confirmed, so the DA entry now carries a reviewer note.

- `scripts/B2-romans-prophecy.md`: English, Style B, about 58 seconds, for "Is Muhammad ﷺ a true prophet?". Quran 30:2-4 and Gibbon verified. It also found that the library's "Issus 622" and the wager hadith need care (reviewer note added).

## Decisions waiting for you

1. Hijab entry: your stance on state enforcement (Review desk).
2. Mongols and Baghdad entry: demote to "use with care", or keep with corrected wording (Review desk).
3. Regenerate the nine library PDFs when the library is republished?
4. Delete `videos/` (the Baghdad draft work)? I have not touched it.
5. First script style (B or C) and first topic.

## Credits

Meedro credits went from 35,570 to 35,074, so 496 were used: six accounts added to the watchlist (300), 22 reels analysed (154), and 42 I cannot account for, probably from a batch you rejected. Everything else I did was free stored data.

## What I could not check

- An end-to-end test (`overnight/da-v2/test/e2e.mjs`) ran 22 checks across the pages with stubbed services: queue, draft dialog, reading modes, finder, tracks, drill, review decisions, audit filters. All passed (the one reported failure was a test comparing text that the page shows in capitals, and the decision itself saved correctly).
- I cannot open the published pages in a browser here. I tested every page with a stubbed database and a stubbed Claude in a headless browser, at desktop and phone widths, light and dark. The calls to Claude ("Draft a reel", drill grading, intake, hook ideas) and the shared database were not run for real, so the first time you press them is the real test.
- Wake subscriptions for the two new artifacts did not register, so I will not be woken by edits or comments on them.
- The weekly Monday sweep routine is unchanged. It cannot write into the Studio Board yet. Doing that is a small change to its prompt if you want it.

## Rebuild

- DA Next: `python3 -I overnight/da-v2/extract.py <original pages> overnight/da-v2/site` then `python3 -I overnight/da-v2/build.py <original pages> overnight/da-v2/site`. The original pages come from the live DA artifact.
- Board: `python3 -I overnight/board-v2/build_board.py`.
- Test harness: `node overnight/da-v2/test/shot.mjs <site dir> <out dir> <page>`.

## Ideas not built yet

- An Arabic version of the attack finder and drill room for the Arabic front.
- A "reel anatomy" overlay that shows a draft script against the Style B or C timeline.
- Letting the Monday sweep write new claims straight into the Studio Board.
- A new DA argument for each library gap the intake finds.
- Re-analysing the same accounts in a month to see how the styles drift.
