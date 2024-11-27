from flask import Flask, request, jsonify, send_from_directory
from pyembroidery import EmbThread, EmbPattern, write_pes, read
from flask_cors import CORS
import os
import urllib.parse

# Initialize Flask app
app = Flask(__name__)
CORS(app)  # Enable Cross-Origin Resource Sharing (CORS)

# Configure upload folder for PES files
UPLOAD_FOLDER = './uploads'
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

# Function to convert HEX to RGB
def hex_to_rgb(hex_color):
    hex_color = hex_color.lstrip('#')
    return tuple(int(hex_color[i:i + 2], 16) for i in (0, 2, 4))


# Function to update the threads based on updated hex colors
def update_threads_with_hex(pattern, hex_colors, threads):
    updated_threads = []

    # Create new threads based on the updated hex colors
    for i, hex_color in enumerate(hex_colors):
        rgb = hex_to_rgb(hex_color)
        new_thread = EmbThread(rgb[0], rgb[1], rgb[2])  # Create a new thread using RGB values
        updated_threads.append(new_thread)

    # Apply the updated threads to the pattern
    pattern.threadlist = updated_threads
    return pattern


# Route to handle the creation of PES file from an existing pattern with updated thread colors
@app.route('/create-pes-from-existing', methods=['POST'])
def create_pes_from_existing():
    data = request.json
    pattern_file = data.get('pattern_file')  # The existing pattern (PES file) to be updated
    hex_colors = data.get('hex_colors')  # The new hex colors to update threads

    if not pattern_file or not hex_colors:
        return jsonify({"error": "Missing required parameters: 'pattern_file' or 'hex_colors'"}), 400

    try:
        # Load the existing PES pattern
        pattern_file_path = os.path.join(app.config['UPLOAD_FOLDER'], pattern_file)
        pattern = read(pattern_file_path)

        # Update threads based on the new hex colors
        updated_pattern = update_threads_with_hex(pattern, hex_colors, pattern.threadlist)

        # Generate the updated PES file
        updated_pes_filename = f'updated_{pattern_file}'
        updated_pes_file_path = os.path.join(app.config['UPLOAD_FOLDER'], updated_pes_filename)
        write_pes(updated_pattern, updated_pes_file_path)

        # Construct the URL for the updated PES file
        base_url = 'https://createpes.onrender.com'  # Adjust with your domain or API base URL
        pes_url = f'{base_url}/uploads/{urllib.parse.quote(updated_pes_filename)}'

        return jsonify({"pes_file_url": pes_url})

    except Exception as e:
        return jsonify({"error": f"Failed to process pattern file: {str(e)}"}), 500


# Route to serve the generated PES file
@app.route('/uploads/<filename>', methods=['GET'])
def download_pes(filename):
    return send_from_directory(app.config['UPLOAD_FOLDER'], filename)


if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0", port=8000)
