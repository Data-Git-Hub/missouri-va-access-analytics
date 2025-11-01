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


---

## Authors

Contributors names and contact info <br>
@github.com/Data-Git-Hub <br>


---

## References


---

## Version History
- Proj 1.0  | Add prepare_missouri_data.py; Modify README.md
- Init 0.2  | Modify requirements.txt, README.md
- Init 0.1  | Add scripts folder, prepare_missouri_data.py, consult_waits_2024_03_25.csv; Modify .gitignore, README.md
- Init 0.0  | Add data folder, process folder, raw folder, requirements.txt; Modify .gitignore, README.md

## Test History
- Test 1.0  | Test prepare_missouri_data.py: TEST-FAIL script did not process consult_waits_2024_03_25.csv
