"""Generate synthetic NPDB fixture for tests."""

from __future__ import annotations

import csv
from pathlib import Path

COLUMNS = [
    "seqno",
    "rectype",
    "reptype",
    "origyear",
    "workstat",
    "workctry",
    "homestat",
    "homectry",
    "licnstat",
    "licnfeld",
    "practage",
    "grad",
    "algnnatr",
    "alegatn1",
    "alegatn2",
    "outcome",
    "malyear1",
    "malyear2",
    "payment",
    "totalpmt",
    "paynumbr",
    "numbprsn",
    "paytype",
    "pyrrltns",
    "ptage",
    "ptsex",
    "pttype",
    "aayear",
    "aaclass1",
    "aaclass2",
    "aaclass3",
    "aaclass4",
    "aaclass5",
    "basiscd1",
    "basiscd2",
    "basiscd3",
    "basiscd4",
    "basiscd5",
    "aalentyp",
    "aalength",
    "aaefyear",
    "aasigyr",
    "type",
    "practnum",
    "accrrpts",
    "npmalrpt",
    "nplicrpt",
    "npclprpt",
    "nppsmrpt",
    "npdearpt",
    "npexcrpt",
    "npgarpt",
    "npctmrpt",
    "fundpymt",
]

STATES = ["CA", "NY", "TX", "FL", "IL", "WA", "MA", "OH"]
REPTYPES = [101, 102, 301, 302, 401, 402, 702]
RECTYPES = ["A", "C", "M", "P"]
LICNFELD = [10, 20, 30, 100, 130, 642]


def blank_row() -> dict[str, str]:
    return {column: "" for column in COLUMNS}


def main() -> None:
    rows: list[dict[str, str]] = []
    for index in range(1, 101):
        row = blank_row()
        row["seqno"] = str(index)
        row["rectype"] = RECTYPES[index % len(RECTYPES)]
        row["reptype"] = str(REPTYPES[index % len(REPTYPES)])
        row["origyear"] = str(1990 + (index % 36))
        row["workstat"] = STATES[index % len(STATES)]
        row["licnstat"] = STATES[(index + 1) % len(STATES)]
        row["licnfeld"] = str(LICNFELD[index % len(LICNFELD)])
        row["practage"] = str(20 + (index % 8) * 10)
        row["grad"] = str(1970 + (index % 5) * 10)
        row["practnum"] = str(1000 + (index % 25))
        row["type"] = "1"

        if row["rectype"] in {"M", "P"}:
            row["payment"] = f"${1500 + index * 100}"
            row["totalpmt"] = row["payment"]
            row["paynumbr"] = "S"
            row["numbprsn"] = "1"
            row["paytype"] = "S"
            row["malyear1"] = str(1985 + (index % 30))
        else:
            row["aayear"] = str(1995 + (index % 25))
            row["aaclass1"] = "101"
            row["basiscd1"] = "01"

        if index == 50:
            row["workstat"] = ""
            row["payment"] = "$0"

        rows.append(row)

    output = Path(__file__).resolve().parent / "fixtures" / "sample_npdb.csv"
    output.parent.mkdir(parents=True, exist_ok=True)
    with output.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=COLUMNS)
        writer.writeheader()
        writer.writerows(rows)
    print(f"Wrote {output}")


if __name__ == "__main__":
    main()
