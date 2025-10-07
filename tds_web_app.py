import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from flask import Flask, render_template, request, send_file, jsonify, session
import pdfplumber
import re
import io
import os
import json as json_lib
from werkzeug.utils import secure_filename

# --------------------------------------------------------------------------------------
# Flask app setup
# --------------------------------------------------------------------------------------
app = Flask(__name__)
app.secret_key = 'tds_analyzer_secret_key_2025'
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024
app.config['UPLOAD_FOLDER'] = 'uploads'
app.config['PERMANENT_SESSION_LIFETIME'] = timedelta(hours=4)

os.makedirs('uploads', exist_ok=True)

# Persistent fallback folder (so download works even after refresh/restart)
PERSIST_DIR = 'persist'
os.makedirs(PERSIST_DIR, exist_ok=True)
PERSIST_RESULTS = os.path.join(PERSIST_DIR, 'results.json')
PERSIST_ORIG = os.path.join(PERSIST_DIR, 'original_data.json')
PERSIST_TXN = os.path.join(PERSIST_DIR, 'transactions_detail.json')
PERSIST_META = os.path.join(PERSIST_DIR, 'meta.json')

# Custom rules file
CUSTOM_RULES_FILE = 'custom_rules.json'

# --------------------------------------------------------------------------------------
# Helpers: custom rules load/save
# --------------------------------------------------------------------------------------
def load_custom_rules():
    try:
        if os.path.exists(CUSTOM_RULES_FILE):
            with open(CUSTOM_RULES_FILE, 'r', encoding='utf-8') as f:
                return json_lib.load(f)
        return []
    except Exception as e:
        print(f"Error loading custom rules: {e}")
        return []

def save_custom_rules(rules):
    try:
        with open(CUSTOM_RULES_FILE, 'w', encoding='utf-8') as f:
            json_lib.dump(rules, f, indent=2, ensure_ascii=False)
        return True
    except Exception as e:
        print(f"Error saving custom rules: {e}")
        return False

