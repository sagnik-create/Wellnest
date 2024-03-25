from flask import Flask, render_template, request
import os
app = Flask(__name__)

@app.route('/signup', methods=['GET', 'POST'])
def signup():
    if request.method == 'POST':
        # Retrieve form data
        username = request.form['username']
        email = request.form['email']
        password = request.form['password']

        # You can perform additional validation or processing here

        # Store the data in a file or a database
        # Example: Store in a text file
        with open('users.txt', 'a') as file:
            file.write(f"Username: {username}, Email: {email}, Password: {password}\n")

        return 'Sign up successful!'
    else:
        return render_template('index.html')

@app.route('/entries/<entry_filename>')
def entry(entry_filename):
    entry_path = os.path.join('entries', entry_filename)
    if os.path.exists(entry_path):
        with open(entry_path, 'r') as entry_file:
            entry_html = entry_file.read()
        return entry_html
    else:
        return 'Entry not found'

if __name__ == '__main__':
    app.run(debug=True)