#!/usr/bin/env python3
"""Fetch MAST-Data rows by offset and split each into links with the readings' own splitter.

    python3 -I -B convert_mast.py <download_dir> <runs_dir> <offset> [<offset> ...]

<download_dir> must be empty or new: each row lands there as row<offset>.json, untouched. Each run folder in
<runs_dir> gets links.jsonl from studies/public-readings/mast/build/extract.py, run unchanged with -I -B
(the splitter is reused, not rewritten). The trajectory's sha256 is printed beside the one the readings recorded.
GET only, `curl -q`, a neutral User-Agent, nothing sent but the URL.
"""
import hashlib, json, os, subprocess, sys

HERE = os.path.dirname(os.path.abspath(__file__))
EXTRACT = os.path.join(HERE, "..", "public-readings", "mast", "build", "extract.py")
URL = "https://datasets-server.huggingface.co/rows?dataset=mcemri/MAST-Data&config=default&split=train&offset={}&length=1"
UA = "Mozilla/5.0"
# offset -> (run folder, sha256 of trace.trajectory), from studies/public-readings/mast/README.md
KNOWN = {0: ("t01-chatdev-checkers", "8af11f42b1afe38165b65744585f51809e96bddf48d49e738ab5255ec1033d9d"),
         30: ("t02-metagpt-checkers", "1658259d3e20163834204f54497f146f890d59bd290e9e2cb49fb9d7e0cd39d7"),
         1: ("t03-chatdev-sudoku", "ee9f14a34a1c17aa01d90c77536cf83a37edb4a2267bac366cca29d73b948180"),
         31: ("t04-metagpt-sudoku", "108cb8094676ad1dd4cc761fd1cafe45b3165e50eaf7b74078b25b8ca3cd4e90"),
         180: ("t05-hyperagent-xarray-4493", "6353286d6d398c8c9eeb2420a0746adbef7f42e2e4fbbec918818f5ad3864b76"),
         181: ("t06-hyperagent-matplotlib-25433", "6f99194cd51e884946abd0fe4a6cf8bf9162ac81b922ee7670fb75a09fa04efa"),
         182: ("t07-hyperagent-matplotlib-18869", "b5e721bc1b73833aff6dee403ad83288c3518d2b8af408a4f6f9d8ff7e58cea9"),
         571: ("t08-ag2-olympiad-0", "9187efc1079cc6eff854371c9132a68d6f4d27d634332270236ba587a34bb488"),
         572: ("t09-ag2-olympiad-1", "de146fa6bb2c0c350740b14659ee79309b3340838ed20881db8d5c54a5885da2"),
         573: ("t10-ag2-olympiad-2", "5283fe4e150a04c6250c1e7253e0fbcca36e4a63afc5bce393eb8f3170a55fec")}


def main(argv):
    if len(argv) < 3:
        print(__doc__, file=sys.stderr)
        return 2
    dl, runs, offsets = os.path.abspath(argv[0]), os.path.abspath(argv[1]), [int(x) for x in argv[2:]]
    os.makedirs(dl, exist_ok=True)
    if os.listdir(dl):
        print(f"{dl} is not empty: downloads go into their own empty folder", file=sys.stderr)
        return 2
    for off in offsets:
        name, want = KNOWN.get(off, (f"mast-row{off}", None))
        row = os.path.join(dl, f"row{off}.json")
        subprocess.run(["curl", "-q", "-sS", "-f", "-A", UA, "-o", row, URL.format(off)], check=True)
        traj = json.load(open(row, encoding="utf-8"))["rows"][0]["row"]["trace"]["trajectory"]
        got = hashlib.sha256(traj.encode("utf-8")).hexdigest()
        scratch = os.path.join(runs, "_scratch", name)
        subprocess.run([sys.executable, "-I", "-B", EXTRACT, row, os.path.join(runs, name), scratch], check=True,
                       stdout=subprocess.DEVNULL)
        print(f"{off}\t{name}\t{'hash matches the readings' if got == want else 'hash ' + got[:12] + (' DIFFERS' if want else ' (no recorded hash)')}")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
