# 💼 TDS & TCS Applicability Analyzer (India FY 2024–25)

A powerful, Python/JavaScript-based analyzer that automatically determines **TDS/TCS applicability** on transactions using **Excel or CSV inputs**.  
It uses **keyword-based ledger mapping**, **section-wise thresholds**, and **per-bill limits** to detect applicable tax sections for each transaction.

---

## 🧩 Overview

The **TDS/TCS Applicability Analyzer** is designed to help accountants, auditors, and finance professionals analyze voucher data (Payments, Receipts, or Journals) to determine which **Income Tax Section** applies to each transaction.

It supports **FY 2024–25** TDS/TCS rates and threshold limits as per the Indian Income Tax Act.

---

## 📁 Input File Format

Input file should be an Excel (`.xlsx`) or CSV file with the following columns:

| Column Name     | Description                                    | Example                          |
|------------------|------------------------------------------------|----------------------------------|
| Date             | Voucher or transaction date                    | 2024-06-15                      |
| Debit Ledger     | Name of the debit ledger                       | Rent Expense                    |
| Credit Ledger    | Name of the credit ledger                      | ABC Properties Pvt Ltd          |
| Voucher Type     | Voucher type (Payment/Receipt/Journal)         | Payment                         |
| Voucher No.      | Voucher number or ID                           | PMT/001                         |
| Amount           | Transaction amount                             | 75,000                          |

---

## ⚙️ How It Works

1. **Read the input file** using `pandas` (Python) or `xlsx` package (JS).
2. **Scan “Debit Ledger” and “Credit Ledger”** names for **keywords** using a predefined mapping table.
3. **Match applicable TDS/TCS section** from the mapping (e.g., Rent → 194I, Professional Fees → 194J).
4. **Check thresholds:**
   - **Annual limit:** Section-wise total per vendor
   - **Per-bill limit:** If applicable
5. **Determine applicability:**
   - If thresholds are crossed, mark transaction as **“TDS Applicable”**
   - Otherwise, mark **“Not Applicable”**
6. **Compute tax** at the correct rate.
7. **Output results** to Excel/PDF summary report.

---

## 🧾 Example Output

| Date       | Debit Ledger   | Credit Ledger           | Section | Description          | Amount | TDS Rate | TDS Amt | Status           |
|-------------|----------------|--------------------------|----------|----------------------|---------|-----------|----------|------------------|
| 2024-06-15  | Rent Expense   | ABC Properties Pvt Ltd   | 194I     | Rent of building     | 75,000  | 10%       | 7,500    | Applicable ✅     |
| 2024-07-01  | Repairs Exp.   | XYZ Engineers            | 194C     | Contract Payment     | 22,000  | 1%        | 220      | Applicable ✅     |
| 2024-07-12  | Stationery     | Super Traders            | N/A      | Goods Purchase       | 18,000  | -         | -        | Not Applicable ❌ |

---

## 📊 Features

✅ Supports **all major TDS & TCS sections (194C, 194J, 194I, 206C, etc.)**  
✅ **Dynamic threshold check** (per vendor & per section)  
✅ **Excel/PDF output with summaries**  
✅ **Party-wise, section-wise, and amount-wise reports**  
✅ Works with **any accounting software exports (Tally, Busy, Marg, etc.)**  
✅ Can be integrated into **web apps** or **desktop tools**  

---

## 🧠 Detection Logic (Simplified)

```text
For each transaction:
    1. Get Debit & Credit Ledger names
    2. Search for keyword matches in TDS/TCS mapping
    3. If match found:
          Identify applicable section & rate
          Check if cumulative total > threshold
          If yes → Mark as "Applicable"
          Else → "Not Applicable"
📘 TDS/TCS Mapping Example (FY 2024–25)
Section	Description	Threshold	Rate	Keywords
194C	Contractor/Job Work	30,000	1%	contract, job, labour, work
194I	Rent of Land/Building	2,40,000	10%	rent, building, property, office
194J	Professional Fees	30,000	10%	consultancy, professional, ca
194H	Commission/Brokerage	15,000	5%	commission, brokerage
206C(1H)	Sale of Goods (TCS)	50,00,000	0.1%	sale, goods, invoice, revenue

🚀 Usage (Python Version)
1️⃣ Install Requirements
bash
Copy code
pip install pandas openpyxl reportlab streamlit
2️⃣ Run the Analyzer
bash
Copy code
python tds_tcs_analyzer.py
3️⃣ Streamlit Web App (Optional)
bash
Copy code
streamlit run tds_tcs_app.py
4️⃣ Upload Excel and Download Report
🧮 Output Files
TDS_TCS_Report.xlsx – Detailed section-wise analysis

TDS_TCS_Summary.pdf – Management summary with charts

🛠️ Tech Stack
Language: Python / TypeScript

Libraries: pandas, openpyxl, reportlab, streamlit

Frontend (Optional): React or Streamlit UI

Output Format: Excel / PDF / JSON

🔒 Notes
The analyzer uses keyword-based matching, so please maintain standard ledger naming (e.g., “Rent Expense” instead of “RentExp”).

TDS/TCS thresholds are as per Income Tax Act FY 2024–25.

Supports both cash basis and accrual basis transactions.

🧑‍💻 Developer Guide
If you want to extend the logic or modify mappings:

Open tds_mapping.py or tds_mapping.ts

Add or edit new sections:

python
Copy code
{
  "section": "194C",
  "threshold": 30000,
  "rate": 1,
  "keywords": ["contract", "job work", "labour"],
  "description": "Payment to contractor"
}
Run the analyzer again — it will automatically apply your updates.
