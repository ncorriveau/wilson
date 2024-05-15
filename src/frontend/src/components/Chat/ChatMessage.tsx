import React from 'react';

interface ChatMessageProps {
    user: string;
    text: string;
}

const ChatMessage: React.FC<ChatMessageProps> = ({ user, text }) => {
    return (
        <div className={`chat-message ${user.toLowerCase()}`}>
            <strong>{user}: </strong>{text}
        </div>
    );
};

export default ChatMessage;
