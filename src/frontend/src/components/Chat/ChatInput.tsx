import React, { useState } from 'react';
import { HStack, Input, Button, useColorModeValue } from '@chakra-ui/react';

interface ChatInputProps {
    onSendMessage: (message: string) => void;
}

const ChatInput: React.FC<ChatInputProps> = ({ onSendMessage }) => {
    const [message, setMessage] = useState<string>('');

    const handleChange = (e: React.ChangeEvent<HTMLInputElement>) => setMessage(e.target.value);
    const handleSubmit = () => {
      onSendMessage(message);
      setMessage('');
    };
  
    return (
      <HStack spacing={2} mt={4}>
        <Input
          value={message}
          onChange={handleChange}
          placeholder="Type your message..."
          bg={useColorModeValue('white', 'gray.800')}
        />
        <Button onClick={handleSubmit} colorScheme="blue">
          Send
        </Button>
      </HStack>
    );
  };

export default ChatInput;
