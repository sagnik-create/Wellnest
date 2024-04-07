import PyPDF2
import re

def extract_medications(prescription_text):
    medication_pattern = r'\b(?:aspirin|ibuprofen|paracetamol|acetaminophen|tylenol|advil|aleve)\b'
    return set(re.findall(medication_pattern, prescription_text, flags=re.IGNORECASE))

def compare_prescriptions(prev_prescription, latest_prescription):
    prev_medications = extract_medications(prev_prescription)
    latest_medications = extract_medications(latest_prescription)

    # Identify medications continued from previous prescription
    continued_medications = prev_medications.intersection(latest_medications)

    # Identify new medications added in the latest prescription
    new_medications = latest_medications - prev_medications

    # Identify medications restricted (removed or dosage/frequency changed) in the latest prescription
    restricted_medications = prev_medications - latest_medications

    # Print results with text formatting
    print("[bold]Medications Continued from Previous Prescription:[/bold]")
    if continued_medications:
        print(", ".join(continued_medications))
    else:
        print("No medications continued from previous prescription.")

    print("\n[bold]New Medications Added in the Latest Prescription:[/bold]")
    if new_medications:
        print(", ".join(new_medications))
    else:
        print("No new medications added in the latest prescription.")

    print("\n[bold]Medications Restricted in the Latest Prescription:[/bold]")
    if restricted_medications:
        print(", ".join(restricted_medications))
    else:
        print("No medications restricted in the latest prescription.")


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


# Take user input for previous and latest prescriptions in PDF format
prev_pdf_path = input("Enter the path to the previous prescription PDF: ")
latest_pdf_path = input("Enter the path to the latest prescription PDF: ")

# Extract text from PDF files
prev_prescription_text = extract_text_from_pdf(prev_pdf_path)
latest_prescription_text = extract_text_from_pdf(latest_pdf_path)

# Compare the prescriptions
compare_prescriptions(prev_prescription_text, latest_prescription_text)