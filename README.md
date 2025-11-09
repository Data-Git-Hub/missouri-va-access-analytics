# missouri-va-access-analytics

A data-driven analysis of Veterans Affairs appointment wait times and care pathways, including VA vs. community performance metrics, filtering Missouri facilities from 2014–2025 to build an evidence-based decision-support model.

**Short tagline:**


---

## Introduction


---

## Project Structure

```text
missouri-va-access-analytics/
|   | - data/
|       | - processed/  # Missouri-only data exported to Git
|       | - raw/        # original files (ignored by Git due to file size)
|           | - consult_waits_2024_03_25.csv
|   | - scripts/
|       | - prepare_missouri_data.py
|   | - .gitgnore
|   | - README.md
```


---

## Requirements

- **Python:**


---

### Recommended tooling


### Why the Raw Data Folder Is Ignored

The `.gitignore` file contains the following lines:

```bash
# Never commit full dataset
data/raw/
```

These entries ensure that large, original data files stored in the `data/raw/` directory are **not committed to the GitHub repository**.

This rule serves two key purposes:

1. **Repository Size and Performance**  
   The full dataset can exceed GitHub’s 100 MB per-file limit and significantly slow down cloning and version control operations.  
   By ignoring this folder, the repository remains lightweight, efficient, and easier to maintain.

2. **Reproducibility and Clean Workflow**  
   Only the **data preparation scripts** and the **processed Missouri-only dataset** are versioned in Git.  
   Anyone replicating the project can download the raw dataset separately, place it in the `data/raw/` directory, and run the included preparation script to regenerate the processed data.

In summary, this `.gitignore` rule prevents large or sensitive raw data files from being uploaded to GitHub while maintaining a clean, reproducible, and efficient project workflow.


---

## Authors

Contributors names and contact info <br>
@github.com/Data-Git-Hub <br>


---

## References


---

## Version History
- Proj 3.0  | Add clean_mo_waits.py; Modify README.md
- Proj 2.0  | Add cleaned folder to data folder; Modify README.md
- Proj 1.4  | Add count_rows_cols.py; Modify README.md
- Proj 1.3  | Modify prepare_missouri_data.py, README.md
- Proj 1.2  | Modify prepare_missouri_data.py, README.md
- Proj 1.1  | Modify prepare_missouri_data.py, requirements.txt, README.md
- Proj 1.0  | Add prepare_missouri_data.py; Modify README.md
- Init 0.2  | Modify requirements.txt, README.md
- Init 0.1  | Add scripts folder, prepare_missouri_data.py, consult_waits_2024_03_25.csv; Modify .gitignore, README.md
- Init 0.0  | Add data folder, process folder, raw folder, requirements.txt; Modify .gitignore, README.md

## Test History
- Test 1.0  | Test prepare_missouri_data.py: TEST-FAIL script did not process consult_waits_2024_03_25.csv
- Test 1.1  | Test prepare_missouri_data.py: TEST-FAIL script did not process consult_waits_2024_03_25.csv
- Test 1.2  | Test prepare_missouri_data.py: TEST-SUCCESS created consult_waits_state_subset.csv.gz
- Test 2.0  | Test clean_mo_waits.py: TEST-SUCCESS created mo_wait_clean.csv.gz

## Commit History (Commits needed to complete Sync due to Internet Connection Error or other factor)
- Comm  0.1 |