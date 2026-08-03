#!/usr/bin/env python3
"""JLCPCB export CLI for the analog_NN board.

Generates the two files JLCPCB assembly needs, straight from the KiCad design:

  * BOM  (Comment, Designator, Footprint, LCSC Part #)   -- grouped
  * CPL  (Designator, Mid X, Mid Y, Layer, Rotation)     -- pick & place

Coordinates and rotations come from `kicad-cli pcb export pos` (the authoritative
KiCad placement engine). LCSC part numbers, canonical comments, assemble flags and
per-part rotation offsets come from jlc_parts.csv (edit that file, not this script).

Usage:
    python3 export_jlc.py                 # generate BOM + CPL into ./out
    python3 export_jlc.py --check         # report unmapped parts, write nothing
    python3 export_jlc.py --out-dir dist  # choose output directory

Run with -h for all options.
"""
from __future__ import annotations

import argparse
import csv
import os
import re
import subprocess
import sys
import tempfile
from collections import defaultdict

HERE = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.dirname(HERE)
DEFAULT_PCB = os.path.join(PROJECT_ROOT, "analog_NN.kicad_pcb")
DEFAULT_PARTS = os.path.join(HERE, "jlc_parts.csv")
DEFAULT_OUT = os.path.join(HERE, "out")
PROJECT_NAME = "analog_NN"

# Gerber layers to plot for a 4-layer board (F.Cu, In1.Cu, In2.Cu, B.Cu).
GERBER_LAYERS = ("F.Cu,In1.Cu,In2.Cu,B.Cu,F.Paste,B.Paste,"
                 "F.SilkS,B.SilkS,F.Mask,B.Mask,Edge.Cuts")

# kicad-cli locations to try if not on PATH / not overridden.
KICAD_CLI_CANDIDATES = [
    "kicad-cli",
    "/Applications/KiCad/KiCad.app/Contents/MacOS/kicad-cli",
    "/usr/bin/kicad-cli",
    "/usr/local/bin/kicad-cli",
]


class Part:
    """One row of jlc_parts.csv."""

    __slots__ = ("value", "package", "comment", "lcsc", "jlc_class",
                 "assemble", "rot_offset", "notes")

    def __init__(self, row: dict):
        self.value = row["match_value"].strip()
        self.package = row["match_package"].strip()
        self.comment = row["comment"].strip()
        self.lcsc = row["lcsc"].strip()
        self.jlc_class = row["jlc_class"].strip()
        self.assemble = row["assemble"].strip().lower() in ("yes", "y", "true", "1")
        off = row["rot_offset"].strip() or "0"
        self.rot_offset = float(off)
        self.notes = row.get("notes", "").strip()

    def matches(self, val: str, package: str) -> bool:
        if not package.startswith(self.package):
            return False
        return self.value == "*" or self.value == val


def find_kicad_cli(override: str | None) -> str:
    candidates = [override] if override else KICAD_CLI_CANDIDATES
    for cand in candidates:
        if not cand:
            continue
        if os.path.sep in cand:
            if os.path.isfile(cand) and os.access(cand, os.X_OK):
                return cand
        else:
            from shutil import which
            found = which(cand)
            if found:
                return found
    sys.exit(
        "error: kicad-cli not found. Install KiCad 8/9 or pass --kicad-cli PATH.\n"
        "  (tried: %s)" % ", ".join(c for c in candidates if c)
    )


def load_parts(path: str) -> list[Part]:
    parts: list[Part] = []
    with open(path, newline="") as fh:
        # Skip leading comment lines (start with '#') before the header.
        lines = [ln for ln in fh if not ln.lstrip().startswith("#")]
    reader = csv.DictReader(lines)
    for row in reader:
        if not (row.get("match_package") or "").strip():
            continue
        parts.append(Part(row))
    if not parts:
        sys.exit(f"error: no part rows found in {path}")
    return parts


def run_pos_export(kicad_cli: str, pcb: str) -> list[dict]:
    """Return per-component placement rows from kicad-cli pcb export pos."""
    with tempfile.TemporaryDirectory() as tmp:
        out = os.path.join(tmp, "pos.csv")
        cmd = [kicad_cli, "pcb", "export", "pos",
               "--format", "csv", "--units", "mm", "--side", "both",
               "-o", out, pcb]
        proc = subprocess.run(cmd, capture_output=True, text=True)
        if proc.returncode != 0:
            sys.exit(f"error: kicad-cli pos export failed:\n{proc.stderr}")
        with open(out, newline="") as fh:
            return list(csv.DictReader(fh))


