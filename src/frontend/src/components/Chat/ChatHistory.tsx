import React from 'react';
import ChatMessage from './ChatMessage';

interface ChatHistoryProps {
    messages: Array<{ user: string, text: string }>;
}

const ChatHistory: React.FC<ChatHistoryProps> = ({ messages }) => {
    return (
        <div className="chat-history">
            {messages.map((message, index) => (
                <ChatMessage key={index} user={message.user} text={message.text} />
            ))}
        </div>
    );
};

export default ChatHistory;
