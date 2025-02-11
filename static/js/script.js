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