def export_gerbers(kicad_cli: str, pcb: str, out_dir: str) -> str:
    """Plot Gerbers + Excellon drill (absolute origin, matching the CPL) and zip them.

    Returns the path to the zip. Absolute drill origin keeps the fab files aligned
    with the CPL, which also uses KiCad's page origin.
    """
    import zipfile

    gdir = os.path.join(out_dir, "gerbers")
    if os.path.isdir(gdir):
        for f in os.listdir(gdir):
            os.remove(os.path.join(gdir, f))
    os.makedirs(gdir, exist_ok=True)

    gcmd = [kicad_cli, "pcb", "export", "gerbers", "--no-protel-ext",
            "-l", GERBER_LAYERS, "-o", gdir, pcb]
    proc = subprocess.run(gcmd, capture_output=True, text=True)
    if proc.returncode != 0:
        sys.exit(f"error: kicad-cli gerbers export failed:\n{proc.stderr}")

    dcmd = [kicad_cli, "pcb", "export", "drill", "--format", "excellon",
            "--drill-origin", "absolute", "--excellon-units", "mm",
            "--generate-map", "--map-format", "gerberx2", "-o", gdir + os.sep, pcb]
    proc = subprocess.run(dcmd, capture_output=True, text=True)
    if proc.returncode != 0:
        sys.exit(f"error: kicad-cli drill export failed:\n{proc.stderr}")

    zip_path = os.path.join(out_dir, f"{PROJECT_NAME}_gerbers.zip")
    with zipfile.ZipFile(zip_path, "w", zipfile.ZIP_DEFLATED) as z:
        for name in sorted(os.listdir(gdir)):
            if name.endswith((".gbr", ".drl", ".gbrjob")):
                z.write(os.path.join(gdir, name), name)
    return zip_path


def natural_key(ref: str):
    m = re.match(r"([A-Za-z]+)(\d+)", ref)
    if m:
        return (m.group(1), int(m.group(2)))
    return (ref, 0)


def compress_refs(refs: list[str]) -> str:
    """C1,C2,C3,C5 -> 'C1-C3,C5' (KiCad-style range compression)."""
    refs = sorted(refs, key=natural_key)
    groups: list[list[str]] = []
    for r in refs:
        m = re.match(r"([A-Za-z]+)(\d+)$", r)
        if not m:
            groups.append([r])
            continue
        prefix, num = m.group(1), int(m.group(2))
        if groups and groups[-1] and re.match(r"([A-Za-z]+)(\d+)$", groups[-1][-1]):
            pm = re.match(r"([A-Za-z]+)(\d+)$", groups[-1][-1])
            if pm.group(1) == prefix and int(pm.group(2)) == num - 1:
                groups[-1].append(r)
                continue
        groups.append([r])
    parts = []
    for g in groups:
        if len(g) >= 3:
            parts.append(f"{g[0]}-{g[-1]}")
        else:
            parts.extend(g)
    return ",".join(parts)


def build(rows: list[dict], parts: list[Part]):
    """Return (bom_groups, cpl_rows, unmapped, excluded)."""
    bom = defaultdict(list)       # key -> list of refs
    meta = {}                     # key -> (comment, footprint, lcsc, jlc_class)
    cpl_rows = []
    unmapped = []                 # (ref, val, package)
    excluded = []                 # (ref, reason)

    for r in rows:
        ref = r["Ref"]
        val = r["Val"]
        package = r["Package"]
        match = next((p for p in parts if p.matches(val, package)), None)

        if match is None:
            unmapped.append((ref, val, package))
            continue
        if not match.assemble:
            excluded.append((ref, "not assembled (jlc_parts.csv assemble=no)"))
            continue
        if not match.lcsc:
            unmapped.append((ref, val, package))
            continue

        key = (match.lcsc, match.comment, package)
        bom[key].append(ref)
        meta[key] = (match.comment, package, match.lcsc, match.jlc_class)

        rot = (float(r["Rot"]) + match.rot_offset) % 360.0
        layer = "Top" if r["Side"].lower().startswith("t") else "Bottom"
        cpl_rows.append({
            "Designator": ref,
            "Mid X": f'{float(r["PosX"]):.4f}',
            "Mid Y": f'{float(r["PosY"]):.4f}',
            "Layer": layer,
            "Rotation": f"{rot:.4f}",
        })

    bom_groups = []
    for key, refs in bom.items():
        comment, footprint, lcsc, jlc_class = meta[key]
        bom_groups.append({
            "Comment": comment,
            "Designator": compress_refs(refs),
            "Footprint": footprint,
            "LCSC Part #": lcsc,
            "JLC Class": jlc_class,
            "Qty": len(refs),
        })
    bom_groups.sort(key=lambda g: natural_key(g["Designator"].split(",")[0]))
    cpl_rows.sort(key=lambda c: natural_key(c["Designator"]))
    return bom_groups, cpl_rows, unmapped, excluded


