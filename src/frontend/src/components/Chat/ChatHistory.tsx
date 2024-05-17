import React from 'react';
import { VStack, Box, Text, useColorModeValue } from '@chakra-ui/react';

interface ChatHistoryProps {
    messages: Array<{ user: string, text: string }>;
}

const ChatHistory: React.FC<ChatHistoryProps> = ({ messages }) => {
    return (
        <VStack
          spacing={4}
          align="stretch"
          overflowY="auto"
          maxH="60vh"
          p={4}
          borderWidth="1px"
          borderRadius="md"
          bg={useColorModeValue('gray.100', 'gray.700')}
        >
          {messages.map((message, index) => (
            <Box
              key={index}
              p={3}
              bg={useColorModeValue('white', 'gray.800')}
              borderRadius="md"
              shadow="sm"
            >
              <Text fontSize="sm" color="gray.500">{message.user}</Text>
              <Text>{message.text}</Text>
            </Box>
          ))}
        </VStack>
      );
};

export default ChatHistory;
