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

if __name__ == '__main__':
    app.run(debug=True)