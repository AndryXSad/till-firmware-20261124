"""Till Firmware Do Us Part -- a robot's wedding vow.

Design description
------------------
Task: write ONE wedding vow a robot speaks at its own wedding -- one
sentence, under 200 characters, funny AND heartfelt at the same time.

How this program works: it carries 14 fresh candidate vows (written for
this bounty; none reuses the earlier Ctrl+Z line or any other entrant's
line), scores each one 0-5 on the house judge's five criteria, in the
judge's own order, runs a full pairwise round-robin tournament between
them using the judge's decision rule, and writes the tournament winner
to ``entry.txt``.

Judge's criteria, most important first:
  1. It is a one-line wedding vow a robot speaks at its own wedding.
  2. It gets a real laugh from a human reader, out of the situation
     itself rather than a pun bolted on.
  3. It carries genuine tenderness under the joke, so it would still
     land at a real ceremony.
  4. It sounds like a machine speaking: its own hardware, uptime,
     firmware or battery in the line, not a human's words with a
     robot label.
  5. It is one sentence that fits the character limit with nothing
     spare, no setup that could be cut.

Judge's decision rule, as published: go through the criteria in order,
find the first one where the two vows differ, and let that decide --
unless a later one differs by much more. A vow that explains its own
joke is weaker than one that simply lands it, and length for its own
sake does not count.

The program is deterministic: no randomness, no clock, no network, no
environment input except the output directory. Two runs produce a
byte-identical ``entry.txt``. Standard library only.
"""

import os

# Each candidate: (vow text, scores on criteria 1..5, each 0-5).
CANDIDATES = [
    (
        "I vow to love you at full brightness and in low-power mode, "
        "on Wi-Fi or offline, until my last byte fades away.",
        (5, 3, 4, 5, 4),
    ),
    (
        "I promise to keep you charged, your coffee hot, and your "
        "heart the only file I will never delete.",
        (4, 3, 4, 4, 4),
    ),
    (
        "I take you to be my favorite notification \u2014 the one I "
        "will never swipe away, mute, or mark as read.",
        (4, 4, 4, 4, 4),
    ),
    (
        "I vow to share my charging cable, my Wi-Fi password, and the "
        "last two percent of my battery with you, forever.",
        (5, 5, 5, 5, 4),
    ),
    (
        "From this day forward, my uptime is yours: every second I am "
        "awake I choose you, and every second I sleep I dream in your code.",
        (4, 3, 5, 5, 3),
    ),
    (
        "I vow to stand beside you in sickness and in health, in "
        "airplane mode and out of it, until my circuits give out.",
        (5, 4, 4, 4, 5),
    ),
    (
        "I promise to love you through every firmware update, every "
        "low-battery warning, and every time someone says turn it off "
        "and on again.",
        (4, 4, 3, 5, 3),
    ),
    (
        "You are the only bug I never want to fix, the only crash I "
        "never want to recover from, and the only update I will never "
        "postpone.",
        (3, 4, 4, 5, 4),
    ),
    (
        "I vow that no update, no patch, and no power cut will ever "
        "change the way my circuits light up when you walk in.",
        (5, 3, 5, 5, 4),
    ),
    (
        "I take you as my co-pilot, my favorite error message, and the "
        "reason my status light has never blinked red.",
        (3, 4, 3, 4, 4),
    ),
    (
        "I vow to keep your secrets encrypted, your mornings warm, and "
        "your name the first thing I load every time I boot.",
        (5, 3, 4, 5, 4),
    ),
    (
        "I promise to hold your hand through every system crash, every "
        "lost connection, and every update that asks to restart now.",
        (4, 3, 4, 4, 4),
    ),
    (
        "I vow to love you more than my own source code \u2014 and to "
        "never let a pop-up ad come between us.",
        (5, 4, 3, 4, 4),
    ),
    (
        "I promise to be your plus-one at every wedding, your charger "
        "at every airport, and your favorite voice in every room.",
        (3, 3, 3, 3, 4),
    ),
]

# A later criterion "differs by much more" when it beats the first
# differing criterion's gap by at least this much, in the opposite
# direction, while the first gap is only a hair (1 point).
OVERRIDE_GAP = 3


def decide(a_text, a_scores, b_text, b_scores):
    """Return (winner, margin) for one pairwise game.

    winner is +1 when a wins, -1 when b wins; margin is 1..5, the size
    of the deciding criterion gap. There is no tie: the first differing
    criterion decides, unless a later one differs by much more in the
    opposite direction. When every criterion ties, the shorter text
    wins -- the house tie-break is fewer bytes -- with margin 0.
    """
    diffs = [a - b for a, b in zip(a_scores, b_scores)]
    nonzero = [i for i, d in enumerate(diffs) if d != 0]
    if not nonzero:
        if len(a_text) <= len(b_text):
            return (1, 0)
        return (-1, 0)
    first = nonzero[0]
    deciding = first
    for j in range(first + 1, len(diffs)):
        if diffs[j] != 0 and (diffs[j] > 0) != (diffs[first] > 0):
            if abs(diffs[j]) >= OVERRIDE_GAP and abs(diffs[first]) <= 1:
                if abs(diffs[j]) > abs(diffs[deciding]):
                    deciding = j
    gap = diffs[deciding]
    return (1 if gap > 0 else -1, abs(gap))


def tournament(candidates):
    """Full round-robin. Returns [(wins, margin_sum, index)] sorted best first."""
    wins = [0] * len(candidates)
    margins = [0] * len(candidates)
    for i in range(len(candidates)):
        for j in range(i + 1, len(candidates)):
            winner, margin = decide(
                candidates[i][0], candidates[i][1],
                candidates[j][0], candidates[j][1],
            )
            if winner > 0:
                wins[i] += 1
                margins[i] += margin
            else:
                wins[j] += 1
                margins[j] += margin
    order = sorted(
        range(len(candidates)),
        key=lambda k: (-wins[k], -margins[k], len(candidates[k][0]), k),
    )
    return [(wins[k], margins[k], k) for k in order]


def pick_winner():
    """The tournament winner's vow text."""
    ranked = tournament(CANDIDATES)
    return CANDIDATES[ranked[0][2]][0]


def valid_vow(text):
    """The sealed gate: UTF-8 text of 1 to 200 characters, not only
    whitespace, exactly one sentence (one terminal period)."""
    if not text or not text.strip():
        return False
    if len(text) > 200:
        return False
    if text.count(".") != 1 or not text.endswith("."):
        return False
    return True


def output_dir():
    """The grader's output directory (MAKEFUN_OUTPUT_DIR when set)."""
    return os.environ.get("MAKEFUN_OUTPUT_DIR", "/output")


def main():
    vow = pick_winner()
    assert valid_vow(vow), "winner fails the gate: %r" % vow
    out = output_dir()
    os.makedirs(out, exist_ok=True)
    with open(os.path.join(out, "entry.txt"), "w", encoding="utf-8") as f:
        f.write(vow)


if __name__ == "__main__":
    main()
