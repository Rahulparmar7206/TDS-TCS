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
