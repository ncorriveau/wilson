import React from "react";
import { VStack, Box, Text, useColorModeValue } from "@chakra-ui/react";
import ReactMarkdown from "react-markdown";
import remarkGfm from "remark-gfm";

interface ChatHistoryProps {
  messages: Array<{ user: string; text: string }>;
}

const ChatHistory: React.FC<ChatHistoryProps> = ({ messages }) => {
  const bgValue = useColorModeValue("gray.100", "gray.700");
  const boxBgValue = useColorModeValue("white", "gray.800");
  return (
    <VStack
      spacing={4}
      align="stretch"
      overflowY="auto"
      maxH="60vh"
      p={4}
      borderWidth="1px"
      borderRadius="md"
      bg={bgValue}
    >
      {messages.map((message, index) => (
        <Box key={index} p={3} bg={boxBgValue} borderRadius="md" shadow="sm">
          <Text fontSize="sm" color="gray.500">
            {message.user}
          </Text>
          <ReactMarkdown remarkPlugins={[remarkGfm]}>
            {message.text}
          </ReactMarkdown>
        </Box>
      ))}
    </VStack>
  );
};

export default ChatHistory;
