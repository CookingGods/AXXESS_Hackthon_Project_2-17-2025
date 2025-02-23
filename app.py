from flask import Flask, request, jsonify, render_template, send_file, send_from_directory
from flask_cors import CORS
import google.genai as genai
import markdown
from inference_sdk import InferenceHTTPClient
from PIL import Image, ImageDraw, ImageFont
from dotenv import load_dotenv
import traceback
import os
import io

load_dotenv()

app = Flask(__name__, static_folder='static')
CORS(app)

GEM_API_KEY = os.getenv('gemini_api')

client = genai.Client(api_key=GEM_API_KEY)

@app.route('/', methods=['GET'])
def index():
    return render_template("index.html")

@app.route('/snapAI', methods=['GET'])
def snapAI():
    return render_template("snapAI.html")

@app.route('/Chatbot', methods=['GET'])
def Chatbot():
    return render_template("Chatbot.html")

@app.route('/Emergency', methods=['GET'])
def Emergency():
    return render_template("Emergency.html")

@app.route('/ERMAP', methods=['GET'])
def ERMAP():
    return render_template("ERMAP.html")


@app.route('/chat', methods=['POST'])
def chat():
    user_message = request.json.get("message")

    if not user_message:
        return jsonify({"error": "No message provided"}), 400

    try:
        response = client.models.generate_content(
            model="gemini-2.0-flash",
            contents=user_message 
        )

        # Convert the response from Gemini to HTML if it contains markdown
        if response.text:
            html_response = markdown.markdown(response.text)
            return jsonify({"response": html_response}), 200
        else:
            return jsonify({"error": "No response from Gemini"}), 500

    except Exception as e:
        return jsonify({"error": str(e)}), 500
    

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
            api_url="http://localhost:9001", 
            api_key= os.getenv('roboflow_api')
        )

        result = client.run_workflow(
            workspace_name="axxcess-2025",
            workflow_id="custom-workflow",
            images={"image": image_path}
        )

        if not result:
            return jsonify({"error": "No result returned from inference."}), 400

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
        if os.path.exists(output_image_path):
            os.remove(output_image_path)
            print("Removed existing output image")
        image.save(output_image_path)

        return send_file(output_image_path, mimetype='image/jpeg')
        #return jsonify({'label': label})


    except Exception as e:
        error_message = f"Error processing image: {str(e)}"
        print(error_message)
        print(traceback.format_exc())  
        return jsonify({"error": error_message}), 500



if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)
    
