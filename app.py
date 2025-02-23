from flask import Flask, request, jsonify, render_template, send_file, send_from_directory
from flask_cors import CORS
import google.genai as genai
import markdown  # Import markdown library to convert markdown to HTML
from inference_sdk import InferenceHTTPClient
from PIL import Image, ImageDraw, ImageFont
from dotenv import load_dotenv
import traceback
import os
import io

load_dotenv()

app = Flask(__name__)
CORS(app)

# Replace with your actual API key
GEM_API_KEY = "AIzaSyC9GysX1DVC_OZ3dZSQ_TMytXGA1e9Ff3w"  # Replace with your actual API key

# Initialize the GenAI client
client = genai.Client(api_key=GEM_API_KEY)

@app.route('/', methods=['GET'])
def home():
    return render_template("index.html")

@app.route('/chat', methods=['POST'])
def chat():
    user_message = request.json.get("message")
    initial_prompt = "You are a first aid assistant named SnapAI. The first input will be the first aid emergency and I want you to provide me with 3 to 5 steps on what to do. If you need to ask a follow-up question for more information go ahead. If the situation is severe recommend calling 911."  # Example prompt

    if not user_message:
        return jsonify({"error": "No message provided"}), 400

    try:
        # Combine the initial prompt with the user's message
        combined_prompt = initial_prompt + "\nUser: " + user_message

        # Use the genai client to send the request to the Gemini model
        response = client.models.generate_content(
            model="gemini-2.0-flash",  # Use the appropriate model
            contents=combined_prompt  # Send the combined prompt and user's message
        )

        # Convert the response from Gemini to HTML if it contains markdown
        if response.text:
            html_response = markdown.markdown(response.text)  # Convert markdown to HTML
            return jsonify({"response": html_response}), 200
        else:
            return jsonify({"error": "No response from Gemini"}), 500

    except Exception as e:
        return jsonify({"error": str(e)}), 500
    
client = InferenceHTTPClient(
    api_url = "http://localhost:9001",  # use the local inference server
    api_key="Ups9KQLQ0H6FQKTlonqT"
)

@app.route('/uploads/<filename>')
def uploaded_file(filename):
    return send_from_directory(os.getcwd(), filename)
    

@app.route('/process-image', methods=['POST'])
def process_image():
    try:
        # Get the image from the request
        if 'image' not in request.files:
            return jsonify({"error": "No image provided"}), 400

        image_file = request.files['image']
        image_path = "uploaded_image.jpg"
        image_file.save(image_path)

        client = InferenceHTTPClient(
            api_url="http://localhost:9001",  # use local inference server
            api_key="Ups9KQLQ0H6FQKTlonqT"
        )

        result = client.run_workflow(
            workspace_name="axxcess-2025",
            workflow_id="custom-workflow",
            images={"image": image_path}
        )

        if not result:
            return jsonify({"error": "No result returned from inference."}), 400

        # Assuming result is a list, process the first item (or adjust based on structure)
        predictions = result[0].get('predictions', {}).get('predictions', [])

        if not predictions:
            return jsonify({"error": "No predictions found"}), 400

        # Get the prediction with the highest confidence
        max_confidence_prediction = max(predictions, key=lambda p: p['confidence'])

        # Open the image and prepare to draw on it
        image = Image.open(image_path)
        draw = ImageDraw.Draw(image)

        # Get the coordinates and label from the prediction
        x = max_confidence_prediction['x']
        y = max_confidence_prediction['y']
        width = max_confidence_prediction['width']
        height = max_confidence_prediction['height']
        label = max_confidence_prediction['class']
        confidence = max_confidence_prediction['confidence']

        x1 = int(x - width / 2)
        y1 = int(y - height / 2)
        x2 = int(x + width / 2)
        y2 = int(y + height / 2)

        # Draw the bounding box
        draw.rectangle([x1, y1, x2, y2], outline="red", width=3)

        # Draw the label and confidence text
        label_text = f"{label} ({confidence * 100:.1f}%)"
        font = ImageFont.load_default()

        text_bbox = draw.textbbox((x1, y1), label_text, font=font)
        text_width = text_bbox[2] - text_bbox[0]
        text_height = text_bbox[3] - text_bbox[1]

        padding = 5
        draw.rectangle([x1, y1 - text_height - padding, x1 + text_width + padding, y1], fill="white")
        draw.text((x1 + padding, y1 - text_height - padding), label_text, fill="black", font=font)

        # Save the processed image
        output_image_path = "output_with_boxes_and_labels.jpg"
        image.save(output_image_path)

        # Return the processed image file
        return send_file(output_image_path, mimetype='image/jpeg')

    except Exception as e:
        error_message = f"Error processing image: {str(e)}"
        print(error_message)
        print(traceback.format_exc())  # Print detailed error stack trace
        return jsonify({"error": error_message}), 500



if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)
    