def write_bom(path: str, groups: list[dict]):
    cols = ["Comment", "Designator", "Footprint", "LCSC Part #", "JLC Class", "Qty"]
    with open(path, "w", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=cols)
        w.writeheader()
        for g in groups:
            w.writerow(g)


def write_cpl(path: str, rows: list[dict]):
    cols = ["Designator", "Mid X", "Mid Y", "Layer", "Rotation"]
    with open(path, "w", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=cols)
        w.writeheader()
        for r in rows:
            w.writerow(r)


def main():
    ap = argparse.ArgumentParser(description="Generate JLCPCB-ready BOM + CPL from the KiCad PCB.")
    ap.add_argument("--pcb", default=DEFAULT_PCB, help="path to .kicad_pcb (default: %(default)s)")
    ap.add_argument("--parts", default=DEFAULT_PARTS, help="LCSC part map CSV (default: jlc_parts.csv)")
    ap.add_argument("--out-dir", default=DEFAULT_OUT, help="output directory (default: ./out)")
    ap.add_argument("--kicad-cli", default=None, help="path to kicad-cli (auto-detected otherwise)")
    ap.add_argument("--check", action="store_true", help="report mapping coverage only; write no files")
    ap.add_argument("--strict", action="store_true", help="exit non-zero if any placed part is unmapped")
    ap.add_argument("--gerbers", action="store_true", help="also plot Gerbers + drill and zip them for fab")
    ap.add_argument("--fab-only", action="store_true", help="only plot Gerbers + drill zip (skip BOM/CPL)")
    args = ap.parse_args()

    if not os.path.isfile(args.pcb):
        sys.exit(f"error: PCB not found: {args.pcb}")
    kicad_cli = find_kicad_cli(args.kicad_cli)

    if args.fab_only:
        os.makedirs(args.out_dir, exist_ok=True)
        zip_path = export_gerbers(kicad_cli, args.pcb, args.out_dir)
        print(f"Wrote {zip_path}")
        return 0

    parts = load_parts(args.parts)
    rows = run_pos_export(kicad_cli, args.pcb)
    bom_groups, cpl_rows, unmapped, excluded = build(rows, parts)

    total = len(rows)
    assembled = len(cpl_rows)
    print(f"Placed components : {total}")
    print(f"Assembled parts   : {assembled} in {len(bom_groups)} BOM lines")
    print(f"Excluded (mech.)  : {len(excluded)}")
    if excluded:
        exrefs = compress_refs([e[0] for e in excluded])
        print(f"    {exrefs}")
    if unmapped:
        print(f"UNMAPPED          : {len(unmapped)}  <-- add rows to {os.path.basename(args.parts)}")
        for ref, val, pkg in unmapped[:20]:
            print(f"    {ref:6}  val={val!r:16}  package={pkg}")
        if len(unmapped) > 20:
            print(f"    ... and {len(unmapped) - 20} more")

    if args.check:
        return 1 if (unmapped and args.strict) else 0

    os.makedirs(args.out_dir, exist_ok=True)
    bom_path = os.path.join(args.out_dir, f"{PROJECT_NAME}_BOM.csv")
    cpl_path = os.path.join(args.out_dir, f"{PROJECT_NAME}_CPL.csv")
    write_bom(bom_path, bom_groups)
    write_cpl(cpl_path, cpl_rows)
    print(f"\nWrote {bom_path}")
    print(f"Wrote {cpl_path}")
    if args.gerbers:
        zip_path = export_gerbers(kicad_cli, args.pcb, args.out_dir)
        print(f"Wrote {zip_path}")
    if unmapped:
        print("\nWARNING: unmapped parts were skipped — the BOM/CPL are INCOMPLETE.")
        return 1 if args.strict else 0
    print("\nAll placed parts mapped. Upload BOM + CPL to JLCPCB assembly.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
