import pandas as pd
import random
from datetime import datetime, timedelta

def generate_sample_data(num_transactions=100):
    """Generate sample transaction data for testing"""
    
    sections_data = {
        '194J': ['M/s. ABC Consultants', 'Professional Services Ltd', 'Tech Solutions Inc', 
                 'Freelance Expert', 'Legal Advisors LLP'],
        '194C': ['M/s. XYZ Contractors', 'Build-It Construction', 'Alpha Builders',
                 'Advertising Agency', 'Catering Services'],
        '194H': ['Commission Agents', 'Brokerage Firm', 'Agent Services',
                 'Stock Broker', 'Insurance Broker'],
        '194I': ['Rent - Office Space', 'Rental Property', 'Lease Holdings',
                 'Commercial Rent', 'Equipment Hire'],
        '194K': ['Mutual Fund Units', 'UTI Dividend', 'SIP Returns',
                 'Equity Fund', 'Debt Fund'],
        '194A': ['Bank Interest', 'FD Interest', 'Savings Account Interest'],
        '194D': ['Insurance Commission', 'Policy Commission'],
    }
    
    transactions = []
    start_date = datetime(2024, 4, 1)
    
    for i in range(num_transactions):
        section = random.choice(list(sections_data.keys()))
        party = random.choice(sections_data[section])
        
        date = start_date + timedelta(days=random.randint(0, 365))
        
        # Generate realistic amounts based on section
        if section == '194J':
            amount = random.randint(10000, 500000)
        elif section == '194C':
            amount = random.randint(20000, 800000)
        elif section == '194H':
            amount = random.randint(5000, 200000)
        elif section == '194I':
            amount = random.randint(15000, 400000)
        elif section == '194K':
            amount = random.randint(3000, 100000)
        elif section == '194A':
            amount = random.randint(5000, 150000)
        else:
            amount = random.randint(10000, 300000)
        
        # Determine expense category
        expense_mapping = {
            '194J': 'Professional Fees',
            '194C': 'Contractor Payments',
            '194H': 'Brokerage',
            '194I': 'Rent Expense',
            '194K': 'Investment Income',
            '194A': 'Interest Income',
            '194D': 'Commission Expense'
        }
        
        transactions.append({
            'Date': date.strftime('%Y-%m-%d'),
            'Debit Ledger': expense_mapping.get(section, 'Expense'),
            'Credit Ledger': party,
            'Voucher Type': 'Payment' if section not in ['194K', '194A'] else 'Receipt',
            'Voucher No.': f'V{1000+i}',
            'Amount': round(amount, 2)
        })
    
    df = pd.DataFrame(transactions)
    
    # Sort by date
    df['Date'] = pd.to_datetime(df['Date'])
    df = df.sort_values('Date')
    df['Date'] = df['Date'].dt.strftime('%Y-%m-%d')
    
    # Save to Excel
    df.to_excel('sample_transactions.xlsx', index=False)
    
    print(f"✓ Generated {num_transactions} sample transactions")
    print(f"✓ File saved: sample_transactions.xlsx")
    print(f"\nBreakdown by Section:")
    
    # Show summary
    for section in sections_data.keys():
        count = len([t for t in transactions if section in str(t['Debit Ledger']) or section in str(t['Credit Ledger'])])
        if count > 0:
            print(f"  - Section {section}: {count} transactions")
    
    return df

if __name__ == '__main__':
    print("=" * 80)
    print("TDS/TCS SAMPLE DATA GENERATOR")
    print("=" * 80)
    print()
    
    # Generate data
    df = generate_sample_data(100)
    
    print("\nSample data preview:")
    print(df.head(10).to_string(index=False))
    
    print("\n" + "=" * 80)
    print("You can now upload 'sample_transactions.xlsx' to the TDS/TCS Analyzer")
    print("=" * 80)
