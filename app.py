import os
import re
import io
import pdfplumber
from flask import Flask, render_template, request, redirect, url_for, flash, session
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime
import uuid


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
        user_type = request.form.get('user_type', 'patient')  # Default to 'patient' if not specified
        hashed_password = generate_password_hash(password)
        
        with open('users.txt', 'a') as file:
            file.write(f"Username: {username}, Email: {email}, Password: {hashed_password}, Type: {user_type}\n")
        
        if user_type == 'doctor':
            user_html = render_template('doctor_dashboard.html', username=username, contributions=0)
        else:
            user_html = render_template('user.html', username=username)
        
        user_file_path = os.path.join('users', f"{username}.html")
        os.makedirs(os.path.dirname(user_file_path), exist_ok=True)
        with open(user_file_path, 'w') as file:
            file.write(user_html)
        
        session['username'] = username
        session['user_type'] = user_type
        flash('Signup successful! Welcome to Wellnest.')
        return redirect(url_for('user', username=username))
    else:
        user_type = request.args.get('type', 'patient')
        if user_type == 'doctor':
            return render_template('doctor_signup.html')
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
                if len(parts) == 4:
                    user_part = parts[0].split(": ")[1]
                    pass_part = parts[2].split(": ")[1]
                    user_type = parts[3].split(": ")[1]
                    if user_part == username and check_password_hash(pass_part, password):
                        session['username'] = username
                        session['user_type'] = user_type
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
    if 'username' not in session or session['username'] != username:
        return redirect(url_for('signin'))
    user_file_path = os.path.join('users', f"{username}.html")
    if os.path.exists(user_file_path):
        with open(user_file_path, 'r') as user_file:
            user_html = user_file.read()
        return user_html
    else:
        return 'User not found'

@app.route('/analyze_report/<username>', methods=['GET', 'POST'])
def analyze_report(username):
    if 'username' not in session or session['username'] != username:
        return redirect(url_for('signin'))
    if request.method == 'POST':
        prev_report_file = request.files.get('prev_report')
        latest_report_file = request.files.get('latest_report')

        if prev_report_file and latest_report_file:
            prev_report_text = extract_text_from_pdf(prev_report_file)
            latest_report_text = extract_text_from_pdf(latest_report_file)

            prev_patient_name, prev_report_data = extract_lab_data(prev_report_text)
            latest_patient_name, latest_report_data = extract_lab_data(latest_report_text)

            comparison_result = compare_lab_reports(prev_report_data, latest_report_data)

            # Generate a unique analysis ID
            analysis_id = str(uuid.uuid4())

            # Prepare the analysis content
            analysis_content = f"Previous Patient: {prev_patient_name}\n"
            analysis_content += f"Latest Patient: {latest_patient_name}\n"
            analysis_content += str(comparison_result)

            return render_template('lab_report_analysis.html',
                                   username=username,
                                   prev_patient_name=prev_patient_name,
                                   latest_patient_name=latest_patient_name,
                                   comparison_result=comparison_result,
                                   analysis_id=analysis_id,
                                   analysis_content=analysis_content)
        else:
            return "No files received"
    else:
        return render_template('lab_report_analysis.html', username=username)

@app.route('/analyze_symptoms/<username>')
def analyze_symptoms(username):
    if 'username' not in session or session['username'] != username:
        return redirect(url_for('signin'))
    return render_template('symptoms_analysis.html', username=username)

@app.route('/doctors_forum')
def doctors_forum():
    if 'user_type' not in session or session['user_type'] != 'doctor':
        flash('You must be logged in as a doctor to access the forum.')
        return redirect(url_for('signin'))

    analyses = []
    with open('shared_analyses.txt', 'r') as file:
        for line in file:
            parts = line.strip().split('|')
            if len(parts) == 6:
                username, analysis_id, patient_name, analysis_type, timestamp, content = parts
                analyses.append({
                    'analysis_id': analysis_id,
                    'username': username,
                    'patient_name': patient_name,
                    'analysis_type': analysis_type,
                    'timestamp': timestamp,
                    'content': content
                })

    return render_template('doctors_forum.html', analyses=analyses)


@app.route('/share_analysis/<username>/<analysis_id>', methods=['POST'])
def share_analysis(username, analysis_id):
    if 'username' not in session or session['username'] != username:
        return redirect(url_for('signin'))
    
    analysis_content = request.form.get('analysis_content')
    patient_name = request.form.get('patient_name')
    analysis_type = "Lab Report Comparison"

    # Store the shared analysis information
    with open('shared_analyses.txt', 'a') as file:
        file.write(f"{username}|{analysis_id}|{patient_name}|{analysis_type}|{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}|{analysis_content}\n")

    flash('Analysis shared successfully to the Doctor\'s Forum')
    return redirect(url_for('analyze_report', username=username))

@app.route('/view_analysis/<analysis_id>')
def view_analysis(analysis_id):
    if 'user_type' not in session or session['user_type'] != 'doctor':
        flash('You must be logged in as a doctor to view analyses.')
        return redirect(url_for('signin'))

    analysis_details = None
    with open('shared_analyses.txt', 'r') as file:
        for line in file:
            parts = line.strip().split('|')
            if len(parts) == 6 and parts[1] == analysis_id:
                username, _, patient_name, analysis_type, timestamp, content = parts
                analysis_details = {
                    'analysis_id': analysis_id,
                    'username': username,
                    'patient_name': patient_name,
                    'analysis_type': analysis_type,
                    'timestamp': timestamp,
                    'content': content
                }
                break

    if analysis_details:
        return render_template(
            'view_analysis.html',
            analysis=analysis_details
        )
    
    flash('Analysis not found.')
    return redirect(url_for('doctors_forum'))


@app.errorhandler(404)
def page_not_found(e):
    return render_template('404.html'), 404


@app.route('/add_comment/<analysis_id>', methods=['POST'])
def add_comment(analysis_id):
    if 'user_type' not in session or session['user_type'] != 'doctor':
        return redirect(url_for('signin'))
    comment = request.form['comment']
    doctor_username = session['username']
    with open('comments.txt', 'a') as file:
        file.write(f"{analysis_id}, {doctor_username}, {comment}\n")
    # Increment the doctor's contribution count
    increment_contribution(doctor_username)
    flash('Comment added successfully')
    return redirect(url_for('view_analysis', analysis_id=analysis_id))

def increment_contribution(username):
    user_file_path = os.path.join('users', f"{username}.html")
    with open(user_file_path, 'r') as file:
        content = file.read()
    contributions = int(re.search(r'Contributions: (\d+)', content).group(1))
    new_content = content.replace(f'Contributions: {contributions}', f'Contributions: {contributions + 1}')
    with open(user_file_path, 'w') as file:
        file.write(new_content)

if __name__ == '__main__':
    app.run(debug=True)