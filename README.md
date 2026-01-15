# Wellnest - Health Analysis Web App

Wellnest is a Flask-based web application designed for health management and analysis. It allows users (patients and doctors) to analyze lab reports, check symptoms, and share insights through a dedicated doctor's forum. The app features user authentication, PDF text extraction for lab reports, and comparison functionalities.

## Features

- **User Authentication**: Secure signup and signin for patients and doctors with personalized dashboards.
- **Lab Report Analysis**: Upload and compare previous and latest lab reports in PDF format to track changes in test values.
- **Symptom Analysis**: Analyze symptoms for health insights (feature in development).
- **Doctor's Forum**: Exclusive forum for doctors to share lab report analyses, view shared analyses, and add comments.
- **PDF Text Extraction**: Uses pdfplumber to extract text from uploaded PDF lab reports.
- **Data Comparison**: Compares lab test values between reports and highlights changes (increased, decreased, or no change).

## Prerequisites

Before running the application, ensure you have the following installed:

- Python 3.7+
- Flask
- pdfplumber
- pandas
- Werkzeug (for security features)

## Installation

1. Clone the repository:

   ```bash
   git clone https://github.com/yourusername/wellnest.git
   cd wellnest
   ```

2. Create a virtual environment and activate it:

   ```bash
   python -m venv venv
   # On Windows:
   venv\Scripts\activate
   # On macOS/Linux:
   source venv/bin/activate
   ```

3. Install the required packages:

   ```bash
   pip install -r requirements.txt
   ```

4. Ensure the directory structure is in place (users folder will be created automatically):

   ```bash
   mkdir users
   ```

## Running the Application

1. Run the Flask application:

   ```bash
   python app.py
   ```

2. Open your browser and navigate to:

   ```
   http://127.0.0.1:5000/
   ```

## Usage

### Sign Up

1. Navigate to the main page and choose to sign up as a patient or doctor.
2. Enter your username, email, and password to create an account.
3. Patients get a user dashboard; doctors get a doctor dashboard with contribution tracking.

### Sign In

1. Enter your username and password on the signin page.
2. Access your personalized dashboard based on your user type.

### Analyze Lab Reports

1. From your dashboard, go to the lab report analysis page.
2. Upload both the previous and latest lab report PDFs.
3. The app extracts text, parses lab data, and compares test values.
4. View the comparison results, including changes in values.
5. Optionally, share the analysis to the doctor's forum (doctors only).

### Doctor's Forum

1. Doctors can access the forum to view shared analyses from other doctors.
2. View detailed analyses, add comments, and track contributions.
3. Shared analyses include patient names, test comparisons, and timestamps.

### Symptom Analysis

- Feature currently under development. Access via the symptom analyzer page.

## File Structure

```
├── app.py                          # Main Flask application
├── requirements.txt                # Python dependencies
├── users.txt                       # User credentials storage
├── shared_analyses.txt             # Shared analyses for doctor's forum
├── comments.txt                    # Comments on analyses
├── mnt/
│   └── data/
│       └── medicine_dataset.csv    # Medicine dataset (for future prescription features)
├── static/
│   ├── styles.css                  # Main stylesheet
│   └── pgstyles.css                # Additional styles
├── templates/
│   ├── 404.html                    # Error page
│   ├── doctor_dashboard.html       # Doctor's dashboard
│   ├── doctor_signup.html          # Doctor signup form
│   ├── doctors_forum.html          # Doctor's forum page
│   ├── first.html                  # Landing page
│   ├── index.html                  # Patient signup form
│   ├── lab_report_analysis.html    # Lab report analysis page
│   ├── prescription_analysis.html  # Prescription analysis (legacy)
│   ├── signin.html                 # Signin page
│   ├── symptom_analysis_result.html # Symptom analysis results
│   ├── symptom_analyzer.html       # Symptom analyzer page
│   ├── user.html                   # Patient dashboard
│   └── view_analysis.html          # View shared analysis details
└── users/
    └── (auto-generated HTML files for user dashboards)
```

## Dataset

The app includes a medicine dataset (`medicine_dataset.csv`) for potential future prescription analysis features, containing:

- **Name**: The name of the medicine.
- **Strength**: The strength (e.g., 500 mg).
- **Dosage Form**: The form in which the medicine is administered (e.g., tablet, syrup).

Currently, the primary focus is on lab report analysis.

## Security Note

- User passwords are hashed using Werkzeug's security functions.
- Session management is implemented for user authentication.
- File uploads are handled securely with Flask-Werkzeug.

## Contributing

Feel free to fork this repository and submit pull requests for improvements, new features, or bug fixes. Ensure to follow best practices for Flask applications and health data handling.

## License

This project is open-source. Please check the license file for details.