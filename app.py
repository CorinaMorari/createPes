from flask import Flask, request, jsonify, send_from_directory
from pyembroidery import read, write_pes, EmbThread, EmbPattern
import os
import urllib.parse

# Initialize Flask app
app = Flask(__name__)

# Configure upload folder
UPLOAD_FOLDER = './uploads'
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

# Function to convert HEX to RGB
def hex_to_rgb(hex_color):
    hex_color = hex_color.lstrip('#')
    return tuple(int(hex_color[i:i + 2], 16) for i in (0, 2, 4))

# Endpoint to create PES file with updated colors
@app.route('/create-pes', methods=['POST'])
def create_pes():
    data = request.json
    dst_file_path = data.get('dst_file_path')  # Path to the DST file
    new_thread_colors = data.get('new_thread_colors')  # New colors in HEX format, e.g., ["#FF5733", "#33FF57"]

    if not dst_file_path or not new_thread_colors:
        return jsonify({"error": "Missing required parameters: 'dst_file_path' or 'new_thread_colors'"}), 400

    try:
        # Step 1: Read the DST file
        pattern = read(dst_file_path)

        # Step 2: Convert the new colors from HEX to RGB
        new_rgb_colors = [hex_to_rgb(hex_color) for hex_color in new_thread_colors]

        # Step 3: Update the threads in the pattern with the new colors
        updated_threads = []
        for i, thread in enumerate(pattern.threadlist):
            if i < len(new_rgb_colors):  # Ensure the new colors list matches the thread count
                new_rgb = new_rgb_colors[i]
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
        base_url = 'https://your-domain.com'  # Update with your domain or public URL
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
