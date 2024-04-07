from flask import Flask, render_template, request, redirect, url_for, flash
import os
import PyPDF2
import re

app = Flask(__name__)

# Prescription analyzer functions

def extract_medications(prescription_text):
    medication_pattern = r'\b(?:aspirin|ibuprofen|paracetamol|acetaminophen|tylenol|advil|aleve)\b'
    return set(re.findall(medication_pattern, prescription_text, flags=re.IGNORECASE))

def compare_prescriptions(prev_prescription, latest_prescription):
    prev_medications = extract_medications(prev_prescription)
    latest_medications = extract_medications(latest_prescription)

    continued_medications = prev_medications.intersection(latest_medications)
    new_medications = latest_medications - prev_medications
    restricted_medications = prev_medications - latest_medications

    return continued_medications, new_medications, restricted_medications

def extract_text_from_pdf(pdf_path):
    text = ""
    try:
        with open(pdf_path, "rb") as f:
            pdf_reader = PyPDF2.PdfReader(f)
            num_pages = len(pdf_reader.pages)
            for page_num in range(num_pages):
                page = pdf_reader.pages[page_num]
                text += page.extract_text()
    except PyPDF2._utils.PdfStreamError as e:
        print(f"Error reading PDF file: {e}")
    return text

# Flask routes

@app.route('/signup', methods=['GET', 'POST'])
def signup():
    if request.method == 'POST':
        # Retrieve form data
        username = request.form['username']
        email = request.form['email']
        password = request.form['password']

        # Store the data in a text file
        with open('users.txt', 'a') as file:
            file.write(f"Username: {username}, Email: {email}, Password: {password}\n")

        # Create a new HTML file for the user
        user_html = render_template('user.html', username=username)
        user_file_path = os.path.join('users', f"{username}.html")
        os.makedirs(os.path.dirname(user_file_path), exist_ok=True)
        with open(user_file_path, 'w') as file:
            file.write(user_html)

        return 'Sign up successful!'
    else:
        return render_template('index.html')

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
        prev_prescription_file = request.files['prev_prescription']
        latest_prescription_file = request.files['latest_prescription']

        prev_prescription_text = extract_text_from_pdf(prev_prescription_file)
        latest_prescription_text = extract_text_from_pdf(latest_prescription_file)

        continued_medications, new_medications, restricted_medications = compare_prescriptions(prev_prescription_text, latest_prescription_text)

        return render_template('prescription_analysis.html', 
                            username=username, 
                            continued_medications=continued_medications, 
                            new_medications=new_medications, 
                            restricted_medications=restricted_medications)
 

if __name__ == '__main__':
    app.run(debug=True)
