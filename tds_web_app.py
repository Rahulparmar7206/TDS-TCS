import pandas as pd
import numpy as np
from datetime import datetime
from flask import Flask, render_template, request, send_file, jsonify, session
import pdfplumber
import re
import io
import os
import json as json_lib
from werkzeug.utils import secure_filename

app = Flask(__name__)
app.secret_key = 'tds_analyzer_secret_key_2025'
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024
app.config['UPLOAD_FOLDER'] = 'uploads'

os.makedirs('uploads', exist_ok=True)

# Custom rules file
CUSTOM_RULES_FILE = 'custom_rules.json'

def load_custom_rules():
    """Load custom rules from JSON file"""
    try:
        if os.path.exists(CUSTOM_RULES_FILE):
            with open(CUSTOM_RULES_FILE, 'r') as f:
                return json_lib.load(f)
        return []
    except:
        return []

def save_custom_rules(rules):
    """Save custom rules to JSON file"""
    try:
        with open(CUSTOM_RULES_FILE, 'w') as f:
            json_lib.dump(rules, f, indent=2)
        return True
    except:
        return False

class TDSAnalyzer:
    """Complete TDS/TCS Analysis System with Custom Rules Support"""
    
    def __init__(self):
        # Default built-in rules
        self.default_rules = [
            {'section': '194A', 'threshold': 40000, 'per_bill_limit': None, 'rate': 10,
             'description': 'Interest other than on securities',
             'keywords': ['interest', 'fd', 'fixed deposit', 'savings', 'recurring deposit'],
             'type': 'TDS', 'priority': 1, 'search_in': 'credit', 'enabled': True, 'custom': False},
            
            {'section': '194C', 'threshold': 100000, 'per_bill_limit': 30000, 'rate': 1,
             'description': 'Contractor Payments (Individual/HUF)',
             'keywords': ['contractor', 'contract', 'construction', 'manufacturing'],
             'type': 'TDS', 'priority': 2, 'search_in': 'credit', 'enabled': True, 'custom': False},
            
            {'section': '194C', 'threshold': 100000, 'per_bill_limit': 30000, 'rate': 2,
             'description': 'Contractor Payments (Others)',
             'keywords': ['contractor', 'contract', 'advertising', 'advertisement', 'catering', 'transport'],
             'type': 'TDS', 'priority': 2, 'search_in': 'credit', 'enabled': True, 'custom': False},
            
            {'section': '194D', 'threshold': 15000, 'per_bill_limit': None, 'rate': 5,
             'description': 'Insurance Commission',
             'keywords': ['insurance commission', 'insurance agent', 'insurance broker'],
             'type': 'TDS', 'priority': 1, 'search_in': 'credit', 'enabled': True, 'custom': False},
            
            {'section': '194DA', 'threshold': 100000, 'per_bill_limit': None, 'rate': 2,
             'description': 'Life Insurance Policy Payment',
             'keywords': ['life insurance', 'policy maturity', 'insurance payout'],
             'type': 'TDS', 'priority': 1, 'search_in': 'credit', 'enabled': True, 'custom': False},
            
            {'section': '194G', 'threshold': 15000, 'per_bill_limit': None, 'rate': 2,
             'description': 'Commission on lottery tickets',
             'keywords': ['lottery commission', 'lottery ticket'],
             'type': 'TDS', 'priority': 1, 'search_in': 'credit', 'enabled': True, 'custom': False},
            
            {'section': '194H', 'threshold': 15000, 'per_bill_limit': None, 'rate': 5,
             'description': 'Commission or Brokerage',
             'keywords': ['commission', 'brokerage', 'broker', 'agent'],
             'type': 'TDS', 'priority': 1, 'search_in': 'credit', 'enabled': True, 'custom': False},
            
            {'section': '194I', 'threshold': 240000, 'per_bill_limit': None, 'rate': 10,
             'description': 'Rent of land/building/furniture',
             'keywords': ['rent', 'rental', 'lease', 'hire charges', 'godown', 'shop rent', 'office rent'],
             'type': 'TDS', 'priority': 1, 'search_in': 'credit', 'enabled': True, 'custom': False},
            
            {'section': '194I', 'threshold': 240000, 'per_bill_limit': None, 'rate': 2,
             'description': 'Rent of machinery/equipment',
             'keywords': ['machinery rent', 'equipment rent', 'plant rent'],
             'type': 'TDS', 'priority': 1, 'search_in': 'credit', 'enabled': True, 'custom': False},
            
            {'section': '194J', 'threshold': 30000, 'per_bill_limit': None, 'rate': 10,
             'description': 'Professional or Technical Services',
             'keywords': ['professional', 'consultancy', 'consulting', 'technical', 'legal',
                        'medical', 'engineering', 'architectural', 'accountancy', 'freelance', 
                        'professional fees', 'technical services'],
             'type': 'TDS', 'priority': 1, 'search_in': 'credit', 'enabled': True, 'custom': False},
            
            {'section': '194J', 'threshold': 30000, 'per_bill_limit': None, 'rate': 2,
             'description': 'Technical services (call centre)',
             'keywords': ['call centre', 'call center'],
             'type': 'TDS', 'priority': 1, 'search_in': 'credit', 'enabled': True, 'custom': False},
            
            {'section': '194K', 'threshold': 5000, 'per_bill_limit': None, 'rate': 10,
             'description': 'Income from mutual fund/UTI',
             'keywords': ['mutual fund', 'uti', 'dividend'],
             'type': 'TDS', 'priority': 1, 'search_in': 'credit', 'enabled': True, 'custom': False},
            
            {'section': '194LA', 'threshold': 250000, 'per_bill_limit': None, 'rate': 10,
             'description': 'Compensation on acquisition of property',
             'keywords': ['compensation', 'acquisition', 'land acquisition'],
             'type': 'TDS', 'priority': 1, 'search_in': 'credit', 'enabled': True, 'custom': False},
            
            {'section': '194M', 'threshold': 5000000, 'per_bill_limit': 5000000, 'rate': 5,
             'description': 'Payment by individuals/HUF',
             'keywords': ['contractor', 'professional', 'contract work'],
             'type': 'TDS', 'priority': 3, 'search_in': 'credit', 'enabled': True, 'custom': False},
            
            {'section': '194N', 'threshold': 10000000, 'per_bill_limit': 2000000, 'rate': 2,
             'description': 'Cash withdrawal',
             'keywords': ['cash withdrawal', 'cash'],
             'type': 'TDS', 'priority': 1, 'search_in': 'debit', 'enabled': True, 'custom': False},
            
            {'section': '194O', 'threshold': 500000, 'per_bill_limit': None, 'rate': 1,
             'description': 'E-commerce participants',
             'keywords': ['e-commerce', 'ecommerce', 'online marketplace'],
             'type': 'TDS', 'priority': 1, 'search_in': 'credit', 'enabled': True, 'custom': False},
            
            {'section': '194Q', 'threshold': 5000000, 'per_bill_limit': None, 'rate': 0.1,
             'description': 'Purchase of goods exceeding ₹50 lakhs',
             'keywords': ['purchase', 'goods purchase', 'material purchase', 'purchase of goods'],
             'type': 'TDS', 'priority': 2, 'search_in': 'credit', 'enabled': True, 'custom': False},
            
            {'section': '194R', 'threshold': 20000, 'per_bill_limit': None, 'rate': 10,
             'description': 'Benefits or perquisites',
             'keywords': ['benefit', 'perquisite', 'perk', 'incentive', 'reward'],
             'type': 'TDS', 'priority': 1, 'search_in': 'credit', 'enabled': True, 'custom': False},
            
            {'section': '194S', 'threshold': 50000, 'per_bill_limit': 10000, 'rate': 1,
             'description': 'Virtual digital assets',
             'keywords': ['cryptocurrency', 'crypto', 'bitcoin', 'virtual asset', 'nft'],
             'type': 'TDS', 'priority': 1, 'search_in': 'credit', 'enabled': True, 'custom': False},
            
            {'section': '193', 'threshold': 10000, 'per_bill_limit': None, 'rate': 10,
             'description': 'Interest on securities',
             'keywords': ['debenture', 'bond', 'security interest'],
             'type': 'TDS', 'priority': 1, 'search_in': 'credit', 'enabled': True, 'custom': False},
            
            {'section': '194B', 'threshold': 10000, 'per_bill_limit': None, 'rate': 30,
             'description': 'Lottery/puzzle winnings',
             'keywords': ['lottery', 'puzzle', 'game show', 'winning'],
             'type': 'TDS', 'priority': 1, 'search_in': 'credit', 'enabled': True, 'custom': False},
            
            {'section': '194BA', 'threshold': 0, 'per_bill_limit': None, 'rate': 30,
             'description': 'Online gaming winnings',
             'keywords': ['online game', 'gaming', 'online gambling'],
             'type': 'TDS', 'priority': 1, 'search_in': 'credit', 'enabled': True, 'custom': False},
            
            {'section': '194BB', 'threshold': 10000, 'per_bill_limit': None, 'rate': 30,
             'description': 'Horse race winnings',
             'keywords': ['horse race', 'race winning'],
             'type': 'TDS', 'priority': 1, 'search_in': 'credit', 'enabled': True, 'custom': False},
            
            {'section': '194EE', 'threshold': 2500, 'per_bill_limit': None, 'rate': 10,
             'description': 'NSS payments',
             'keywords': ['nss', 'national savings'],
             'type': 'TDS', 'priority': 1, 'search_in': 'credit', 'enabled': True, 'custom': False},
            
            {'section': '192', 'threshold': 0, 'per_bill_limit': None, 'rate': 0,
             'description': 'Salary (as per IT slab)',
             'keywords': ['salary', 'wages', 'remuneration'],
             'type': 'TDS', 'priority': 1, 'search_in': 'credit', 'enabled': True, 'custom': False},
            
            {'section': '194IA', 'threshold': 5000000, 'per_bill_limit': None, 'rate': 1,
             'description': 'Sale of immovable property',
             'keywords': ['sale of property', 'property sale', 'land sale'],
             'type': 'TDS', 'priority': 1, 'search_in': 'credit', 'enabled': True, 'custom': False},
            
            # TCS Sections
            {'section': '206C(1H)', 'threshold': 5000000, 'per_bill_limit': None, 'rate': 0.1,
             'description': 'Sale of goods exceeding ₹50 lakhs',
             'keywords': ['sales', 'goods sold', 'merchandise', 'sale invoice'],
             'type': 'TCS', 'priority': 3, 'search_in': 'debit', 'enabled': True, 'custom': False},
            
            {'section': '206C(1)', 'threshold': 0, 'per_bill_limit': None, 'rate': 1,
             'description': 'Sale of timber, forest produce, scrap',
             'keywords': ['tendu', 'timber', 'forest', 'scrap', 'minerals'],
             'type': 'TCS', 'priority': 2, 'search_in': 'debit', 'enabled': True, 'custom': False},
            
            {'section': '206CCA', 'threshold': 700000, 'per_bill_limit': None, 'rate': 5,
             'description': 'Foreign remittance (LRS)',
             'keywords': ['foreign remittance', 'liberalised remittance', 'lrs', 'overseas'],
             'type': 'TCS', 'priority': 1, 'search_in': 'debit', 'enabled': True, 'custom': False},
            
            {'section': '206C(1G)', 'threshold': 1000000, 'per_bill_limit': None, 'rate': 1,
             'description': 'Sale of motor vehicle',
             'keywords': ['motor vehicle', 'car', 'vehicle sale', 'automobile'],
             'type': 'TCS', 'priority': 1, 'search_in': 'debit', 'enabled': True, 'custom': False},
        ]
        
        # Load and merge with custom rules
        self.refresh_rules()
    
    def refresh_rules(self):
        """Refresh rules from default + custom"""
        custom = load_custom_rules()
        # Merge: custom rules override default if same section
        all_rules = self.default_rules.copy()
        all_rules.extend([{**r, 'custom': True} for r in custom])
        # Filter only enabled rules
        self.tds_rules = [r for r in all_rules if r.get('enabled', True)]
    
    def get_all_rules(self):
        """Get all rules (enabled + disabled)"""
        custom = load_custom_rules()
        all_rules = self.default_rules.copy()
        all_rules.extend([{**r, 'custom': True} for r in custom])
        return all_rules
    
    # ... (keep all other methods same: detect_tds_sections, process_transactions, etc.)
    def detect_tds_sections(self, transaction, rules):
        """Detect applicable TDS/TCS sections"""
        matches = []
        debit_lower = str(transaction['Debit Ledger']).lower()
        credit_lower = str(transaction['Credit Ledger']).lower()
        
        for rule in rules:
            for keyword in rule['keywords']:
                keyword_lower = keyword.lower()
                matched = False
                matched_in = None
                
                if rule['search_in'] in ['debit', 'both']:
                    if keyword_lower in debit_lower:
                        matched = True
                        matched_in = 'debit'
                
                if not matched and rule['search_in'] in ['credit', 'both']:
                    if keyword_lower in credit_lower:
                        matched = True
                        matched_in = 'credit'
                
                if matched and matched_in:
                    ledger_text = debit_lower if matched_in == 'debit' else credit_lower
                    confidence = 'high' if keyword_lower in ledger_text.split() else 'medium'
                    
                    matches.append({
                        'rule': rule,
                        'matched_keyword': keyword,
                        'matched_in': matched_in,
                        'confidence': confidence
                    })
                    break
        
        confidence_weight = {'high': 0, 'medium': 1, 'low': 2}
        matches.sort(key=lambda x: (x['rule']['priority'], confidence_weight[x['confidence']]))
        return matches
    
    def process_transactions(self, df):
        """Process and analyze all transactions"""
        grouped_data = {}
        all_transactions_detail = []
        
        for idx, row in df.iterrows():
            matches = self.detect_tds_sections(row, self.tds_rules)
            
            transaction_detail = {
                'Date': row['Date'],
                'Debit Ledger': row['Debit Ledger'],
                'Credit Ledger': row['Credit Ledger'],
                'Voucher Type': row.get('Voucher Type', 'N/A'),
                'Voucher No': row.get('Voucher No.', 'N/A'),
                'Amount': row['Amount'],
                'TDS Section': matches[0]['rule']['section'] if matches else 'N/A',
                'TDS Rate (%)': matches[0]['rule']['rate'] if matches else 0,
                'TDS Amount': (row['Amount'] * matches[0]['rule']['rate'] / 100) if matches else 0,
                'Matched Keyword': matches[0]['matched_keyword'] if matches else 'N/A'
            }
            all_transactions_detail.append(transaction_detail)
            
            if not matches:
                continue
            
            selected_match = matches[0]
            rule = selected_match['rule']
            
            party_name = row['Credit Ledger'] if rule['search_in'] == 'credit' else row['Debit Ledger']
            key = f"{party_name}|{rule['section']}"
            
            if key not in grouped_data:
                grouped_data[key] = {
                    'transactions': [],
                    'rule': rule,
                    'matched_rules': matches,
                    'party_name': party_name
                }
            
            grouped_data[key]['transactions'].append(row)
        
        results = []
        for key, data in grouped_data.items():
            transactions = data['transactions']
            rule = data['rule']
            party_name = data['party_name']
            
            total_amount = sum(t['Amount'] for t in transactions)
            max_transaction = max(t['Amount'] for t in transactions)
            
            per_bill_breach = False
            annual_threshold_breach = False
            tds_applicable = False
            reason = ""
            
            if rule['per_bill_limit'] and max_transaction >= rule['per_bill_limit']:
                per_bill_breach = True
                tds_applicable = True
                reason = f"Single transaction exceeds per-bill limit"
            
            if total_amount >= rule['threshold']:
                annual_threshold_breach = True
                tds_applicable = True
                if reason:
                    reason += " and "
                reason += f"Total exceeds threshold"
            
            if not tds_applicable:
                reason = f"Below threshold"
            
            tds_amount = (total_amount * rule['rate']) / 100 if tds_applicable else 0
            
            results.append({
                'Party Name': party_name,
                'Section': rule['section'],
                'Type': rule['type'],
                'Description': rule['description'],
                'Total Amount': round(total_amount, 2),
                'Threshold': rule['threshold'],
                'Per Bill Limit': rule['per_bill_limit'] if rule['per_bill_limit'] else 'N/A',
                'Rate': rule['rate'],
                'TDS/TCS Applicable': 'Yes' if tds_applicable else 'No',
                'TDS/TCS Amount': round(tds_amount, 2),
                'Reason': reason,
                'Transaction Count': len(transactions),
                'Max Transaction': round(max_transaction, 2),
                'Per Bill Breach': 'Yes' if per_bill_breach else 'No',
                'Threshold Breach': 'Yes' if annual_threshold_breach else 'No'
            })
        
        results.sort(key=lambda x: x['Total Amount'], reverse=True)
        return pd.DataFrame(results), pd.DataFrame(all_transactions_detail)

