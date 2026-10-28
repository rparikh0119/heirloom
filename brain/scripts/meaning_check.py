"""How well does Heirloom understand phrasings nobody typed in? Run on your PC (no headset, no mic):

    python scripts/meaning_check.py
    python scripts/meaning_check.py --file my_lines.txt     # your own sentences, one per line:
                                                            #   hey you   | wave
                                                            #   what time is it  | huh
                                                            # blank lines and lines starting with # are skipped

Each sentence below is NOT in intents.py word for word. It prints what the droid would understand,
how sure it was, and a score. Add your own sentences to TRY. If too much lands as "huh?", lower
ACCEPT in heirloom/perception/meaning.py. If it understands things wrongly, raise it.
"""
import argparse
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from heirloom.perception.intents import match  # noqa: E402
from heirloom.perception.meaning import ACCEPT, MARGIN, Meaning  # noqa: E402

TRY = [
    # (what someone might say, what it should mean, or None = should ask "huh?")
    ("hey there little guy", "wave"),
    ("good morning sunshine", "wake"),
    ("long time no see", "wave"),
    ("you're such a good little robot", "good"),
    ("I'm so proud of you", "good"),
    ("that was perfect", "good"),
    ("nice one buddy", "good"),
    ("I adore you", "heart"),
    ("you mean the world to me", "heart"),
    ("give me a minute", "not_now"),
    ("I need some space right now", "not_now"),
    ("can you be a little quieter", "shh"),
    ("time for bed little guy", "sleep"),
    ("go take a nap", "sleep"),
    ("rise and shine buddy", "wake"),
    ("come over to me", "curious"),
    ("look what I've got", "curious"),
    ("I'm sorry I yelled", "sorry"),
    ("my apologies", "sorry"),
    ("you're so annoying", "offended"),
    ("get lost", "offended"),
    ("knock that off", "scold"),
    ("show me something from before", "show_memory"),
    ("do you remember that day", "show_memory"),
    ("snap a shot of this", "take_photo"),
    ("let me hear that recording", "play_memory"),
    ("head back to your spot", "go_home"),
    # things it should NOT pretend to understand
    ("what's the weather like", None),
    ("did you finish the assignment", None),
    ("pass me the remote", None),
    ("I don't love you", None),
]


def _read(path: str) -> list[tuple[str, str | None]]:
    """'hey you | wave' -> ('hey you', 'wave'). 'huh', 'none' or nothing after | -> None (should ask "huh?")."""
    out = []
    for n, line in enumerate(Path(path).read_text(encoding="utf-8").splitlines(), 1):
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        if "|" not in line:
            raise SystemExit(f"{path} line {n}: write it as  sentence | event   (got {line!r})")
        said, want = (x.strip() for x in line.split("|", 1))
        out.append((said, None if want.lower() in ("", "huh", "none", "huh?") else want))
    return out


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--file", default=None, help="your own sentences: one 'sentence | event' per line")
    args = ap.parse_args()
    tries = _read(args.file) if args.file else TRY
    t = time.perf_counter()
    m = Meaning()
    print(f"Model ready in {time.perf_counter() - t:.1f} s.  ACCEPT {ACCEPT}  MARGIN {MARGIN}\n")
    right = 0
    for said, want in tries:
        exact = match(said, loose=True)[1]
        t = time.perf_counter()
        got, sure = (exact, 1.0) if exact else m.understand(said)
        ms = (time.perf_counter() - t) * 1000
        how = "exact" if exact else f"{sure:.2f}"
        ok = got == want
        right += ok
        top = "  ".join(f"{e} {s:.2f}" for e, s in m.scores(said)[:3])
        print(f"  {'ok ' if ok else 'NO '} {said!r:42} -> {str(got or 'huh?'):12} ({how}, {ms:.0f} ms)   top: {top}")
    print(f"\n{right}/{len(tries)} as expected")


if __name__ == "__main__":
    main()