# --------------------------------------------------------------------------------------
# Core Analyzer
# --------------------------------------------------------------------------------------
class TDSAnalyzer:
    """Complete TDS/TCS Analysis System with Custom Rules & PDF Support"""
    def __init__(self):
        self.default_rules = [
            # TDS
            {'section': '194A','threshold': 40000,'per_bill_limit': None,'rate': 10,'description': 'Interest other than on securities','keywords': ['interest','fd','fixed deposit','savings','recurring deposit'],'type': 'TDS','priority': 1,'search_in': 'credit','enabled': True,'custom': False},
            {'section': '194C','threshold': 100000,'per_bill_limit': 30000,'rate': 1,'description': 'Contractor Payments (Individual/HUF)','keywords': ['contractor','contract','construction','manufacturing'],'type': 'TDS','priority': 2,'search_in': 'credit','enabled': True,'custom': False},
            {'section': '194C','threshold': 100000,'per_bill_limit': 30000,'rate': 2,'description': 'Contractor Payments (Others)','keywords': ['contractor','contract','advertising','advertisement','catering','transport'],'type': 'TDS','priority': 2,'search_in': 'credit','enabled': True,'custom': False},
            {'section': '194D','threshold': 15000,'per_bill_limit': None,'rate': 5,'description': 'Insurance Commission','keywords': ['insurance commission','insurance agent','insurance broker'],'type': 'TDS','priority': 1,'search_in': 'credit','enabled': True,'custom': False},
            {'section': '194DA','threshold': 100000,'per_bill_limit': None,'rate': 2,'description': 'Life Insurance Policy Payment','keywords': ['life insurance','policy maturity','insurance payout'],'type': 'TDS','priority': 1,'search_in': 'credit','enabled': True,'custom': False},
            {'section': '194G','threshold': 15000,'per_bill_limit': None,'rate': 2,'description': 'Commission on lottery tickets','keywords': ['lottery commission','lottery ticket'],'type': 'TDS','priority': 1,'search_in': 'credit','enabled': True,'custom': False},
            {'section': '194H','threshold': 15000,'per_bill_limit': None,'rate': 5,'description': 'Commission or Brokerage','keywords': ['commission','brokerage','broker','agent'],'type': 'TDS','priority': 1,'search_in': 'credit','enabled': True,'custom': False},
            {'section': '194I','threshold': 240000,'per_bill_limit': None,'rate': 10,'description': 'Rent of land/building/furniture','keywords': ['rent','rental','lease','hire charges','godown','shop rent','office rent'],'type': 'TDS','priority': 1,'search_in': 'credit','enabled': True,'custom': False},
            {'section': '194I','threshold': 240000,'per_bill_limit': None,'rate': 2,'description': 'Rent of machinery/equipment','keywords': ['machinery rent','equipment rent','plant rent'],'type': 'TDS','priority': 1,'search_in': 'credit','enabled': True,'custom': False},
            {'section': '194J','threshold': 30000,'per_bill_limit': None,'rate': 10,'description': 'Professional or Technical Services','keywords': ['professional','consultancy','consulting','technical','legal','medical','engineering','architectural','accountancy','freelance','professional fees','technical services'],'type': 'TDS','priority': 1,'search_in': 'credit','enabled': True,'custom': False},
            {'section': '194J','threshold': 30000,'per_bill_limit': None,'rate': 2,'description': 'Technical services (call centre)','keywords': ['call centre','call center'],'type': 'TDS','priority': 1,'search_in': 'credit','enabled': True,'custom': False},
            {'section': '194K','threshold': 5000,'per_bill_limit': None,'rate': 10,'description': 'Income from mutual fund/UTI','keywords': ['mutual fund','uti','unit','dividend'],'type': 'TDS','priority': 1,'search_in': 'credit','enabled': True,'custom': False},
            {'section': '194LA','threshold': 250000,'per_bill_limit': None,'rate': 10,'description': 'Compensation on acquisition of property','keywords': ['compensation','acquisition','land acquisition'],'type': 'TDS','priority': 1,'search_in': 'credit','enabled': True,'custom': False},
            {'section': '194M','threshold': 5000000,'per_bill_limit': 5000000,'rate': 5,'description': 'Payment by individuals/HUF','keywords': ['contractor','professional','contract work'],'type': 'TDS','priority': 3,'search_in': 'credit','enabled': True,'custom': False},
            {'section': '194N','threshold': 10000000,'per_bill_limit': 2000000,'rate': 2,'description': 'Cash withdrawal','keywords': ['cash withdrawal','cash'],'type': 'TDS','priority': 1,'search_in': 'debit','enabled': True,'custom': False},
            {'section': '194O','threshold': 500000,'per_bill_limit': None,'rate': 1,'description': 'E-commerce participants','keywords': ['e-commerce','ecommerce','online marketplace'],'type': 'TDS','priority': 1,'search_in': 'credit','enabled': True,'custom': False},
            {'section': '194Q','threshold': 5000000,'per_bill_limit': None,'rate': 0.1,'description': 'Purchase of goods exceeding ₹50 lakhs','keywords': ['purchase','goods purchase','material purchase','purchase of goods'],'type': 'TDS','priority': 2,'search_in': 'credit','enabled': True,'custom': False},
            {'section': '194R','threshold': 20000,'per_bill_limit': None,'rate': 10,'description': 'Benefits or perquisites','keywords': ['benefit','perquisite','perk','incentive','reward'],'type': 'TDS','priority': 1,'search_in': 'credit','enabled': True,'custom': False},
            {'section': '194S','threshold': 50000,'per_bill_limit': 10000,'rate': 1,'description': 'Virtual digital assets','keywords': ['cryptocurrency','crypto','bitcoin','virtual asset','nft'],'type': 'TDS','priority': 1,'search_in': 'credit','enabled': True,'custom': False},
            {'section': '193','threshold': 10000,'per_bill_limit': None,'rate': 10,'description': 'Interest on securities','keywords': ['debenture','bond','security interest'],'type': 'TDS','priority': 1,'search_in': 'credit','enabled': True,'custom': False},
            {'section': '194B','threshold': 10000,'per_bill_limit': None,'rate': 30,'description': 'Lottery/puzzle winnings','keywords': ['lottery','puzzle','game show','winning'],'type': 'TDS','priority': 1,'search_in': 'credit','enabled': True,'custom': False},
            {'section': '194BA','threshold': 0,'per_bill_limit': None,'rate': 30,'description': 'Online gaming winnings','keywords': ['online game','gaming','online gambling'],'type': 'TDS','priority': 1,'search_in': 'credit','enabled': True,'custom': False},
            {'section': '194BB','threshold': 10000,'per_bill_limit': None,'rate': 30,'description': 'Horse race winnings','keywords': ['horse race','race winning'],'type': 'TDS','priority': 1,'search_in': 'credit','enabled': True,'custom': False},
            {'section': '194EE','threshold': 2500,'per_bill_limit': None,'rate': 10,'description': 'NSS payments','keywords': ['nss','national savings'],'type': 'TDS','priority': 1,'search_in': 'credit','enabled': True,'custom': False},
            {'section': '192','threshold': 0,'per_bill_limit': None,'rate': 0,'description': 'Salary (as per IT slab)','keywords': ['salary','wages','remuneration'],'type': 'TDS','priority': 1,'search_in': 'credit','enabled': True,'custom': False},
            {'section': '194IA','threshold': 5000000,'per_bill_limit': None,'rate': 1,'description': 'Sale of immovable property','keywords': ['sale of property','property sale','land sale'],'type': 'TDS','priority': 1,'search_in': 'credit','enabled': True,'custom': False},
            # TCS
            {'section': '206C(1H)','threshold': 5000000,'per_bill_limit': None,'rate': 0.1,'description': 'Sale of goods exceeding ₹50 lakhs','keywords': ['sales','goods sold','merchandise','sale invoice'],'type': 'TCS','priority': 3,'search_in': 'debit','enabled': True,'custom': False},
            {'section': '206C(1)','threshold': 0,'per_bill_limit': None,'rate': 1,'description': 'Sale of timber, forest produce, scrap','keywords': ['tendu','timber','forest','scrap','minerals'],'type': 'TCS','priority': 2,'search_in': 'debit','enabled': True,'custom': False},
            {'section': '206CCA','threshold': 700000,'per_bill_limit': None,'rate': 5,'description': 'Foreign remittance (LRS)','keywords': ['foreign remittance','liberalised remittance','lrs','overseas'],'type': 'TCS','priority': 1,'search_in': 'debit','enabled': True,'custom': False},
            {'section': '206C(1G)','threshold': 1000000,'per_bill_limit': None,'rate': 1,'description': 'Sale of motor vehicle','keywords': ['motor vehicle','car','vehicle sale','automobile'],'type': 'TCS','priority': 1,'search_in': 'debit','enabled': True,'custom': False},
        ]
        self.refresh_rules()

    def refresh_rules(self):
        custom = load_custom_rules()
        all_rules = self.default_rules.copy()
        all_rules.extend([{**r, 'custom': True} for r in custom])
        self.tds_rules = [r for r in all_rules if r.get('enabled', True)]

    def get_all_rules(self):
        custom = load_custom_rules()
        all_rules = self.default_rules.copy()
        all_rules.extend([{**r, 'custom': True} for r in custom])
        return all_rules

    # ---------------- PDF helpers ----------------
    def extract_text_from_pdf(self, file_bytes):
        text_pages = []
        try:
            with pdfplumber.open(io.BytesIO(file_bytes)) as pdf:
                for page in pdf.pages:
                    text_pages.append(page.extract_text() or "")
            return "\n".join(text_pages)
        except Exception as e:
            print(f"PDF extraction error: {e}")
            return ""

    def split_into_ledger_sections(self, text):
        pattern = re.compile(r"Account Statement For\s+(.+?)\nFrom\s+\d{2}/\d{2}/\d{4}", flags=re.S | re.I)
        matches = list(pattern.finditer(text))
        if not matches:
            return []
        sections = []
        for i, match in enumerate(matches):
            start = match.end()
            end = matches[i + 1].start() if i + 1 < len(matches) else len(text)
            sections.append((match.group(1).strip(), text[start:end]))
        return sections

    def extract_amounts_from_section(self, section_text):
        closing_balance = None
        close = re.search(r"Closing Balance\s*([\d,\.]+)", section_text, flags=re.I)
        if close:
            try:
                closing_balance = float(close.group(1).replace(",", ""))
            except:
                closing_balance = None
        amounts = re.findall(r"\b\d{1,3}(?:,\d{3})*(?:\.\d+)?\b", section_text)
        total = sum([float(a.replace(",", "")) for a in amounts]) if amounts else 0.0
        return total, closing_balance

    def parse_pdf_ledger(self, pdf_file):
        transactions = []
        try:
            pdf_bytes = pdf_file.read() if hasattr(pdf_file, 'read') else pdf_file
            text = self.extract_text_from_pdf(pdf_bytes)
            if not text:
                return pd.DataFrame()
            sections = self.split_into_ledger_sections(text)
            if not sections:
                # fallback: page-block aggregation (best-effort)
                blocks = [blk for blk in text.split('\n\n') if blk.strip()]
                for i, blk in enumerate(blocks, 1):
                    amounts = re.findall(r"\b\d{1,3}(?:,\d{3})*(?:\.\d+)?\b", blk)
                    total = sum([float(a.replace(",", "")) for a in amounts]) if amounts else 0.0
                    if total > 0:
                        transactions.append({
                            'Date': datetime.now().strftime('%Y-%m-%d'),
                            'Debit Ledger': 'Expense',
                            'Credit Ledger': f'PDF Section {i}',
                            'Voucher Type': 'Payment',
                            'Voucher No.': f'PDF-{i}',
                            'Amount': total
                        })
            else:
                for ledger_head, body in sections:
                    total_amount, closing_balance = self.extract_amounts_from_section(body)
                    amount = closing_balance if closing_balance else total_amount
                    if amount > 0:
                        transactions.append({
                            'Date': datetime.now().strftime('%Y-%m-%d'),
                            'Debit Ledger': 'Expense',
                            'Credit Ledger': ledger_head,
                            'Voucher Type': 'Payment',
                            'Voucher No.': f'PDF-{len(transactions)+1}',
                            'Amount': amount
                        })
        except Exception as e:
            print(f"PDF parsing error: {e}")
        return pd.DataFrame(transactions) if transactions else pd.DataFrame()

    # ---------------- Detection & processing ----------------
    def detect_tds_sections(self, transaction, rules):
        matches = []
        debit_lower = str(transaction['Debit Ledger']).lower()
        credit_lower = str(transaction['Credit Ledger']).lower()
        for rule in rules:
            for keyword in rule['keywords']:
                kw = keyword.lower()
                hit, where = False, None
                if rule['search_in'] in ['debit', 'both'] and kw in debit_lower:
                    hit, where = True, 'debit'
                if not hit and rule['search_in'] in ['credit', 'both'] and kw in credit_lower:
                    hit, where = True, 'credit'
                if hit:
                    conf = 'high' if kw in (debit_lower if where=='debit' else credit_lower).split() else 'medium'
                    matches.append({'rule': rule,'matched_keyword': keyword,'matched_in': where,'confidence': conf})
                    break
        matches.sort(key=lambda x: (x['rule']['priority'], {'high':0,'medium':1,'low':2}[x['confidence']]))
        return matches

    def process_transactions(self, df):
        grouped, details = {}, []
        for _, row in df.iterrows():
            matches = self.detect_tds_sections(row, self.tds_rules)
            details.append({
                'Date': row['Date'],
                'Debit Ledger': row['Debit Ledger'],
                'Credit Ledger': row['Credit Ledger'],
                'Voucher Type': row.get('Voucher Type','N/A'),
                'Voucher No': row.get('Voucher No.','N/A'),
                'Amount': row['Amount'],
                'TDS Section': matches[0]['rule']['section'] if matches else 'N/A',
                'TDS Rate (%)': matches[0]['rule']['rate'] if matches else 0,
                'TDS Amount': (row['Amount'] * matches[0]['rule']['rate'] / 100) if matches else 0,
                'Matched Keyword': matches[0]['matched_keyword'] if matches else 'N/A'
            })
            if not matches:
                continue
            rule = matches[0]['rule']
            party = row['Credit Ledger'] if rule['search_in']=='credit' else row['Debit Ledger']
            key = f"{party}|{rule['section']}"
            grouped.setdefault(key, {'transactions': [], 'rule': rule, 'party': party})
            grouped[key]['transactions'].append(row)

        results = []
        for key, data in grouped.items():
            txns, rule, party = data['transactions'], data['rule'], data['party']
            total = sum(t['Amount'] for t in txns)
            max_txn = max(t['Amount'] for t in txns)
            per_bill = bool(rule['per_bill_limit'] and max_txn >= rule['per_bill_limit'])
            annual = total >= rule['threshold']
            applicable = per_bill or annual
            reason = " and ".join([txt for txt in [
                "Single transaction exceeds per-bill limit" if per_bill else "",
                "Total exceeds threshold" if annual else ""
            ] if txt]) or "Below threshold"
            tds_amount = (total * rule['rate']) / 100 if applicable else 0
            results.append({
                'Party Name': party,
                'Section': rule['section'],
                'Type': rule['type'],
                'Description': rule['description'],
                'Total Amount': round(total, 2),
                'Threshold': rule['threshold'],
                'Per Bill Limit': rule['per_bill_limit'] if rule['per_bill_limit'] else 'N/A',
                'Rate': rule['rate'],
                'TDS/TCS Applicable': 'Yes' if applicable else 'No',
                'TDS/TCS Amount': round(tds_amount, 2),
                'Reason': reason,
                'Transaction Count': len(txns),
                'Max Transaction': round(max_txn, 2),
                'Per Bill Breach': 'Yes' if per_bill else 'No',
                'Threshold Breach': 'Yes' if annual else 'No'
            })
        results.sort(key=lambda x: x['Total Amount'], reverse=True)
        return pd.DataFrame(results), pd.DataFrame(details)

