"""Collect the early-memtest results of every boot in the systemd journal and summarise them.

    python3 analyse.py            (needs read access to the kernel journal; no root needed on this machine)

Writes all_boots.json, summary.json and kernel_boot_times.json next to this file.
"""
import collections, json, pathlib, re, statistics, subprocess

HERE = pathlib.Path(__file__).resolve().parent
PAGE = 4096

def jc(*args):
    return subprocess.run(["journalctl", "--no-pager", *args], capture_output=True, text=True).stdout

boots = json.loads(jc("--list-boots", "-o", "json"))
per, times = {}, []
for b in boots:
    out = jc("-k", "-b", b["boot_id"], "-o", "short-iso")
    tests = re.search(r"early_memtest: # of tests: (\d+)", out)
    bad = re.findall(r"([0-9a-f]{16}) bad mem addr (0x[0-9a-f]+) - (0x[0-9a-f]+) reserved", out)
    per[b["index"]] = {"date": out[:19], "tests": int(tests.group(1)) if tests else 0,
                       "bad": [(p, int(a, 16), int(e, 16)) for p, a, e in bad]}
    fin = jc("-b", b["boot_id"], "-t", "systemd", "-g", "Startup finished in")
    line = next((l for l in fin.splitlines() if "(kernel)" in l), "")
    m = re.search(r"(?:(\d+)min )?([\d.]+)(ms|s) \(kernel\)", line)
    if m:
        sec = (int(m.group(1) or 0) * 60) + float(m.group(2)) / (1000 if m.group(3) == "ms" else 1)
        times.append((b["index"], bool(tests), sec))
(HERE / "all_boots.json").write_text(json.dumps(per, indent=1))
(HERE / "kernel_boot_times.json").write_text(json.dumps(times))

tested = sorted((k, v) for k, v in per.items() if v["tests"])
counts, patterns, rows = collections.Counter(), collections.Counter(), []
for k, v in tested:
    words = set()
    for p, a, e in v["bad"]:
        patterns[p] += 1
        words.update(range(a, e, 8))
    counts.update(words)
    rows.append((k, v["date"][:10], words))
pages = sorted({w // PAGE for w in counts})
summary = {
    "n_boots_tested": len(tested), "n_boots_untested": len(per) - len(tested),
    "pages": [hex(p * PAGE) for p in pages],
    "distinct_bad_words": len(counts),
    "bad_on_every_boot": sum(1 for c in counts.values() if c == len(tested)),
    "bad_exactly_once": sum(1 for c in counts.values() if c == 1),
    "distinct_bad_words_per_page": {hex(p * PAGE): sum(1 for w in counts if w // PAGE == p) for p in pages},
    "ranges_by_pattern": dict(patterns),
    "boots": [{"idx": k, "date": d, "words": len(w), "per_page": [sum(1 for x in w if x // PAGE == p) for p in pages]} for k, d, w in rows],
    "boots_missing_a_page": [d for k, d, w in rows if any(not any(x // PAGE == p for x in w) for p in pages)],
    "words": {hex(w): c for w, c in sorted(counts.items())},
}
on = [s for _, t, s in times if t]; off = [s for _, t, s in times if not t]
summary["kernel_start_median_s"] = {"with_memtest": statistics.median(on) if on else None, "n_with": len(on),
                                    "without": statistics.median(off) if off else None, "n_without": len(off)}
(HERE / "summary.json").write_text(json.dumps(summary, indent=1))
print(json.dumps({k: v for k, v in summary.items() if k not in ("words", "boots")}, indent=1))
