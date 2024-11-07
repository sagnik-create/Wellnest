import os
import re
import io
import pdfplumber
from flask import Flask, render_template, request, redirect, url_for, flash

app = Flask(__name__)
app.secret_key = 'sagnikd2345678900000000'

def extract_text_from_pdf(file_storage):
    text = ""
    try:
        pdf_bytes = file_storage.read()
        pdf_stream = io.BytesIO(pdf_bytes)
        with pdfplumber.open(pdf_stream) as pdf:
            for page in pdf.pages:
                text += page.extract_text() + "\n"
    except Exception as e:
        print(f"Error reading PDF file: {e}")
    return text

def extract_lab_data(report_text):
    name_pattern = r"Patient Name\s*:\s*([\w\s]+)"
    name_match = re.search(name_pattern, report_text)
    patient_name = name_match.group(1).strip() if name_match else "Unknown"

    test_data = {}
    sections = re.split(r'\n(?=[A-Z][a-z]+ Profile|DEPARTMENT OF)', report_text)
    
    for section in sections:
        section_name_match = re.match(r'([A-Z][a-z]+ Profile|DEPARTMENT OF [A-Z]+)', section)
        if section_name_match:
            section_name = section_name_match.group(1)
            test_data[section_name] = []
            
            pattern = r'([\w\s(),-]+?)\s*:\s*([\d.]+)\s*(\w+/?\w*)\s*([\d.\s-]+|[<>]=?\s*[\d.]+|[\w\s-]+)'
            matches = re.findall(pattern, section, re.MULTILINE)
            
            for match in matches:
                test_name, value, unit, reference_range = match
                try:
                    test_data[section_name].append({
                        'test_name': test_name.strip(),
                        'value': float(value) if value.replace('.', '').isdigit() else value,
                        'unit': unit.strip(),
                        'reference_range': reference_range.strip()
                    })
                except ValueError:
                    test_data[section_name].append({
                        'test_name': test_name.strip(),
                        'value': value.strip(),
                        'unit': unit.strip(),
                        'reference_range': reference_range.strip()
                    })

    return patient_name, test_data

def compare_lab_reports(prev_report, latest_report):
    comparison = []
    for section in prev_report.keys() & latest_report.keys():
        prev_tests = {test['test_name']: test for test in prev_report[section]}
        latest_tests = {test['test_name']: test for test in latest_report[section]}
        
        for test_name in prev_tests.keys() & latest_tests.keys():
            prev_test = prev_tests[test_name]
            latest_test = latest_tests[test_name]
            if isinstance(prev_test['value'], (int, float)) and isinstance(latest_test['value'], (int, float)):
                change = latest_test['value'] - prev_test['value']
                change_status = 'Increased' if change > 0 else 'Decreased' if change < 0 else 'No change'
            else:
                change = 'N/A'
                change_status = 'Cannot compare'
            comparison.append({
                'section': section,
                'test_name': test_name,
                'prev_value': prev_test['value'],
                'latest_value': latest_test['value'],
                'unit': prev_test['unit'],
                'reference_range': latest_test['reference_range'],
                'change': change_status
            })

    return comparison

@app.route('/')
def main_page():
    return render_template('first.html')

@app.route('/signup', methods=['GET', 'POST'])
def signup():
    if request.method == 'POST':
        username = request.form['username']
        email = request.form['email']
        password = request.form['password']
        with open('users.txt', 'a') as file:
            file.write(f"Username: {username}, Email: {email}, Password: {password}\n")
        user_html = render_template('user.html', username=username)
        user_file_path = os.path.join('users', f"{username}.html")
        os.makedirs(os.path.dirname(user_file_path), exist_ok=True)
        with open(user_file_path, 'w') as file:
            file.write(user_html)
        return redirect(url_for('user', username=username))
    else:
        return render_template('index.html')

@app.route('/signin', methods=['GET', 'POST'])
def signin():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        with open('users.txt', 'r') as file:
            for line in file:
                parts = line.strip().split(", ")
                if len(parts) == 3:
                    user_part = parts[0].split(": ")[1]
                    pass_part = parts[2].split(": ")[1]
                    if user_part == username and pass_part == password:
                        user_file_path = os.path.join('users', f"{username}.html")
                        if os.path.exists(user_file_path):
                            return redirect(url_for('user', username=username))
                        else:
                            flash('User page not found')
                            return redirect(url_for('signin'))
        flash('Invalid Username or Password')
        return redirect(url_for('signin'))
    return render_template('signin.html')

@app.route('/users/<username>')
def user(username):
    user_file_path = os.path.join('users', f"{username}.html")
    if os.path.exists(user_file_path):
        with open(user_file_path, 'r') as user_file:
            user_html = user_file.read()
        return user_html
    else:
        return 'User not found'

@app.route('/analyze_report/<username>', methods=['GET', 'POST'])
def analyze_report(username):
    if request.method == 'POST':
        prev_report_file = request.files.get('prev_report')
        latest_report_file = request.files.get('latest_report')

        if prev_report_file and latest_report_file:
            prev_report_text = extract_text_from_pdf(prev_report_file)
            latest_report_text = extract_text_from_pdf(latest_report_file)

            prev_patient_name, prev_report_data = extract_lab_data(prev_report_text)
            latest_patient_name, latest_report_data = extract_lab_data(latest_report_text)

            comparison_result = compare_lab_reports(prev_report_data, latest_report_data)

            return render_template('lab_report_analysis.html',
                                   username=username,
                                   prev_patient_name=prev_patient_name,
                                   latest_patient_name=latest_patient_name,
                                   comparison_result=comparison_result)
        else:
            return "No files received"
    else:
        return render_template('lab_report_analysis.html', username=username)

@app.route('/analyze_symptoms/<username>')
def analyze_symptoms(username):
    return render_template('symptoms_analysis.html', username=username)

if __name__ == '__main__':
    app.run(debug=True)