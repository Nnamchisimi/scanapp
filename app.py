from multiprocessing import Process
import sys
import os
import pandas as pd
from flask import Flask, render_template, request, jsonify
from PyQt5 import QtWidgets, QtCore, QtWebEngineWidgets
from PyQt5.QtWebEngineWidgets import QWebEngineView
import re

# Initialize Flask
app = Flask(__name__, static_folder="static", template_folder="templates")

upload_directory = "files"
if not os.path.exists(upload_directory):
    os.mkdir(upload_directory)

class WebsiteViewer(QtWidgets.QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Scan App")
        self.setGeometry(100, 100, 1280, 720)
        self.browser = QWebEngineView()
        self.setCentralWidget(self.browser)
        self.upload_file_path = None

        # Load webpage from Flask server
        self.browser.setUrl(QtCore.QUrl("http://127.0.0.1:5003/"))

@app.route("/")
def index():
    return render_template("index.html")

@app.route("/delete", methods=["POST"])
def delete_uploaded_file():
    # Get file path from the request (assuming it's passed in the request)
    file_path = request.form.get("file_path")
    if file_path and os.path.exists(file_path):
        os.remove(file_path)  # Remove the file
        return jsonify({"message": "Uploaded file has been removed successfully!"})
    else:
        return jsonify({"message": "No uploaded file found to delete."}), 400


@app.route("/upload", methods=["POST"])
def upload_file():
    if "upload_file" not in request.files:
        return jsonify({"message": "No file uploaded"}), 400

    file = request.files["upload_file"]
    if file.filename == "":
        return jsonify({"message": "No selected file"}), 400

    file_path = os.path.join(upload_directory, file.filename)
    file.save(file_path)
    return jsonify({"message": "File uploaded successfully", "file_path": file_path})

@app.route("/submit-form", methods=["POST"])
def handle_form_submission():
    try:
        # Extract data from form submission
        data = request.form.to_dict()
        part_number = data.get("part_number")
        raf_number = data.get("raf_number")
        num_pieces = int(data.get("num_pieces", 1))  # Default to 1 if not provided
        qr_code = data.get("qr_code")

        # Ensure part_number and raf_number are provided
        if not part_number or not raf_number:
            return jsonify({"message": "Part number and Raf number are required!"}), 400

        # Get the uploaded file and check its validity
        uploaded_file = request.files.get("upload_file")
        if not uploaded_file:
            return jsonify({"message": "No file uploaded!"}), 400

        file_path = os.path.join(upload_directory, uploaded_file.filename)

        if os.path.exists(file_path):
            # Read the existing Excel file
            print(f"Reading existing file: {file_path}")  # Debugging line
            df = pd.read_excel(file_path)

            # Clean up any extra spaces in column names
            df.columns = [col.strip() for col in df.columns]

            # Ensure required columns are present
            print("Columns:", df.columns)  # Debugging line
            if "Part number" not in df.columns or "Raf Number" not in df.columns:
                return jsonify({"message": "Missing required columns: 'Part number' or 'Raf Number' in the file"}), 400
        else:
            # If no file exists, create an empty DataFrame with the expected columns
            print(f"Creating new file at: {file_path}")  # Debugging line
            df = pd.DataFrame(columns=["Part number", "Raf Number", "Package Quantity", "No of pieces"])

        # If QR code is provided, extract the package quantity
        if qr_code:
            package_quantity = extract_value(qr_code)  # Extract value from the QR code
        else:
            # If no QR code, use the manually entered number as the package quantity
            package_quantity = num_pieces

        # Check if the row with the same part_number and raf_number exists
        existing_row = df[(df["Part number"] == part_number) & (df["Raf Number"] == raf_number)]

        if not existing_row.empty:
            # If the row exists, update the existing quantities
            index = existing_row.index[0]
            df.at[index, "No of pieces"] += num_pieces
            df.at[index, "Package Quantity"] += package_quantity  # Update Package Quantity with extracted or entered value
        else:
            # If the row doesn't exist, append a new row
            new_row = pd.DataFrame({
                "Part number": [part_number],
                "Raf Number": [raf_number],
                "Package Quantity": [package_quantity],  # Set Package Quantity to QR value or manual number
                "No of pieces": [num_pieces]
            })
            df = pd.concat([df, new_row], ignore_index=True)

        # Save the updated DataFrame back to the original Excel file (this will modify the uploaded file)
        print("Saving updated DataFrame to Excel")  # Debugging line
        df.to_excel(file_path, index=False)

        return jsonify({"message": "Data saved successfully!"})

    except Exception as e:
        # Catch any unexpected exceptions and return the error message
        return jsonify({"message": f"An error occurred: {str(e)}"}), 500

def extract_value(qr_code):
    """Extract the value after 'Q' from the QR code string, or return the manually entered number, or 'Not Found'."""
    
    # Condition 1: If qr_code is a string and it's a number (manually entered), return it directly
    if isinstance(qr_code, str) and qr_code.isdigit():
        return int(qr_code)  # Return the number directly
    
    # Condition 2: If qr_code matches the QR code pattern 'Q<number>', extract the value
    match = re.search(r'Q(\d+)', qr_code)
    if match:
        return int(match.group(1))  # Return the number after 'Q'
    
    # Condition 3: If neither condition is met, return "Not Found"
    return "Not Found"

def handle_request(self, request):
        # Parse the request data
        data = {key: value for key, value in request.form.items()}

        if request.method == 'POST':
            if 'delete' in data:
                return self.delete_uploaded_file()
            else:
                return self.handle_form_submission(data)


def run_flask():
    app.run(debug=True, host="127.0.0.1", port=5003, use_reloader=False)

if __name__ == "__main__":
    flask_process = Process(target=run_flask)
    flask_process.start()

    qt_app = QtWidgets.QApplication(sys.argv)
    window = WebsiteViewer()
    window.show()
    sys.exit(qt_app.exec_())