analyzer = TDSAnalyzer()

analyzer = TDSAnalyzer()

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/get_rules', methods=['GET'])
def get_rules():
    """Get all rules"""
    try:
        rules = analyzer.get_all_rules()
        return jsonify({'success': True, 'rules': rules})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/get_rule/<section>', methods=['GET'])
def get_rule(section):
    """Get a specific rule by section"""
    try:
        # First check in custom rules
        custom_rules = load_custom_rules()
        rule = next((r for r in custom_rules if r['section'] == section), None)
        
        if not rule:
            # If not in custom, check in default rules
            rule = next((r for r in analyzer.default_rules if r['section'] == section), None)
        
        if rule:
            return jsonify({'success': True, 'rule': rule})
        else:
            return jsonify({'success': False, 'error': f'Rule {section} not found'}), 404
    except Exception as e:
        import traceback
        print(traceback.format_exc())
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/add_custom_rule', methods=['POST'])
def add_custom_rule():
    """Add or update a custom rule"""
    try:
        new_rule = request.json
        custom_rules = load_custom_rules()
        
        # Check if section already exists
        existing_index = next((i for i, r in enumerate(custom_rules) if r['section'] == new_rule['section']), None)
        
        if existing_index is not None:
            # Update existing rule
            custom_rules[existing_index] = new_rule
            message = f"Rule {new_rule['section']} updated successfully"
        else:
            # Add new rule
            custom_rules.append(new_rule)
            message = f"Rule {new_rule['section']} added successfully"
        
        save_custom_rules(custom_rules)
        analyzer.refresh_rules()
        
        return jsonify({'success': True, 'message': message, 'updated': existing_index is not None})
    except Exception as e:
        import traceback
        print(traceback.format_exc())
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/update_custom_rule', methods=['POST'])
def update_custom_rule():
    """Update an existing custom rule"""
    try:
        updated_rule = request.json
        section = updated_rule.get('section')
        
        custom_rules = load_custom_rules()
        
        # Find and update the rule
        rule_index = next((i for i, r in enumerate(custom_rules) if r['section'] == section), None)
        
        if rule_index is not None:
            custom_rules[rule_index] = updated_rule
            save_custom_rules(custom_rules)
            analyzer.refresh_rules()
            return jsonify({'success': True, 'message': f'Rule {section} updated successfully'})
        else:
            return jsonify({'success': False, 'error': 'Rule not found'}), 404
    except Exception as e:
        import traceback
        print(traceback.format_exc())
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/delete_custom_rule', methods=['POST'])
def delete_custom_rule():
    """Delete a custom rule"""
    try:
        data = request.json
        section = data.get('section')
        custom_rules = load_custom_rules()
        
        # Filter out the rule to delete
        original_count = len(custom_rules)
        custom_rules = [r for r in custom_rules if r['section'] != section]
        
        if len(custom_rules) < original_count:
            save_custom_rules(custom_rules)
            analyzer.refresh_rules()
            return jsonify({'success': True, 'message': f'Rule {section} deleted successfully'})
        else:
            return jsonify({'success': False, 'error': 'Rule not found'}), 404
    except Exception as e:
        import traceback
        print(traceback.format_exc())
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/check_rule_exists/<section>', methods=['GET'])
def check_rule_exists(section):
    """Check if a rule section already exists"""
    try:
        custom_rules = load_custom_rules()
        exists_in_custom = any(r['section'] == section for r in custom_rules)
        exists_in_default = any(r['section'] == section for r in analyzer.default_rules)
        
        return jsonify({
            'success': True,
            'exists': exists_in_custom or exists_in_default,
            'in_custom': exists_in_custom,
            'in_default': exists_in_default
        })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/upload', methods=['POST'])
