from flask import Flask, render_template, request, redirect, url_for, flash , session
import os
import PyPDF2
import re
import io

app = Flask(__name__)
app.secret_key = 'sagnikd2345678900000000'

reminders_per_user = {}

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

def extract_medications(prescription_text):
    # Expanded list of common medications
    medication_pattern = r'\b(?:aspirin|ibuprofen|paracetamol|acetaminophen|tylenol|advil|aleve|lisinopril|metformin|amlodipine|metoprolol|omeprazole|losartan|gabapentin|sertraline|levothyroxine|atorvastatin|simvastatin|citalopram|fluoxetine|escitalopram|bupropion|venlafaxine|duloxetine|trazodone|alprazolam|lorazepam|clonazepam|zolpidem|eszopiclone|pantoprazole|ranitidine|famotidine|cetirizine|loratadine|fexofenadine|montelukast|fluticasone|budesonide|albuterol|levalbuterol|tiotropium|prednisone|methylprednisolone|hydrocortisone|insulin|metformin|glipizide|glyburide|sitagliptin|pioglitazone|liraglutide|empagliflozin|warfarin|apixaban|rivaroxaban|clopidogrel|rosuvastatin|ezetimibe|fenofibrate|niacin|alendronate|risedronate|calcium|vitamin d|folic acid|cyanocobalamin|ferrous sulfate)\b'
    return set(re.findall(medication_pattern, prescription_text, flags=re.IGNORECASE))

def compare_prescriptions(prev_prescription, latest_prescription):
    prev_medications = extract_medications(prev_prescription)
    latest_medications = extract_medications(latest_prescription)
    common_medications = prev_medications.intersection(latest_medications)
    return common_medications

@app.route('/')
def main_page():
    return render_template('first.html')

@app.route('/signup', methods=['GET', 'POST'])
def signup():
    if request.method == 'POST':
        username = request.form['username'].strip()
        email = request.form['email'].strip()
        password = request.form['password'].strip()

        if not username or not email or not password:
            flash('All fields are required.')
            return redirect(url_for('signup'))

        # Check for existing username
        if os.path.exists('users.txt'):
            with open('users.txt', 'r') as file:
                for line in file:
                    parts = line.strip().split(", ")
                    if len(parts) >= 1:
                        user_part = parts[0].split(": ")[1]
                        if user_part.lower() == username.lower():
                            flash('Username already exists.')
                            return redirect(url_for('signup'))

        # Save user credentials
        with open('users.txt', 'a') as file:
            file.write(f"Username: {username}, Email: {email}, Password: {password}\n")

        # Initialize reminders for the user
        reminders_per_user[username] = []

        # Create user-specific HTML files
        user_html = render_template('user.html', username=username)
        user_file_path = os.path.join('users', f"{username}.html")
        os.makedirs(os.path.dirname(user_file_path), exist_ok=True)
        with open(user_file_path, 'w') as file:
            file.write(user_html)

        prescription_analysis_html = render_template('prescription_analysis.html', username=username)
        prescription_analysis_file_path = os.path.join('users', f"{username}_prescription_analysis.html")
        with open(prescription_analysis_file_path, 'w') as file:
            file.write(prescription_analysis_html)

        flash('Signup successful! Please sign in.')
        return redirect(url_for('signin'))
    else:
        return render_template('index.html')
    

@app.route('/signin', methods=['GET', 'POST'])
def signin():
    if request.method == 'POST':
        username = request.form['username'].strip()
        password = request.form['password'].strip()
        
        # Ensure both fields are filled out
        if not username or not password:
            flash('Both fields are required.')
            return redirect(url_for('signin'))
        
        user_found = False  # Flag to check if user is found
        with open('users.txt', 'r') as file:
            for line in file:
                parts = line.strip().split(", ")
                if len(parts) == 3:
                    user_part = parts[0].split(": ")[1].strip()  # Stripping whitespace
                    pass_part = parts[2].split(": ")[1].strip()  # Stripping whitespace
                    if user_part.lower() == username.lower() and pass_part == password:  # Case-insensitive username check
                        session['username'] = username  # Set session variable
                        user_file_path = os.path.join('users', f"{username}.html")
                        if os.path.exists(user_file_path):
                            return redirect(url_for('user', username=username))
                        else:
                            flash('User page not found.')
                            return redirect(url_for('signin'))
                        user_found = True
        
        if not user_found:
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

@app.route('/analyze_prescription/<username>', methods=['GET', 'POST'])
def analyze_prescription(username):
    if request.method == 'POST':
        prev_prescription_file = request.files.get('prev_prescription')
        latest_prescription_file = request.files.get('latest_prescription')

        if prev_prescription_file and latest_prescription_file:
            prev_prescription_text = extract_text_from_pdf(prev_prescription_file)
            latest_prescription_text = extract_text_from_pdf(latest_prescription_file)

            common_medications = compare_prescriptions(prev_prescription_text, latest_prescription_text)

            return render_template('prescription_analysis.html',
                                   username=username,
                                   prev_prescription_text=prev_prescription_text,
                                   latest_prescription_text=latest_prescription_text,
                                   common_medications=common_medications)
        else:
            return "No files received"
    else:
        return render_template('prescription_analysis.html', username=username)

@app.route('/reminder')
def reminders(username):
    if 'username' not in session:
        flash('You need to sign in first.')
        return redirect(url_for('signin'))
    username = session['username']
    user_reminders = reminders_per_user.get(username, [])
    return render_template('reminder.html', reminders=user_reminders)


@app.route('/reminder/<username>', methods=['GET', 'POST'])
def reminder(username):
    if request.method == 'POST':
        new_reminder = request.form.get('reminders')
        if username in reminders_per_user:
            reminders_per_user[username].append(new_reminder)
        else:
            reminders_per_user[username] = [new_reminder]
        return redirect(url_for('reminders', username=username))
    
    user_reminders = reminders_per_user.get(username, [])
    return render_template('reminder.html', username=username, reminders=user_reminders)


@app.route('/add_reminder/<username>', methods=['GET','POST'])
def add_reminder(username):
    if 'username' not in session:
        flash('You need to sign in first.')
        return redirect(url_for('signin'))
    
    username = session['username']
    pill_name = request.form.get('pill_name').strip()
    time = request.form.get('time').strip()
    
    if pill_name and time:
        reminders_per_user[username].append({'pill_name': pill_name, 'time': time})
        flash('Reminder added successfully!')
    else:
        flash('Please provide both pill name and time.')
    
    return redirect(url_for('reminder'))  # Redirect to the correct route



@app.route('/remove_reminder/<int:index>')
def remove_reminder(index):
    if 'username' not in session:
        flash('You need to sign in first.')
        return redirect(url_for('signin'))
    username = session['username']
    if 0 <= index < len(reminders_per_user.get(username, [])):
        reminders_per_user[username].pop(index)
        flash('Reminder removed successfully!')
    else:
        flash('Invalid reminder index.')
    return redirect(url_for('reminder'))  


if __name__ == '__main__':
    app.run(debug=True)