analyzer = TDSAnalyzer()

@app.before_request
def make_session_permanent():
    session.permanent = True

# --------------------------------------------------------------------------------------
# Pages
# --------------------------------------------------------------------------------------
@app.route('/')
def index():
    return render_template('index.html')

# --------------------------------------------------------------------------------------
# Rules Manager APIs
# --------------------------------------------------------------------------------------
@app.route('/get_rules', methods=['GET'])
def get_rules():
    try:
        return jsonify({'success': True, 'rules': analyzer.get_all_rules()})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/get_rule/<section>', methods=['GET'])
def get_rule(section):
    try:
        custom = load_custom_rules()
        rule = next((r for r in custom if r['section'] == section), None)
        if not rule:
            rule = next((r for r in analyzer.default_rules if r['section'] == section), None)
        if rule:
            return jsonify({'success': True, 'rule': rule})
        return jsonify({'success': False, 'error': 'Rule not found'}), 404
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/check_rule_exists/<section>', methods=['GET'])
def check_rule_exists(section):
    try:
        custom = load_custom_rules()
        in_custom = any(r['section'] == section for r in custom)
        in_default = any(r['section'] == section for r in analyzer.default_rules)
        return jsonify({'success': True, 'exists': in_custom or in_default, 'in_custom': in_custom, 'in_default': in_default})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/add_custom_rule', methods=['POST'])
