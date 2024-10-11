from flask import Flask, render_template, request, redirect, url_for, flash,session
import os
import PyPDF2
import re
import io
import pandas as pd
from flask_mail import Mail,Message
from apscheduler.schedulers.background import BackgroundScheduler
from datetime import datetime

# Load the medicine dataset
medicine_data = pd.read_csv('/workspaces/Medbud/mnt/data/medicine_dataset.csv')

app = Flask(__name__)
app.secret_key = 'sagnikd2345678900000000'

# Flask-Mail Configuration
app.config['MAIL_SERVER'] = 'smtp.gmail.com'  
app.config['MAIL_PORT'] = 587
app.config['MAIL_USE_TLS'] = True
app.config['MAIL_USERNAME'] = 'your_email@gmail.com'  
app.config['MAIL_PASSWORD'] = 'your_email_password'

mail = Mail(app)

# Initialize APScheduler
scheduler = BackgroundScheduler()
scheduler.start()

reminders_per_user = {}

# Function to extract text from the uploaded PDF
def extract_text_from_pdf(file_storage):
    text = ""
    try:
        pdf_bytes = file_storage.read()
        pdf_stream = io.BytesIO(pdf_bytes)
        pdf_reader = PyPDF2.PdfReader(pdf_stream)
        num_pages = len(pdf_reader.pages)
        for page_num in range(num_pages):
            page = pdf_reader.pages[page_num]
            text += page.extract_text()
    except PyPDF2.errors.PdfReadError as e:
        print(f"Error reading PDF file: {e}")
    return text

# Function to extract medications from prescription text
def extract_medications(prescription_text):
    # Pattern to extract medicine names and dosages from the text
    medication_pattern = r'Medicine name\s*–\s*(\w+)\s*Strength\s*-\s*(\d+\s*mg)'
    return re.findall(medication_pattern, prescription_text)

# Function to compare medications between prescriptions and with the dataset
def compare_prescriptions(prev_prescription, latest_prescription):
    prev_medications = extract_medications(prev_prescription)
    latest_medications = extract_medications(latest_prescription)
    
    prev_med_dict = {med: int(strength.replace(" mg", "")) for med, strength in prev_medications}
    latest_med_dict = {med: int(strength.replace(" mg", "")) for med, strength in latest_medications}

    # Find common medications between the two prescriptions
    common_medications = set(prev_med_dict.keys()).intersection(latest_med_dict.keys())

    result = {}
    
    for med in common_medications:
        prev_strength = prev_med_dict[med]
        latest_strength = latest_med_dict[med]

        # Check for strength in the dataset
        dataset_strength = medicine_data[medicine_data['Name'].str.contains(med, case=False, na=False)]
        if not dataset_strength.empty:
            dataset_strength_value = int(dataset_strength['Strength'].values[0].replace(" mg", ""))

            result[med] = {
                'previous_strength': prev_strength,
                'latest_strength': latest_strength,
                'dataset_strength': dataset_strength_value,
                'higher_strength': latest_strength > dataset_strength_value,
                'dosage_form': dataset_strength['Dosage Form'].values[0]
            }
    
    return result

# Function to present a series of multiple choice questions for the symptom analyzer
def get_symptom_questions():
    return [
        {"question": "Do you have a fever?", "options": ["Yes", "No"], "id": "fever"},
        {"question": "Are you experiencing a headache?", "options": ["Yes", "No"], "id": "headache"},
        {"question": "Do you have a sore throat?", "options": ["Yes", "No"], "id": "sore_throat"},
        {"question": "Do you have a cough?", "options": ["Yes", "No"], "id": "cough"},
        {"question": "Are you feeling nauseous?", "options": ["Yes", "No"], "id": "nausea"},
    ]

# Function to get user indications based on the multiple choice answers
def get_user_indications(answers):
    indications = []
    if answers.get('fever') == 'Yes':
        indications.append('Fever')
    if answers.get('headache') == 'Yes':
        indications.append('Headache')
    if answers.get('sore_throat') == 'Yes':
        indications.append('Sore Throat')
    if answers.get('cough') == 'Yes':
        indications.append('Cough')
    if answers.get('nausea') == 'Yes':
        indications.append('Nausea')
    return indications

# Function to suggest medicines based on indications
def suggest_medicines_for_indications(indications):
    suggested_medicines = {}
    
    for indication in indications:
        # Compare indications with the dataset to find suitable medicines
        matching_medicines = medicine_data[medicine_data['Indication'].str.contains(indication, case=False, na=False)]
        
        if not matching_medicines.empty:
            medicines = matching_medicines['Name'].tolist()
            suggested_medicines[indication] = medicines
    
    return suggested_medicines

def get_user_email(username):
    if not os.path.exists('users.txt'):
        return None
    with open('users.txt', 'r') as file:
        for line in file:
            parts = line.strip().split(", ")
            if len(parts) >= 2:
                user_part = parts[0].split(": ")[1].strip()
                email_part = parts[1].split(": ")[1].strip()
                if user_part.lower() == username.lower():
                    return email_part
    return None

