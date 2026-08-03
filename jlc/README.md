# JLCPCB assembly export

Generates the two files JLCPCB's assembly service needs, straight from the KiCad design:

| File | Contents | Purpose |
|------|---------|---------|
| `out/analog_NN_gerbers.zip` | Gerbers (4-layer) + Excellon drill | **fab** — make the bare board |
| `out/analog_NN_BOM.csv` | Comment, Designator, Footprint, LCSC Part #, JLC Class, Qty | **assembly** — what to place |
| `out/analog_NN_CPL.csv` | Designator, Mid X, Mid Y, Layer, Rotation | **assembly** — where/how to place |

Coordinates and rotations come from `kicad-cli pcb export pos` (KiCad's own placement
engine). LCSC part numbers, canonical comments, assemble flags and rotation offsets come
from **`jlc_parts.csv`** — that file is the source of truth you edit; the script is not.

## Usage

```bash
python3 export_jlc.py            # write BOM + CPL into ./out
python3 export_jlc.py --gerbers  # BOM + CPL + gerber/drill zip (full JLCPCB package)
python3 export_jlc.py --fab-only # only the gerber/drill zip
python3 export_jlc.py --check    # report mapping coverage, write nothing
python3 export_jlc.py --strict   # non-zero exit if any placed part is unmapped
python3 export_jlc.py --out-dir dist --kicad-cli /path/to/kicad-cli
```

The Gerbers cover the 4-layer stackup (F.Cu, In1.Cu, In2.Cu, B.Cu) plus mask/silk/paste
and Edge.Cuts, with **absolute** drill origin so the fab files line up with the CPL.

Requires KiCad 8/9 (`kicad-cli`). On macOS it auto-finds
`/Applications/KiCad/KiCad.app/Contents/MacOS/kicad-cli`.

## Assigning parts

Each placed component is matched to the **first** row of `jlc_parts.csv` whose
`match_package` is a prefix of its footprint **and** whose `match_value` is `*` or equals
the schematic value. To add/change a part, edit that CSV and re-run. `assemble=no` keeps a
component out of assembly (the 10 `WireSolderPad` J-pads are hand-soldered wire terminals).

## Current board (v1)

220 assembled parts, 9 BOM lines; 10 wire pads excluded.

- Op-amps U1–U27 have a **blank** schematic value — they are mapped to `TLV9061IDBVR`
  (C398358) by the `*` SOT-23-5 rule, not by value.
- **Extended** parts (TLV9061 C398358, AD5160 C40097) incur JLCPCB feeder fees; the rest
  are Basic. AD5160 is the 10k-tap variant — the 100k variant is C578141.

## Before you order — verify

1. **Rotation.** All `rot_offset` values default to `0` (KiCad's native rotation). KiCad and
   JLCPCB do not always agree on the zero-orientation of SOT-23-5/‑8 and SOIC parts. Upload,
   open the JLCPCB placement **preview**, and if any part is rotated wrong set its
   `rot_offset` in `jlc_parts.csv` (usually ±90/180) and re-export. Do not skip this — a bad
   rotation solders the part down mirrored.
2. **Origin.** The CPL uses KiCad's page origin (no drill-origin offset). Export your Gerbers
   the same way (default origin) so board and placement align.
3. **Stock.** LCSC numbers were verified at design time; re-check availability before ordering.