def add_custom_rule():
    try:
        new_rule = request.json
        custom = load_custom_rules()
        idx = next((i for i, r in enumerate(custom) if r['section'] == new_rule['section']), None)
        if idx is not None:
            custom[idx] = new_rule
            msg, updated = f"Rule {new_rule['section']} updated successfully", True
        else:
            custom.append(new_rule)
            msg, updated = f"Rule {new_rule['section']} added successfully", False
        save_custom_rules(custom)
        analyzer.refresh_rules()
        return jsonify({'success': True, 'message': msg, 'updated': updated})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/update_custom_rule', methods=['POST'])
def update_custom_rule():
    try:
        upd = request.json
        section = upd.get('section')
        custom = load_custom_rules()
        idx = next((i for i, r in enumerate(custom) if r['section'] == section), None)
        if idx is None:
            return jsonify({'success': False, 'error': 'Rule not found'}), 404
        custom[idx] = upd
        save_custom_rules(custom)
        analyzer.refresh_rules()
        return jsonify({'success': True, 'message': f'Rule {section} updated successfully'})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/delete_custom_rule', methods=['POST'])
def delete_custom_rule():
    try:
        section = request.json.get('section')
        custom = load_custom_rules()
        new_rules = [r for r in custom if r['section'] != section]
        if len(new_rules) == len(custom):
            return jsonify({'success': False, 'error': 'Rule not found'}), 404
        save_custom_rules(new_rules)
        analyzer.refresh_rules()
        return jsonify({'success': True, 'message': f'Rule {section} deleted successfully'})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/toggle_rule', methods=['POST'])
