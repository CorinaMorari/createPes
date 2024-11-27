from flask import Flask, request, jsonify
from pyembroidery import EmbThread, EmbPattern, read_pes, write_pes
import os
import urllib.parse
import requests

app = Flask(__name__)

# Set up the upload folder for storing generated PES files
app.config['UPLOAD_FOLDER'] = './uploads'

# Route to update thread colors in a PES file
@app.route('/update-thread-colors', methods=['POST'])
def update_thread_colors():
    # Get data from the request
    data = request.json
    pes_file_url = data.get('pes_file_url')  # URL to the PES file
    hex_colors = data.get('hex_colors')  # List of hex colors to update the threads

    # Check if required data is provided
    if not pes_file_url or not hex_colors:
        return jsonify({"error": "Missing required parameters: 'pes_file_url' or 'hex_colors'"}), 400

    # Download the PES file from the URL
    try:
        response = requests.get(pes_file_url)
        response.raise_for_status()
        pes_file_content = response.content
    except requests.exceptions.RequestException as e:
        return jsonify({"error": f"Failed to download PES file: {str(e)}"}), 400

    # Read the PES file using pyembroidery
    pattern = read_pes(pes_file_content)

    # Update threads based on the hex color changes
    for i, hex_color in enumerate(hex_colors):
        if i < len(pattern.threadlist):  # Ensure we do not exceed the number of threads
            # Update thread color using the set_hex_color() method
            pattern.threadlist[i].set_hex_color(hex_color)

    # Save the modified PES file to the upload folder
    pes_filename = 'updated_pattern.pes'
    pes_file_path = os.path.join(app.config['UPLOAD_FOLDER'], pes_filename)
    write_pes(pattern, pes_file_path)

    # Generate the URL for accessing the updated PES file
    base_url = 'https://createpes.onrender.com'  # Adjust to your actual base URL
    pes_url = f'{base_url}/uploads/{urllib.parse.quote(pes_filename)}'

    # Return the URL of the updated PES file
    return jsonify({"pes_file_url": pes_url})

# Start the Flask application
if __name__ == '__main__':
    # Ensure the upload folder exists
    if not os.path.exists(app.config['UPLOAD_FOLDER']):
        os.makedirs(app.config['UPLOAD_FOLDER'])
    
    app.run(debug=True, host="0.0.0.0", port=8000)