def upload_file():
    if 'file' not in request.files:
        return jsonify({'error': 'No file uploaded'}), 400
    
    file = request.files['file']
    if file.filename == '':
        return jsonify({'error': 'No file selected'}), 400
    
    filename = secure_filename(file.filename)
    file_ext = filename.rsplit('.', 1)[1].lower() if '.' in filename else ''
    
    try:
        if file_ext in ['xlsx', 'xls']:
            df = pd.read_excel(file)
        else:
            return jsonify({'error': 'Please upload Excel file (.xlsx, .xls)'}), 400
        
        required_cols = ['Date', 'Debit Ledger', 'Credit Ledger', 'Amount']
        missing = [col for col in required_cols if col not in df.columns]
        if missing:
            return jsonify({'error': f'Missing columns: {", ".join(missing)}'}), 400
        
        # Refresh rules before processing
        analyzer.refresh_rules()
        
        results, transactions_detail = analyzer.process_transactions(df)
        
        total_transactions_amount = float(df['Amount'].sum())
        total_tds_applicable_amount = float(results[results['TDS/TCS Applicable'] == 'Yes']['Total Amount'].sum())
        
        session.clear()
        session['results'] = results.to_json(orient='records')
        session['original_data'] = df.to_json(orient='records')
        session['transactions_detail'] = transactions_detail.to_json(orient='records')
        session['total_amount'] = total_transactions_amount
        
        return jsonify({
            'success': True,
            'message': f'Analyzed {len(df)} transactions successfully',
            'results': json_lib.loads(results.to_json(orient='records')),
            'total_transactions_amount': total_transactions_amount,
            'total_tds_applicable_amount': total_tds_applicable_amount
        })
    
    except Exception as e:
        import traceback
        print(traceback.format_exc())
        return jsonify({'error': str(e)}), 500

