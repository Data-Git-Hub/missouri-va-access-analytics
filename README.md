# missouri-va-access-analytics

A data-driven analysis of Veterans Affairs appointment wait times and care pathways, including VA vs. community performance metrics, filtering Missouri facilities from 2014–2025 to build an evidence-based decision-support model.


**Short tagline:**
> A data-driven evaluation of how quickly Missouri veterans receive care — and which factors most strongly predict timely access within the VA and Community Care systems.


---

## Introduction

Timely access to healthcare remains one of the most critical challenges facing the United States Department of Veterans Affairs (VA). Multiple federal reviews have documented persistent delays in scheduling, processing, and completing care, especially in specialty services (U.S. Government Accountability Office [GAO], 2023; Department of Veterans Affairs Office of Inspector General [VA OIG], 2024). In response to long-standing access problems, major federal legislation—including the Veterans Access, Choice, and Accountability Act of 2014 (VACAA) and the VA MISSION Act of 2018, expanded the use of community providers to improve appointment timeliness and reduce operational bottlenecks (United States, 2014; United States, 2018).

This project analyzes Missouri appointment wait times using the publicly available Griffith (2024) dataset to identify measurable differences between VA facility care and Community Care, quantify specialty-level delays, and evaluate historical trends following federal policy interventions. In addition to exploratory data analysis (EDA), the project implements a supervised machine learning (ML) workflow to predict whether an appointment meets the federal access standard—defined as completion within established timelines determined by specialty category.

The predictive modeling pipeline uses logistic regression and random forest classifiers to evaluate how care setting, specialty category, facility code (STA3N), calendar year, and veteran geography influence the likelihood of meeting the access standard. The goal is to create a reproducible, scalable analytic framework that can be extended to other states and integrated with escalation-channel outcomes (e.g., Patient Advocate, White House VA Hotline, congressional casework) in future work. The results provide operational insights relevant to transparency, accountability, and performance improvement across the VA healthcare system.


---

## Machine Learning Model Results

<h3 align="center">Figure 1 — ROC Curves</h3>
<p align="center">
  <img src="figures/ml/ml_roc_logreg_vs_rf.png" width="600">
</p>
<p align="center">
  <em>ROC curves for logistic regression and random forest models predicting access-standard
  attainment. The random forest model achieves a higher AUC on the held-out test set, indicating
  better discriminatory performance between timely and delayed appointments.</em>
</p>

---

<h3 align="center">Figure 2 — Logistic Regression Confusion Matrix</h3>
<p align="center">
  <img src="figures/ml/ml_confusion_logistic_regression.png" width="450">
</p>
<p align="center">
  <em>Normalized confusion matrix for the logistic regression model. Values represent the proportion
  of true “Met” and “Not Met” appointments classified into each category.</em>
</p>

---

<h3 align="center">Figure 3 — Random Forest Confusion Matrix</h3>
<p align="center">
  <img src="figures/ml/ml_confusion_random_forest.png" width="450">
</p>
<p align="center">
  <em>Normalized confusion matrix for the random forest model. Compared to logistic regression,
  the ensemble model improves sensitivity for appointments that meet the access standard while
  maintaining similar specificity.</em>
</p>


---

## Project Structure

```text
missouri-va-access-analytics/
|   | - data/
|      | - cleaned
|          | - cleaned_mo_waits.csv.gz
|          | - cleaning_summary.csv
|      | - metadata
|          | - eda_compliance_by_setting.csv
|          | - eda_group_stats_setting_specialty.csv
|          | - eda_numeric_summary.csv
|          | - figures_manifest.csv
|          | - ml_model_metrics_summary.csv
|          | - ml_rf_feature_importances.csv
|      | - processed/  # Missouri-only data exported to Git
|          | - consult_waits_state_subset.csv.gz
|      | - raw/        # original files (ignored by Git due to file size)
|          | - consult_waits_2024_03_25.csv
|      | - figures 
|          | - eda
|              | - correlation_matrix.png
|              | - eda_access_by_setting_bar.png
|              | - eda_waitdays_box_by_setting.png
|              | - eda_waitdays_hist.png
|              | - missing_heatmap.png
|              | - missing_matrix.png
|              | - trend_median_wait_by_year_community.png
|              | - trend_median_wait_by_year_va.png
|          | - ml
|              | - ml_confusion_logistic_regression.png
|              | - ml_confusion_random_forest.png
|              | - ml_feature_importance_rf_top15.png
|              | - ml_roc_logreg_vs_rf.png
|      | - mech_diag.png
|      | - scripts/
|          | - clean_mo_waits.py
|          | - count_rows_cols.py
|          | - generate_mechanism_diagram.py
|          | - prepare_missouri_data.py
|   | - .gitgnore
|   | - LICENSE
|   | - README.md
|   | - requirements.txt
|   | - va_mo_waits.ipynb
```