def send_reminder_email(username, pill_name, time):
    user_email = get_user_email(username)
    if not user_email:
        print(f"No email found for user {username}")
        return

    msg = Message(subject="Medicine Reminder",
                  sender=app.config['MAIL_USERNAME'],
                  recipients=[user_email])
    msg.body = f"Hello {username},\n\nThis is your reminder to take your medicine: {pill_name} at {time}.\n\nStay Healthy!"
    mail.send(msg)
    print(f"Sent reminder to {user_email} for {pill_name} at {time}.")

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
        prescription_analysis_html = render_template('prescription_analysis.html', username=username)
        prescription_analysis_file_path = os.path.join('users', f"{username}_prescription_analysis.html")
        with open(prescription_analysis_file_path, 'w') as file:
            file.write(prescription_analysis_html)
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

@app.route('/logout')
def logout():
    session.pop('username', None)
    flash('You have been logged out.')
    return redirect(url_for('signin'))

@app.route('/users/<username>')
def user(username):
    user_file_path = os.path.join('users', f"{username}.html")
    if os.path.exists(user_file_path):
        with open(user_file_path, 'r') as user_file:
            user_html = user_file.read()
        return user_html
    else:
        return 'User not found'

@app.route('/analyze_prescription/<username>', methods=['GET', 'POST'])
def analyze_prescription(username):
    if request.method == 'POST':
        prev_prescription_file = request.files.get('prev_prescription')
        latest_prescription_file = request.files.get('latest_prescription')

        if prev_prescription_file and latest_prescription_file:
            prev_prescription_text = extract_text_from_pdf(prev_prescription_file)
            latest_prescription_text = extract_text_from_pdf(latest_prescription_file)

            comparison_result = compare_prescriptions(prev_prescription_text, latest_prescription_text)

            return render_template('prescription_analysis.html',
                                   username=username,
                                   prev_prescription_text=prev_prescription_text,
                                   latest_prescription_text=latest_prescription_text,
                                   comparison_result=comparison_result)
        else:
            return "No files received"
    else:
        return render_template('prescription_analysis.html', username=username)

@app.route('/analyze_symptoms/<username>', methods=['GET', 'POST'])
def analyze_symptoms(username):
    if request.method == 'POST':
        # Get user answers from the form submission
        answers = {key: request.form[key] for key in request.form.keys()}
        indications = get_user_indications(answers)
        
        # Get suggested medicines for the indications
        suggested_medicines = suggest_medicines_for_indications(indications)

        return render_template('symptom_analysis_result.html', 
                               username=username, 
                               indications=indications, 
                               suggested_medicines=suggested_medicines)
    else:
        questions = get_symptom_questions()
        return render_template('symptom_analyzer.html', username=username, questions=questions)

@app.route('/reminders', methods=['GET', 'POST'])
def reminders():
    if 'username' not in session:
        flash('You need to sign in first.')
        return redirect(url_for('signin'))

    username = session['username']

    if request.method == 'POST':
        pill_name = request.form.get('pill_name').strip()
        time_str = request.form.get('time').strip()

        if not pill_name or not time_str:
            flash('Both pill name and time are required.')
            return redirect(url_for('reminders'))

        # Validate time format HH:MM (24-hour)
        try:
            time_obj = datetime.strptime(time_str, '%H:%M')
            time_formatted = time_obj.strftime('%H:%M')
        except ValueError:
            flash('Invalid time format. Please use HH:MM in 24-hour format.')
            return redirect(url_for('reminders'))

        # Add reminder to the user's list
        reminders_per_user.setdefault(username, []).append({'pill_name': pill_name, 'time': time_formatted})
        flash('Reminder added successfully!')

        # Schedule the email reminder
        job_id = f"{username}_{pill_name}_{time_formatted}"
        scheduler.add_job(func=send_reminder_email,
                          trigger='cron',
                          hour=time_obj.hour,
                          minute=time_obj.minute,
                          args=[username, pill_name, time_formatted],
                          id=job_id,
                          replace_existing=True)

        return redirect(url_for('reminders'))

    user_reminders = reminders_per_user.get(username, [])
    return render_template('reminder.html', reminders=user_reminders)

@app.route('/remove_reminder/<int:index>')
def remove_reminder(index):
    if 'username' not in session:
        flash('You need to sign in first.')
        return redirect(url_for('signin'))

    username = session['username']
    user_reminders = reminders_per_user.get(username, [])

    if 0 <= index < len(user_reminders):
        reminder = user_reminders.pop(index)
        flash('Reminder removed successfully!')

        # Remove the scheduled job
        job_id = f"{username}_{reminder['pill_name']}_{reminder['time']}"
        scheduler.remove_job(job_id)

    else:
        flash('Invalid reminder index.')

    return redirect(url_for('reminders'))


if __name__ == '__main__':
    app.run(debug=True)
