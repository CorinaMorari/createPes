from flask import Flask, request, jsonify, send_from_directory
from pyembroidery import EmbThread, EmbPattern, write_pes
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


# Function to create and return an updated PES pattern
def create_pattern(stitches, threads, hex_colors):
    # Create a new pattern
    pattern = EmbPattern()

    # Add threads based on the provided hex colors
    updated_threads = []
    for i, hex_color in enumerate(hex_colors):
        rgb = hex_to_rgb(hex_color)
        new_thread = EmbThread(rgb[0], rgb[1], rgb[2])
        updated_threads.append(new_thread)

    # Apply the updated threads to the pattern
    pattern.threadlist = updated_threads

    # Add stitches to the pattern
    for stitch in stitches:
        x, y, command = stitch['x'], stitch['y'], stitch['command']
        
        if command == 1:  # "stitch"
            pattern.stitches.append((x, y))
        elif command == 2:  # "jump"
            pattern.jumps.append((x, y))
        elif command == 3:  # "trim" (example)
            pattern.trims.append((x, y))
        elif command == 4:  # "colorchange" (example)
            pattern.colorchanges.append((x, y))

    return pattern


# Route to handle creating PES file from provided stitches, threads, and hex_colors
@app.route('/create-pes', methods=['POST'])
def create_pes():
    data = request.json
    stitches = data.get('stitches')
    threads = data.get('threads')
    hex_colors = data.get('hex_colors')

    if not stitches or not threads or not hex_colors:
        return jsonify({"error": "Missing required parameters: 'stitches', 'threads', or 'hex_colors'"}), 400

    try:
        # Create the pattern from provided data
        pattern = create_pattern(stitches, threads, hex_colors)

        # Generate the PES file
        pes_filename = 'generated_pattern.pes'
        pes_file_path = os.path.join(app.config['UPLOAD_FOLDER'], pes_filename)
        write_pes(pattern, pes_file_path)

        # Construct the URL for the PES file
        base_url =  'https://createpes.onrender.com'  # Adjust with your domain or API base URL
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