@app.route('/update_entry', methods=['POST'])
def update_entry():
    try:
        data = request.json
        party_name = data.get('party_name')
        field = data.get('field')
        value = data.get('value')
        
        if 'results' not in session:
            return jsonify({'error': 'No data available'}), 400
        
        results = pd.read_json(session['results'], orient='records')
        mask = results['Party Name'] == party_name
        
        if not mask.any():
            return jsonify({'error': f'Party {party_name} not found'}), 404
        
        if field == 'rate':
            try:
                new_rate = float(value)
                results.loc[mask, 'Rate'] = new_rate
                total_amount = results.loc[mask, 'Total Amount'].values[0]
                new_tds = (total_amount * new_rate) / 100
                results.loc[mask, 'TDS/TCS Amount'] = round(new_tds, 2)
            except ValueError:
                return jsonify({'error': 'Invalid rate value'}), 400
        elif field == 'section':
            results.loc[mask, 'Section'] = str(value)
        
        session['results'] = results.to_json(orient='records')
        
        return jsonify({
            'success': True, 
            'message': f'Updated {field} for {party_name}',
            'new_value': value
        })
    except Exception as e:
        import traceback
        print(traceback.format_exc())
        return jsonify({'error': str(e)}), 500

@app.route('/download/<format>')
def download(format):
    if 'results' not in session:
        return "No data available. Please upload a file first.", 400
    
    try:
        results = pd.read_json(session['results'], orient='records')
        original_data = pd.read_json(session['original_data'], orient='records')
        
        if 'transactions_detail' in session:
            transactions_detail = pd.read_json(session['transactions_detail'], orient='records')
        else:
            transactions_detail = original_data.copy()
            transactions_detail['TDS Section'] = 'N/A'
            transactions_detail['TDS Rate (%)'] = 0
            transactions_detail['TDS Amount'] = 0
            transactions_detail['Matched Keyword'] = 'N/A'
        
        if format == 'excel':
            output = io.BytesIO()
            with pd.ExcelWriter(output, engine='openpyxl') as writer:
                results.to_excel(writer, sheet_name='Summary', index=False)
                transactions_detail.to_excel(writer, sheet_name='Transaction Details', index=False)
                
                applicable = results[results['TDS/TCS Applicable'] == 'Yes']
                if len(applicable) > 0:
                    applicable.to_excel(writer, sheet_name='TDS_TCS_Payable', index=False)
                
                original_data.to_excel(writer, sheet_name='Original Data', index=False)
                
                total_amount = session.get('total_amount', float(original_data['Amount'].sum()))
                total_tds = float(applicable['TDS/TCS Amount'].sum()) if len(applicable) > 0 else 0.0
                
                stats = pd.DataFrame({
                    'Metric': [
                        'Total Transactions', 
                        'Total Amount (All Transactions)', 
                        'Parties Detected',
                        'TDS/TCS Applicable Parties', 
                        'Total TDS/TCS Amount'
                    ],
                    'Value': [
                        len(original_data),
                        f"₹{total_amount:,.2f}",
                        len(results),
                        len(applicable),
                        f"₹{total_tds:,.2f}"
                    ]
                })
                stats.to_excel(writer, sheet_name='Statistics', index=False)
            
            output.seek(0)
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            filename = f'TDS_TCS_Report_{timestamp}.xlsx'
            return send_file(output, download_name=filename, as_attachment=True)
        
        elif format == 'csv':
            output = io.BytesIO()
            results.to_csv(output, index=False)
            output.seek(0)
            return send_file(output, download_name='TDS_TCS_Report.csv', as_attachment=True)
        
        return "Invalid format", 400
    
    except Exception as e:
        import traceback
        print(traceback.format_exc())
        return f"Error: {str(e)}", 500

if __name__ == '__main__':
    print("=" * 80)
    print("TDS/TCS ANALYZER PRO - WITH CUSTOM RULES MANAGER")
    print("=" * 80)
    print("\nStarting server at: http://localhost:5000")
    print("\nFeatures:")
    print("  ✓ Auto-detect 29 TDS/TCS sections")
    print("  ✓ Custom Rules Manager (Add/Edit/Delete)")
    print("  ✓ Edit rates & sections in browser")
    print("  ✓ Export to Excel with 5 sheets")
    print("  ✓ Rules saved for future use")
    print("\nPress Ctrl+C to stop")
    print("=" * 80)
    app.run(debug=True, host='0.0.0.0', port=5000)