def toggle_rule():
    try:
        section = request.json.get('section')
        enabled = bool(request.json.get('enabled', True))
        custom = load_custom_rules()
        for r in custom:
            if r['section'] == section:
                r['enabled'] = enabled
                save_custom_rules(custom)
                analyzer.refresh_rules()
                return jsonify({'success': True, 'message': f'Rule {section} {"enabled" if enabled else "disabled"}'})
        return jsonify({'success': False, 'error': 'Rule not found'}), 404
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

# --------------------------------------------------------------------------------------
# Upload & Analyze (Excel + PDF)
# --------------------------------------------------------------------------------------
@app.route('/upload', methods=['POST'])
def upload_file():
    if 'file' not in request.files:
        return jsonify({'error': 'No file uploaded'}), 400
    file = request.files['file']
    if file.filename == '':
        return jsonify({'error': 'No file selected'}), 400

    filename = secure_filename(file.filename)
    ext = filename.rsplit('.', 1)[1].lower() if '.' in filename else ''
    try:
        if ext in ['xlsx', 'xls']:
            df = pd.read_excel(file)
        elif ext == 'pdf':
            df = analyzer.parse_pdf_ledger(file)
            if df.empty:
                return jsonify({'error': 'Could not extract data from PDF. Please check format.'}), 400
        else:
            return jsonify({'error': 'Please upload Excel (.xlsx, .xls) or PDF (.pdf)'}), 400

        required = ['Date','Debit Ledger','Credit Ledger','Amount']
        missing = [c for c in required if c not in df.columns]
        if missing:
            return jsonify({'error': f'Missing columns: {", ".join(missing)}'}), 400

        analyzer.refresh_rules()
        results, tx_detail = analyzer.process_transactions(df)

        total_amt = float(df['Amount'].sum())
        total_tds_base = float(results.loc[results['TDS/TCS Applicable']=='Yes','Total Amount'].sum())

        session.clear()
        session['results'] = results.to_json(orient='records')
        session['original_data'] = df.to_json(orient='records')
        session['transactions_detail'] = tx_detail.to_json(orient='records')
        session['total_amount'] = total_amt

        # Persist to disk (fallback)
        with open(PERSIST_RESULTS, 'w', encoding='utf-8') as f: f.write(results.to_json(orient='records'))
        with open(PERSIST_ORIG, 'w', encoding='utf-8') as f: f.write(df.to_json(orient='records'))
        with open(PERSIST_TXN, 'w', encoding='utf-8') as f: f.write(tx_detail.to_json(orient='records'))
        with open(PERSIST_META, 'w', encoding='utf-8') as f: json_lib.dump({'total_amount': total_amt}, f)

        return jsonify({
            'success': True,
            'message': f'Analyzed {len(df)} transactions successfully',
            'results': json_lib.loads(results.to_json(orient='records')),
            'total_transactions_amount': total_amt,
            'total_tds_applicable_amount': total_tds_base
        })
    except Exception as e:
        import traceback
        print(traceback.format_exc())
        return jsonify({'error': str(e)}), 500

