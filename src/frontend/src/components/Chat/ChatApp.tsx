import React, { useState } from 'react';
import axios from 'axios';
import ChatHistory from './ChatHistory';
import ChatInput from './ChatInput';
import './ChatApp.css';

interface ChatProps {
    token: string;
    userId: string;
  }
  

const apiUrl = 'http://localhost:8000/api/v1/chat_w_data/';  // Adjust this to your actual API endpoint

const ChatApp: React.FC<ChatProps> = ({userId, token}) => {
    const [messages, setMessages] = useState<Array<{ user: string, text: string }>>([]);

    const handleSendMessage = async (message: string) => {
        const userMessage = { user: 'User', text: message };
        setMessages([...messages, userMessage]);
        console.log('message ', message)
        try {
            const response = await axios.post(`${apiUrl}${userId}`, {
                query: message,
            },
            {
                headers: {
                    Authorization: `Bearer ${token}`,
                    'Content-Type': 'application/json',
                },
            }
        );
            console.log('response ', response);
            const botMessage = { user: 'Bot', text: response.data.response };
            setMessages([...messages, userMessage, botMessage]);
        } catch (error) {
            console.error("Error fetching response:", error);
            const errorMessage = { user: 'Bot', text: 'There was an error processing your request.' };
            setMessages([...messages, userMessage, errorMessage]);
        }
    };

    return (
        <div className="chat-app">
            <header>
                <h1>Chat with Your Data</h1>
            </header>
            <ChatHistory messages={messages} />
            <ChatInput onSendMessage={handleSendMessage} />
        </div>
    );
};

export default ChatApp;