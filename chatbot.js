import { useState } from "react";
import axios from "axios";

export default function Chatbot() {
  const [messages, setMessages] = useState([]);
  const [userInput, setUserInput] = useState("");

  const API_URL = "https://api.gemini.com/chat"; // Replace with your actual API URL
  const API_KEY = "AIzaSyC9GysX1DVC_OZ3dZSQ_TMytXGA1e9Ff3w"; // Replace with your actual API key

  const handleSendMessage = async () => {
    if (userInput.trim() === "") return;

    const newMessages = [...messages, { sender: "user", text: userInput }];
    setMessages(newMessages);
    setUserInput("");

    try {
      const response = await axios.post(API_URL, {
        prompt: userInput,
        apiKey: API_KEY,
      });

      setMessages([
        ...newMessages,
        { sender: "gemini", text: response.data.text },
      ]);
    } catch (error) {
      console.error("Error calling Gemini API:", error);
      setMessages([
        ...newMessages,
        { sender: "gemini", text: "Sorry, there was an error." },
      ]);
    }
  };

  return (
    <div className="chatbot-container">
      <div className="chat-window">
        <div className="chat-messages">
          {messages.map((msg, index) => (
            <div key={index} className={`message ${msg.sender}`}>
              <p>{msg.text}</p>
            </div>
          ))}
        </div>
      </div>
      <div className="chat-input">
        <input
          type="text"
          value={userInput}
          onChange={(e) => setUserInput(e.target.value)}
          placeholder="Type your message..."
        />
        <button onClick={handleSendMessage}>Send</button>
      </div>
    </div>
  );
}
