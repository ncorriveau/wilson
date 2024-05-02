import React, { useState, useEffect } from 'react';
import './LoadingWithMessages.css';

const LoadingWithMessages: React.FC = () => {
  const [message, setMessage] = useState('Analyzing...');
  const messages = ['Analyzing...', 'Extracting very important medical info...', 'Almost done...'];

  useEffect(() => {
    const interval = setInterval(() => {
      setMessage(prev => {
        const nextIndex = (messages.indexOf(prev) + 1) % messages.length;
        return messages[nextIndex];
      });
    }, 5000); // Change message every 5 seconds

    return () => clearInterval(interval);
  }, []);

  return (
    <div className="loading-container">
      <div className="spinner"></div>
      <p>{message}</p>
    </div>
  );
};

export default LoadingWithMessages;