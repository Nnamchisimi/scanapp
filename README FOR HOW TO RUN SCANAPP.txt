READ ME!!!
steps to run the scanapp
best workıng versıon ıs ın the documents dırectory
, when uploadıng fıle use the one thats ot ınsıde the files folder thenn all tıngs work normally 
heres a copy of all the workıng codes 

APP.PY 


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




SCRIPT.JS


document.addEventListener('DOMContentLoaded', function () {
    const fileInput = document.getElementById('fileInput');
    const fileLabel = document.querySelector('.file-label');
    const deleteButton = document.getElementById('deleteButton');
    
    // Handle file input change (update file label text)
    fileInput.addEventListener('change', function () {
        if (fileInput.files.length > 0) {
            const fileName = fileInput.files[0].name;
            fileLabel.textContent = fileName;
            deleteButton.disabled = false;
        } else {
            fileLabel.textContent = 'No file Chosen';
            deleteButton.disabled = true;
        }
    });
    
    // Define the deleteFile function properly
    function deleteFile() {
        if (confirm('Are you sure you want to delete this file?')) {
            fileInput.value = '';  // Clear the file input
            fileLabel.textContent = 'No file Chosen';
            deleteButton.disabled = true;
        }
    }

    // Make sure the deleteButton's click event triggers the deleteFile function
    deleteButton.addEventListener('click', deleteFile);

    // Handle form submission with file upload
    document.getElementById('uploadForm').onsubmit = async function (event) {
        event.preventDefault(); // Prevent the default form submission

        const formData = new FormData(this);

        if (fileInput.files.length > 0) {
            formData.append('upload_file', fileInput.files[0]); // Append the uploaded file

            // Send the form data to the server via fetch
            try {
                const response = await fetch('/submit-form', {
                    method: 'POST',
                    body: formData
                });

                const result = await response.json();
                alert(result.message); // Display the response message from the server
            } catch (error) {
                alert('Error: ' + error.message); // Handle any errors that occur
            }

            // Reset form after submission
            const inputs = this.querySelectorAll('input[type="text"], input[type="number"]');
            inputs.forEach(input => input.value = '');
            //fileInput.value = '';  // Reset file input
            //fileLabel.textContent = 'No file Chosen';  // Reset file label
            deleteButton.disabled = false; // Disable delete button
        } else {
            alert('No file selected for upload!');
        }
    };
});


INDEX.HTML


<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>QR code Scanner</title>
    <link rel="stylesheet" href="{{ url_for('static', filename='css/style.css') }}">
</head>
<body>
    <!-- Header Image -->
    <img src="{{ url_for('static', filename='images/nlc.jpg') }}" alt="Logo" class="header-image">
    
    <div class="container">
        <form id="uploadForm" method="POST" enctype="multipart/form-data">
            <!-- Inputs for QR code, part number, raf number, and number of pieces -->
            <input type="text" name="qr_code" placeholder="Enter QR code or Number" autofocus required>
            <input type="text" name="part_number" placeholder="Enter Part Number" required>
            <input type="text" name="raf_number" placeholder="Enter Raf Number" required>
            <input type="number" name="num_pieces" placeholder="Enter number of pieces (default 1)" required>
            
            <!-- File input -->
            <div class="file-label">No file Chosen</div>
            <input type="file" name="upload_file" accept=".xls,.xlsx" id="fileInput">
            
            <!-- Submit and Delete buttons -->
            <input type="submit" value="Submit">
            <input type="button" value="Delete" id="deleteButton" onclick="deleteFile()">
        </form>
    </div>
    
    <script src="{{ url_for('static', filename='js/script.js') }}"></script>
</body>
</html>


STYLE.CSS


body{
    font-family: Arial, san-serif;
    background-image: url("../images/n.jpg");
    background-size: cover;
    background-repeat: no-repeat;
    background-position: center;
    height: 100vh;
    margin: 0;
    padding: 20px;
    color: white;
}
.header-image{
    display:block;
    margin: 0 auto 20px;
    height: auto;
    width: 15%;
}
.container{
    max-width: 400px;
    margin: auto;
    background-color: rgba(255, 255, 255, 0.8);
    border-radius: 8px;
    padding: 20px;
    box-shadow: 0 2px 10px rgba(0, 0, 0, 0.1);
}
form{
    display: flex;
    flex-direction: column;
    align-items: center;   
}

input[type="text"], input[type="file"], input[type="number"]{
    padding: 10px;
    font-size: 16px;
    border: 1px solid #ccc;
    border-radius: 4px;
    margin-bottom: 15px;
    width:100%;

}
input[type="submit"], input[type="button"]{
    padding: 10px 15px;
    font-size: 16px;
    border: none;
    border-radius: 4px;
    color: white;
    cursor: pointer;
    margin: 5px 0;
    width: 100px;
}
input[type="submit"]{
    background-color: #28a745;
}
input[type="submit"]:hover{
    background-color: #218838;
}
input[type="button"]{
    background-color: #dc3545;
}
input[type= "button"]:hover{
    background-color: #000000;
}
.file-label{
    margin-bottom: 10px;
    font-size: 16px;
    text-align: center;
    color: dimgrey;
}
h2{
    text-align: center;
    font-size: 14px;
    margin-top: 20px;
}