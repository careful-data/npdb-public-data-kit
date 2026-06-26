# NPDB Public Use Data File — Download Instructions

## Official source

Download the NPDB Public Use Data File from HRSA:

https://www.npdb.hrsa.gov/resources/publicData.jsp

## File formats

The full public-use file is available in:

- **CSV** (recommended for this toolkit)
- ASCII fixed-width (`.DAT`) — not supported by v0.1
- SPSS portable (`.POR`) — not supported by v0.1

## Update schedule

NPDB updates quarterly as of:

- March 31
- June 30
- September 30
- December 31

Updated files are generally available within ~2 months of each cutoff date.

## Local usage

1. Complete the HRSA download form on the official site.
2. Save the CSV (or ZIP containing CSV) locally.
3. Run:

```bash
npdb-kit build /path/to/NPDBYYMM.CSV --output ./output
```

Do not commit raw NPDB files to version control.

## Citation

When publishing research, cite the NPDB Public Use Data File and document the release quarter used.
