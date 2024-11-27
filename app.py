from flask import Flask, request, jsonify
from pyembroidery import EmbThread, EmbPattern, write_pes
import os
import urllib.parse

app = Flask(__name__)

# Set up the upload folder for storing generated PES files
app.config['UPLOAD_FOLDER'] = './uploads'

# Utility function to convert hex color to RGB
def hex_to_rgb(hex_color):
    hex_color = hex_color.lstrip('#')
    return tuple(int(hex_color[i:i+2], 16) for i in (0, 2, 4))

# Route to create a PES file
@app.route('/create-pes', methods=['POST'])
def create_pes():
    # Get data from the request
    data = request.json
    stitches = data.get('stitches')
    threads = data.get('threads')
    hex_colors = data.get('hex_colors')

    # Check if required data is provided
    if not stitches or not threads or not hex_colors:
        return jsonify({"error": "Missing required parameters: 'stitches', 'threads', or 'hex_colors'"}), 400

    # Create a new pattern for the embroidery
    pattern = EmbPattern()

    # Add threads to the pattern
    for thread_data in threads:
        # Get RGB values from the thread data
        r, g, b = thread_data['r'], thread_data['g'], thread_data['b']
        thread = EmbThread(r, g, b)
        pattern.add_thread(thread)

    # Update threads based on the hex color changes
    updated_threads = []
    for i, hex_color in enumerate(hex_colors):
        # Convert hex color to RGB
        r, g, b = hex_to_rgb(hex_color)
        # Replace the thread with the updated color
        updated_thread = EmbThread(r, g, b)
        updated_threads.append(updated_thread)

    # Apply updated threads to the pattern
    pattern.threadlist = updated_threads

    # Add stitches to the pattern
    for stitch_data in stitches:
        x, y, command = stitch_data['x'], stitch_data['y'], stitch_data['command']
        pattern.add_stitch(x, y, command)

    # Generate the PES file from the pattern
    pes_filename = 'generated_pattern.pes'
    pes_file_path = os.path.join(app.config['UPLOAD_FOLDER'], pes_filename)
    write_pes(pattern, pes_file_path)

    # Generate the URL for accessing the PES file
    base_url = 'https://createpes.onrender.com'  # Change this to your actual base URL
    pes_url = f'{base_url}/uploads/{urllib.parse.quote(pes_filename)}'

    # Return the URL of the generated PES file
    return jsonify({"pes_file_url": pes_url})

# Start the Flask application
if __name__ == '__main__':
    # Ensure the upload folder exists
    if not os.path.exists(app.config['UPLOAD_FOLDER']):
        os.makedirs(app.config['UPLOAD_FOLDER'])
    
    app.run(debug=True, host="0.0.0.0", port=8000)
