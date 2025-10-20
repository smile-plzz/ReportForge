# Comments Report Starter

A small, reproducible pipeline to generate an operational report from a CSV of interactions/comments.

## What it does (out of the box)

- **Late night interaction count (20:00–06:00)** (local to your timezone).
- **Issues reported vs. resolved counts**.
- **Merchants who went live**.
- Additional metrics scaffolded for easy extension (peak hour, weekday/weekend split, etc.).
- Exports **metrics.json**, **metrics.md**, and basic **charts/** images.

## Repo layout

```
comments-report-starter/
├─ src/
│  ├─ report.py         # main CLI script
│  └─ utils.py          # helpers
├─ tests/
│  └─ sample_comments.csv
├─ charts/              # generated charts land here
├─ config.yaml          # map your column names (edit this!)
├─ requirements.txt
├─ Makefile
├─ scripts/
│  └─ setup.sh
└─ README.md
```

## Quickstart

```bash
# 1) Clone your Git repo and copy these files in,
#    or unzip comments-report-starter.zip then `cd` into it

python -m venv .venv
source .venv/bin/activate   # Windows: .venv\Scripts\activate
pip install -r requirements.txt

# 2) Put your CSV at any path, for example ./comments.csv
#    Then edit config.yaml to match your column names.
#    (The defaults match the sample file in tests/.)

# 3) Run the report
python src/report.py --csv ./comments.csv --tz Asia/Dhaka --out ./out

# Or with the sample:
python src/report.py --csv ./tests/sample_comments.csv --tz Asia/Dhaka --out ./out

# 4) Open the outputs
ls ./out
# -> metrics.json, metrics.md, and charts/*.png
```

## Config (column mapping)

Open **config.yaml** and set the columns that exist in your CSV. Defaults below:

```yaml
timestamp_col: timestamp
merchant_id_col: merchant_id
comment_col: comment
issue_status_col: issue_status       # values example: reported, resolved, open
issue_id_col: issue_id               # optional
resolution_timestamp_col: resolved_at  # optional
live_status_col: live_status         # values example: live, not_live
live_timestamp_col: live_at          # optional
actor_type_col: actor_type           # optional (merchant/support)
```

> Anything marked **optional** can be omitted. The script will skip metrics that need missing columns.

## Extending

- Add new metrics in `src/report.py` under `compute_additional_metrics`.
- Add new charts in the `render_charts` section using matplotlib.
- No seaborn, no custom colors are set by default (you can add them if you prefer).

## Make targets

```bash
make install     # create venv and install deps
make run         # run on ./tests/sample_comments.csv (edit Makefile to change args)
```

---

**Notes**
- The script treats time window 20:00–06:00 as *local* in `--tz` (default: Asia/Dhaka). Adjust with `--tz`.
- If your timestamps are naive, they’ll be assumed to already be in the provided `--tz`.
- If your timestamps contain timezone info, we normalize them to the provided `--tz` for analysis.
