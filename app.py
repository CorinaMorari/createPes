from flask import Flask, request, jsonify, send_from_directory
from pyembroidery import read, write_pes, EmbThread
import os
import urllib.parse
import json

# Initialize Flask app
app = Flask(__name__)

# Configure upload folder
UPLOAD_FOLDER = './uploads'
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

# Function to convert HEX to RGB
def hex_to_rgb(hex_color):
    """Convert HEX color to RGB tuple."""
    hex_color = hex_color.lstrip('#')  # Remove '#' if present
    if len(hex_color) == 6:  # Ensure it's a 6-character hex
        return tuple(int(hex_color[i:i + 2], 16) for i in (0, 2, 4))
    else:
        raise ValueError(f"Invalid HEX color format: {hex_color}")

# Endpoint to create PES file with updated colors
@app.route('/create-pes', methods=['POST'])
def create_pes():
    # Check if a file is part of the request
    if 'dst_file' not in request.files:
        return jsonify({"error": "Missing DST file in request"}), 400

    dst_file = request.files['dst_file']  # The DST file uploaded by the user
    new_thread_colors = request.form.get('new_thread_colors')  # New colors in HEX format, e.g., ["#FF5733", "#33FF57"]

    if not new_thread_colors:
        return jsonify({"error": "Missing required parameter: 'new_thread_colors'"}), 400

    try:
        # Parse the new_thread_colors from the JSON string
        new_thread_colors = json.loads(new_thread_colors)  # Convert from string to list

        # Save the uploaded DST file temporarily
        dst_file_path = os.path.join(app.config['UPLOAD_FOLDER'], dst_file.filename)
        dst_file.save(dst_file_path)

        # Step 1: Read the DST file
        pattern = read(dst_file_path)

        # Step 2: Convert the new colors from HEX to RGB
        new_rgb_colors = []
        for hex_color in new_thread_colors:
            try:
                rgb = hex_to_rgb(hex_color)
                new_rgb_colors.append(rgb)
            except ValueError as e:
                return jsonify({"error": f"Invalid HEX color: {hex_color}"}), 400

        # Step 3: Update the threads in the pattern with the new colors
        updated_threads = []
        for i, thread in enumerate(pattern.threadlist):
            if i < len(new_rgb_colors):  # Ensure the new colors list matches the thread count
                new_rgb = new_rgb_colors[i]
                print(f"Updating thread {i} with RGB: {new_rgb}")  # Debugging line to see RGB values
                # Create a new EmbThread object with updated color
                new_thread = EmbThread(new_rgb[0], new_rgb[1], new_rgb[2])
                updated_threads.append(new_thread)
            else:
                updated_threads.append(thread)  # If no new color, keep the original thread

        # Update the threads in the pattern
        pattern.threadlist = updated_threads

        # Step 4: Save the new PES file
        pes_filename = 'updated_pattern.pes'
        pes_file_path = os.path.join(app.config['UPLOAD_FOLDER'], pes_filename)
        write_pes(pattern, pes_file_path)

        # Step 5: Return the URL of the new PES file
        base_url = 'https://createpes.onrender.com'  # Update with your domain or public URL
        pes_url = f'{base_url}/uploads/{urllib.parse.quote(pes_filename)}'

        return jsonify({"pes_file_url": pes_url})

    except Exception as e:
        return jsonify({"error": f"Failed to create PES file: {str(e)}"}), 500

# Route to serve the generated PES file
@app.route('/uploads/<filename>', methods=['GET'])
def download_pes(filename):
    return send_from_directory(app.config['UPLOAD_FOLDER'], filename)

if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0", port=8000)
