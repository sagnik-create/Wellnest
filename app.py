from flask import Flask, render_template, request, redirect, url_for, flash
import os
import PyPDF2
import re
import io
import pandas as pd

# Load the medicine dataset
medicine_data = pd.read_csv('/workspaces/Medbud/mnt/data/medicine_dataset.csv')

app = Flask(__name__)
app.secret_key = 'sagnikd2345678900000000'

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

if __name__ == '__main__':
    app.run(debug=True)