# --------------------------------------------------------------------------------------
# Inline edits (party-level)
# --------------------------------------------------------------------------------------
@app.route('/update_entry', methods=['POST'])
def update_entry():
    try:
        data = request.json
        party = data.get('party_name')
        field = data.get('field')
        value = data.get('value')

        if 'results' not in session:
            return jsonify({'error': 'No data available'}), 400

        results = pd.read_json(session['results'], orient='records')
        mask = results['Party Name'] == party
        if not mask.any():
            return jsonify({'error': f'Party {party} not found'}), 404

        if field == 'rate':
            try:
                new_rate = float(value)
            except ValueError:
                return jsonify({'error': 'Invalid rate value'}), 400
            results.loc[mask, 'Rate'] = new_rate
            base = results.loc[mask, 'Total Amount'].values[0]
            results.loc[mask, 'TDS/TCS Amount'] = round(base * new_rate / 100.0, 2)
        elif field == 'section':
            results.loc[mask, 'Section'] = str(value)
        else:
            return jsonify({'error': 'Unsupported field'}), 400

        session['results'] = results.to_json(orient='records')
        # Update persisted results as well
        with open(PERSIST_RESULTS, 'w', encoding='utf-8') as f: f.write(results.to_json(orient='records'))

        return jsonify({'success': True, 'message': f'Updated {field} for {party}', 'new_value': value})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