---

## Requirements

- **Python:**
  

---

## Quick Start

## 1) Create, Activate, and Install Dependencies for .venv

Windows
```shell
# Navigate to the project root
cd C:\Projects\missouri-va-access-analytics

# Create a new virtual environment
python -m venv .venv

# Activate the virtual environment
.\.venv\Scripts\Activate

# Upgrade pip (recommended)
python -m pip install --upgrade pip

# Install required dependencies
pip install -r requirements.txt

# (Optional) Register .venv as a Jupyter kernel
python -m ipykernel install --user --name missouri-va-venv --display-name "Python 3.11 – MO VA (.venv)"
```

macOS/Linux
```bash
# Navigate to the project root
cd ~/Projects/missouri-va-access-analytics

# Create a new virtual environment
python3 -m venv .venv

# Activate the virtual environment
source .venv/bin/activate

# Upgrade pip (recommended)
python -m pip install --upgrade pip

# Install required dependencies
pip install -r requirements.txt

# (Optional) Register .venv as a Jupyter kernel
python -m ipykernel install --user --name missouri-va-venv --display-name "Python 3.11 – MO VA (.venv)"
```

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

Department of Veterans Affairs, Office of Inspector General. (2024). *Delays in community care consult processing and scheduling at the Martinsburg VA Medical Center in West Virginia* (Report No. 23-02020-85). https://www.vaoig.gov/

Griffith, K. (2024). *Appointment Wait Times for Primary and Specialty Care in Veterans Health Administration Facilities vs. Community Medical Centers* (Version 16) [Dataset]. Mendeley Data. https://doi.org/10.17632/rmk89k4rhb.16

U.S. Government Accountability Office. (2023). *Veterans health care: VA actions needed to ensure timely scheduling of specialty care appointments* (GAO-23-105617). https://www.gao.gov/

United States. (2014). *Veterans Access, Choice, and Accountability Act of 2014*, Pub. L. No. 113–146. https://www.govinfo.gov/

United States. (2018). *VA MISSION Act of 2018*, Pub. L. No. 115–182. https://www.congress.gov/

Department of Veterans Affairs. (2019). *Veterans Community Care Program*, 38 C.F.R. §§ 17.4000–17.4040. https://www.ecfr.gov/


---

## Version History
- Proj 6.1  | Modify README.md
- Proj 6.0  | Modify README.md
- Proj 5.2  | Modify va_mo_waits.ipynb, README.md
- Proj 5.1  | Modify va_mo_waits.ipynb, README.md
- Proj 5.0  | Modify va_mo_waits.ipynb, requirements.txt, README.md
- Proj 4.6  | Modify va_mo_waits.ipynb, README.md - Easier use for LaTex
- Proj 4.5  | Modify va_mo_waits.ipynb, README.md
- Proj 4.4  | Modify README.md
- Proj 4.3  | Add metadata folder, figures folder, eda folder;Modify README.md
- Proj 4.2  | Modify va_mo_waits.ipynb, README.md
- Proj 4.1  | Add cleaned_mo_waits.parquet; Modify clean_mo_waits.py; README.md
- Proj 4.0  | Add va_mo_waits.ipynb; Modify README.md
- Proj 3.3  | Modify README.md
- Proj 3.2  | Add cleaning_summary.csv; Modify clean_mo_waits.py; README.md
- Proj 3.1  | Delete placeholder file text.txt from cleaned folder; Modify README.md
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
- Test 2.0  | Test clean_mo_waits.py: TEST-FAIL created mo_wait_clean.csv.gz with 1kb of information
- Test 2.1  | Test clean_mo_waits.py: TEST-SUCCESS created mo_wait_clean.csv.gz, cleaning_summary.csv
- Test 3.0  | Test va_mo_waits.ipynb: TEST-SUCCESS created readable .png files for LaTex
- Test 6.0  | Test va_mo_waits.ipynb: TEST-SUCCESS

## Commit History (Commits needed to complete Sync due to Internet Connection Error or other factor)
- Comm  0.1 | Commit retire due to connection error
- Comm  0.2 | Commit retire due to connection error


