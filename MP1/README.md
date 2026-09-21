# Foodie India MP1

This project cleans and analyzes `Restaurant.xlsx`, creates the tables and figures in `outputs/`, and checks that the final report is correct. The original Excel file is never changed.

## Run the project

You do not need to install the project packages yourself.

1. Open a Terminal in this project folder.
2. Copy and paste this command, then press Enter:

```bash
./run.sh
```

The first run may take a few minutes because it creates a private Python environment and installs the required packages. Later runs are faster.

When the process finishes, it prints a line beginning with `PASS`. Then open:

- `Foodie_India_MP1_Report.pdf` for the final report;
- `outputs/` for the generated tables; and
- `outputs/figures/` for the generated charts.

If the Terminal says “Permission denied”, use this equivalent command:

```bash
bash run.sh
```

Python 3 is the only system requirement. If Python is missing, the script explains what must be installed and stops without changing the data.

## Project structure

```text
Foodie India MP1/
├── analysis.py                 Simple compatibility entry point
├── foodie_india/
│   ├── config.py               File paths, category order, and chart colors
│   ├── cleaning.py             Workbook loading, cleaning, and quality flags
│   ├── summaries.py            Descriptive summaries and duplicate audit
│   ├── statistics.py           Hypothesis tests and sensitivity analysis
│   ├── figures.py              Four report figures
│   └── pipeline.py             Runs the modules and writes every output
├── verify.py                   Checks the data, outputs, figures, and PDF
├── run.sh                      One-command setup, analysis, and verification
├── requirements.txt            Exact Python package requirements
├── Restaurant.xlsx             Original input; never modified
├── outputs/                    Generated CSV files and figures
├── Docs/                       Detailed project documentation
└── Foodie_India_MP1_Report.pdf Final report
```

The old command still works exactly as before:

```bash
python analysis.py
python verify.py
```

## What the checks protect

The verifier confirms the original workbook hash, all 365 source rows, anomaly flags, statistical decisions, generated files, figure dimensions, required report content, student identities, landscape layout, and black-on-white PDF typography outside the four figures.

For more detail, see:

- `Docs/PROJECT.md` for the complete workflow;
- `Docs/ANALYSIS.md` for cleaning and statistical methods; and
- `Docs/VERIFICATION.md` for every automated check.
