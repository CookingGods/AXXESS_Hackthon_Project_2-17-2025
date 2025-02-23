from flask import Flask, request, jsonify, render_template
import google.genai as genai
import markdown  # Import markdown library to convert markdown to HTML

app = Flask(__name__)

# Replace with your actual API key
API_KEY = "AIzaSyC9GysX1DVC_OZ3dZSQ_TMytXGA1e9Ff3w"  # Replace with your actual API key

# Initialize the GenAI client
client = genai.Client(api_key=API_KEY)

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

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)
