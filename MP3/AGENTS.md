# AGENTS.md

## Overview
MP3 consulting project. Client: IMF. Cluster 37 countries on 9 ICT-worker issues. Two scores per issue (18 features). Goal: defensible country groups + macroeconomic interpretation. Interpretation is highest-weight part.

## Deliverables (ONLY these two files)
1. `analysis.py` = full analysis, single script, reproducible.
2. `report.docx` (or `report.pdf`) = formal client report.

Nothing else. No extra modules. No notebooks. No tests. No lint configs. No `src/`. No `requirements.txt`. No helper files. Figures embed directly in report. Intermediate files go to temp, deleted after.

## Stack
- Python 3.11+
- pandas, numpy, openpyxl, scipy, scikit-learn, matplotlib, seaborn
- Report build: `docx` or `pdf` skill

## Data
- Folder: `dataset/`
- `dataset/ICTIndiv.xlsx` = scores. Read only. Never edit.
- `dataset/ICTInvFldDesc.pdf` = issue definitions. Read first.
- Inspect columns first. Do not assume names or score meanings.

## Commands
- Run: `python analysis.py`

## Startup Workflow (mandatory order)
1. List installed skills first. Use `ListSkills` / `SearchSkills`.
2. Check Superpowers installed. Use for planning, execution, review. Missing? Say so. Do not fake it.
3. Read description PDF. Inspect Excel file.
4. Create plan. Each task gets one named skill that fits best. Show plan in chat. No `PLAN.md` file.
5. Execute. Write `analysis.py`. Run it. Build report.
6. Verify numbers from real output. Then stop.

## Plan Format (in chat only)
Table: `#`, `Task`, `Skill`, `Why`, `Output`.

Expected tasks (skill from installed list only):
- Plan and breakdown: Superpowers planning
- Data profiling, nulls, outliers: EDA skill (e.g. `programmatic-eda`)
- Cleaning, scaling, clustering: Superpowers execution
- Interpretation, economic context: deep-research
- Report build: `docx` or `pdf`
- Final review: Superpowers review

No fitting skill? Mark `none`. Do directly.

## Analysis Requirements
- Cluster on Score A only, Score B only, both combined.
- Compare outcomes. Adjusted Rand Index + membership table.
- Methods: hierarchical (Ward, average), k-means, optional GMM.
- Choose k with evidence: silhouette, elbow, dendrogram. Justify.
- Standardize features. State why.
- Check multicollinearity. Consider PCA. Report variance explained.
- Check outliers. Report effect.
- `random_state=42` everywhere.
- Profile each cluster. Rank countries.
- Interpret via macro lens: income, development stage, labour markets, digital infrastructure, education, policy.
- Flag borderline countries. State limits: n=37, unknown score method.

## Report Structure (headings MANDATORY)
1. Title page: title, names, roll numbers, course name + number, instructor name
2. Introduction
3. Data Preprocessing
4. Data Visualization
5. Hypotheses / Theory Building
6. Analysis
7. Recommendations
8. References

- Every chart earns place. Useless chart = penalty.
- Recommendations tied to findings.
- Tone: formal consultant to client.

## Code Conventions
- One script. Sectioned with comment headers.
- Paths via `pathlib`. Relative only.
- Constants at top.
- Figures: labelled axes, titles, 300 dpi.

## Boundaries
- Always: run script end to end. Cite real output numbers.
- Ask first: dropping countries or features, imputing values.
- Never: edit `dataset/`. Create files beyond the two deliverables. Invent data. Fabricate economic claims. Pad with filler charts.

## Gotchas
- Two scores per issue. Verify pairing against PDF.
- Score direction may differ per issue. Check before combining.
- n=37. Clusters fragile. Show stability.
- Cluster labels arbitrary between runs. Align before comparing.
- Interpretation weighs most. Reserve time.
- Deadline strict. Submit early on BB.