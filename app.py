from flask import Flask, request, jsonify
from pyembroidery import write_pes, EmbThread, EmbPattern
from flask_cors import CORS
import os

# Initialize Flask app
app = Flask(__name__)
CORS(app)  # Enable Cross-Origin Resource Sharing (CORS)

# Configure upload folder
UPLOAD_FOLDER = './uploads'
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

# Function to convert RGB to HEX format
def rgb_to_hex(rgb):
    return f'#{rgb[0]:02x}{rgb[1]:02x}{rgb[2]:02x}'

# Function to convert HEX to RGB format
def hex_to_rgb(hex_color):
    hex_color = hex_color.lstrip('#')
    return tuple(int(hex_color[i:i+2], 16) for i in (0, 2, 4))

# Function to create PES file from provided data
def create_pes_file(stitches, threads, hex_colors):
    # Convert hex colors to RGB
    thread_list = []
    for color in hex_colors:
        rgb = hex_to_rgb(color)
        thread_list.append(EmbThread(rgb[0], rgb[1], rgb[2]))  # Create EmbThread for each color
    
    # Create EmbPattern object
    pattern = EmbPattern()

    # Add threads to pattern
    for thread in thread_list:
        pattern.add_thread(thread)

    # Add stitches to pattern
    for stitch in stitches:
        # Assuming the stitch object contains x, y, command
        x, y, command = stitch['x'], stitch['y'], stitch['command']
        
        if command == "start":
            pattern.add_stitch(x, y, "start")
        elif command == "stitch":
            pattern.add_stitch(x, y, "stitch")
        elif command == "stop":
            pattern.add_stitch(x, y, "stop")
        elif command == "jump":
            pattern.add_stitch(x, y, "jump")

    # Generate PES file path
    pes_file_path = os.path.join(app.config['UPLOAD_FOLDER'], 'generated_pattern.pes')

    # Write PES file
    write_pes(pattern, pes_file_path)

    return pes_file_path

# Route to create PES from stitches, threads, and colors
@app.route('/create-pes', methods=['POST'])
def create_pes():
    data = request.json

    stitches = data.get('stitches')
    threads = data.get('threads')  # The threads parameter is passed but not directly used in this case
    hex_colors = data.get('hex_colors')

    if not stitches or not hex_colors:
        return jsonify({"error": "Missing required parameters: stitches or hex_colors"}), 400

    try:
        # Create PES file
        pes_file_path = create_pes_file(stitches, threads, hex_colors)

        # URL for the generated PES file (adjust domain as needed)
        base_url = 'https://dstupload.onrender.com'
        pes_file_url = f'{base_url}/uploads/{os.path.basename(pes_file_path)}'

        return jsonify({"pes_file_url": pes_file_url})
    
    except Exception as e:
        return jsonify({"error": f"Failed to create PES file: {str(e)}"}), 500

if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0", port=8000)
