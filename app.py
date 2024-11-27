from flask import Flask, request, jsonify, send_from_directory
from pyembroidery import EmbThread, EmbPattern, write_pes
import os
import urllib.parse

# Initialize Flask app
app = Flask(__name__)

# Configure upload folder for PES files
UPLOAD_FOLDER = './uploads'
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

# Route to create PES file
@app.route('/create-pes', methods=['POST'])
def create_pes():
    data = request.json
    stitches = data.get('stitches')
    threads = data.get('threads')
    hex_colors = data.get('hex_colors')

    if not stitches or not threads or not hex_colors:
        return jsonify({"error": "Missing required parameters: 'stitches', 'threads', or 'hex_colors'"}), 400

    # Create a new pattern
    pattern = EmbPattern()

    # Add threads (adjusted to the provided color data)
    for thread_data in threads:
        thread = EmbThread(thread_data['r'], thread_data['g'], thread_data['b'])
        pattern.add_thread(thread)

    # Add stitches (add your stitch logic here)
    for stitch_data in stitches:
        x, y, command = stitch_data['x'], stitch_data['y'], stitch_data['command']
        pattern.add_stitch(x, y, command)

    # Generate PES file path
    pes_filename = 'generated_pattern.pes'
    pes_file_path = os.path.join(app.config['UPLOAD_FOLDER'], pes_filename)

    # Write PES file
    write_pes(pattern, pes_file_path)

    # Construct the URL to access the PES file
    base_url = 'https://createpes.onrender.com'  # Adjust this to your base URL
    pes_url = f'{base_url}/uploads/{urllib.parse.quote(pes_filename)}'

    return jsonify({"pes_file_url": pes_url})


# Route to serve the generated PES file
@app.route('/uploads/<filename>', methods=['GET'])
def download_pes(filename):
    return send_from_directory(app.config['UPLOAD_FOLDER'], filename)

if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0", port=8000)