# --------------------------------------------------------------------------------------
# Download (uses session; falls back to persisted files)
# --------------------------------------------------------------------------------------
@app.route('/download/<format>')
def download(format):
    try:
        if 'results' in session and 'original_data' in session:
            results = pd.read_json(session['results'], orient='records')
            original = pd.read_json(session['original_data'], orient='records')
            tx_detail = pd.read_json(session.get('transactions_detail', '[]'), orient='records')
            total_amount = session.get('total_amount', float(original['Amount'].sum()) if 'Amount' in original.columns else 0.0)
        else:
            # Fallback to persisted data if session is empty
            if not (os.path.exists(PERSIST_RESULTS) and os.path.exists(PERSIST_ORIG)):
                return jsonify({'error': 'No data available. Please upload and analyze a file first.'}), 400
            results = pd.read_json(PERSIST_RESULTS, orient='records')
            original = pd.read_json(PERSIST_ORIG, orient='records')
            tx_detail = pd.read_json(PERSIST_TXN, orient='records') if os.path.exists(PERSIST_TXN) else pd.DataFrame()
            meta = json_lib.load(open(PERSIST_META, 'r', encoding='utf-8')) if os.path.exists(PERSIST_META) else {}
            total_amount = meta.get('total_amount', float(original['Amount'].sum()) if 'Amount' in original.columns else 0.0)

        if tx_detail.empty:
            tx_detail = original.copy()
            for col, val in [('TDS Section','N/A'),('TDS Rate (%)',0),('TDS Amount',0),('Matched Keyword','N/A')]:
                if col not in tx_detail.columns: tx_detail[col] = val

        applicable = results.loc[results['TDS/TCS Applicable'] == 'Yes'] if not results.empty else pd.DataFrame()

        if format == 'excel':
            output = io.BytesIO()
            with pd.ExcelWriter(output, engine='openpyxl') as writer:
                results.to_excel(writer, sheet_name='Summary', index=False)
                tx_detail.to_excel(writer, sheet_name='Transaction Details', index=False)
                if len(applicable) > 0:
                    applicable.to_excel(writer, sheet_name='TDS_TCS_Payable', index=False)
                original.to_excel(writer, sheet_name='Original Data', index=False)
                stats = pd.DataFrame({
                    'Metric': ['Total Transactions','Total Amount (All Transactions)','Parties Detected','TDS/TCS Applicable Parties','Total TDS/TCS Amount'],
                    'Value': [len(original), f"₹{total_amount:,.2f}", len(results), len(applicable), f"₹{float(applicable['TDS/TCS Amount'].sum() if 'TDS/TCS Amount' in applicable.columns else 0):,.2f}"]
                })
                stats.to_excel(writer, sheet_name='Statistics', index=False)
            output.seek(0)
            ts = datetime.now().strftime('%Y%m%d_%H%M%S')
            return send_file(output, download_name=f'TDS_TCS_Report_{ts}.xlsx', as_attachment=True)

        if format == 'csv':
            output = io.BytesIO()
            results.to_csv(output, index=False)
            output.seek(0)
            ts = datetime.now().strftime('%Y%m%d_%H%M%S')
            return send_file(output, download_name=f'TDS_TCS_Report_{ts}.csv', as_attachment=True)

        return jsonify({'error': "Invalid format. Use 'excel' or 'csv'"}), 400
    except Exception as e:
        import traceback
        print(traceback.format_exc())
        return jsonify({'error': f"Error generating download: {str(e)}"}), 500

# --------------------------------------------------------------------------------------
# Debug helper (optional)
# --------------------------------------------------------------------------------------
@app.route('/_debug_session')
def _debug_session():
    return jsonify({
        'host': request.host,
        'has_results': 'results' in session,
        'has_original_data': 'original_data' in session,
        'has_txn_detail': 'transactions_detail' in session,
        'persist_files': {
            'results': os.path.exists(PERSIST_RESULTS),
            'original': os.path.exists(PERSIST_ORIG),
            'transactions': os.path.exists(PERSIST_TXN),
            'meta': os.path.exists(PERSIST_META),
        }
    })

# --------------------------------------------------------------------------------------
# Run
# --------------------------------------------------------------------------------------
if __name__ == '__main__':
    print("=" * 80)
    print("TDS/TCS ANALYZER PRO - PERSISTENT DOWNLOAD + PDF SUPPORT")
    print("=" * 80)
    print("Open: http://localhost:5000")
    print("Features:")
    print("  ✓ Upload Excel & PDF")
    print("  ✓ Custom Rules Manager (Add/Update/Delete)")
    print("  ✓ Edit rates/sections inline")
    print("  ✓ Export Excel (5 sheets) + CSV")
    print("  ✓ Persistent fallback for downloads")
    print("=" * 80)
    app.run(debug=True, host='0.0.0.0', port=5000)
