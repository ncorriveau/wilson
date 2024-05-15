import React, { useState, useCallback } from "react";
import { useDropzone } from "react-dropzone";
import MultiStepConfirmation from "./MultiStepConfirmation";
import AppointmentList from "./AppointmentList";
// import "./Appointments.css";
import axios from "axios";
import LoadingWithMessages from "./LoadingWithMessages";

import {
    Box,
    Button,
    Container,
    Heading,
    Text,
    VStack,
    Spinner,
    useToast,
    Stack,
    Icon,
} from '@chakra-ui/react';
import { FiUploadCloud } from 'react-icons/fi';

interface AppointmentManagerProps {
  token: string;
  userId: string;
}

const apiUrl = "http://localhost:8000/api/v1/appointments/";

const AppointmentManager: React.FC<AppointmentManagerProps> = ({ token, userId }) => {
  const [file, setFile] = useState<File | null>(null);
  const [modalOpen, setModalOpen] = useState(false);
  const [analysisResults, setAnalysisResults] = useState<any>(null);
  const [loading, setLoading] = useState(false);
  const toast = useToast();

  const onDrop = useCallback((acceptedFiles: File[]) => {
    const uploadedFile = acceptedFiles[0];
    if (uploadedFile.type === "application/pdf") {
      setFile(uploadedFile);
    } else {
      toast({
        title: 'Invalid file type.',
        description: 'Please upload a PDF file.',
        status: 'error',
        duration: 5000,
        isClosable: true,
      });
      return;
    }
  }, []);

  const { getRootProps, getInputProps, isDragActive } = useDropzone({
    onDrop,
    multiple: false,
    // @ts-ignore
    accept: "application/pdf",
  });

  const handleSubmit = async () => {
    if (!file) {
        toast({
          title: 'No file selected.',
          description: 'Please upload a PDF file before submitting.',
          status: 'error',
          duration: 5000,
          isClosable: true,
        });
        return;
    }

    // this would need to be form eventually and we send the location of the data
    setLoading(true);
    try {
      const response = await axios.post(`${apiUrl}upload`, 
        {
            data_location: "data",
            user_id: userId,
        },
        {
            headers: {
                'Authorization': `Bearer ${token}`,
                'Content-Type': 'application/json',
            },
        }
    );

      if (response.status === 200) {
        const result = response.data;
        console.log(result);
        setAnalysisResults(result);
        setModalOpen(true);
        toast({
          title: 'Analysis successful.',
          description: 'Your appointment data has been analyzed.',
          status: 'success',
          duration: 5000,
          isClosable: true,
        });
      } else {
        toast({
          title: 'Analysis failed.',
          description: 'There was an issue analyzing your appointment data.',
          status: 'error',
          duration: 5000,
          isClosable: true,
        });
      }
    } catch (error) {
      console.error("Submission error:", error);
      toast({
        title: 'Submission error.',
        description: 'An error occurred while submitting data.',
        status: 'error',
        duration: 5000,
        isClosable: true,
      });
    } finally {
      setLoading(false);
    }
  };

  const handleClose = () => {
    console.log("Closing modal and cleaning up");
    setModalOpen(false);
  };

  return (
    <Container maxW="container.md" py={10} centerContent>
      <VStack spacing={5} w="100%" bgGradient="linear(to-r, white, lightblue)" p={6} borderRadius="md" boxShadow="xl">
        <Heading color="grey">Upload Appointment Data</Heading>
        {loading ? (
          <VStack>
            <Spinner size="xl" color="white" />
            <Text color="white">Uploading...</Text>
            <Text color="white">Almost there...</Text>
          </VStack>
        ) : (
          <Box
            {...getRootProps()}
            p={5}
            border="2px dashed"
            borderColor="gray.300"
            borderRadius="md"
            textAlign="center"
            bg="white"
            w="100%"
          >
            <input {...getInputProps()} />
            <Stack direction="column" align="center" spacing={2}>
              <Icon as={FiUploadCloud} boxSize={12} color="teal.500" />
              {isDragActive ? (
                <Text>Drop the PDF here ...</Text>
              ) : (
                <Text>Drag 'n' drop a PDF file here, or click to select a file</Text>
              )}
              {file && <Text mt={2}>Uploaded File: {file.name}</Text>}
            </Stack>
          </Box>
        )}
        <Button colorScheme="teal" onClick={handleSubmit} isLoading={loading} variant="solid" size="lg">
          🤖 Analyze your appointment 🤖
        </Button>
        {modalOpen && analysisResults && (
          <MultiStepConfirmation data={analysisResults} onClose={handleClose} />
        )}
        <AppointmentList token={token} userId={userId} />
      </VStack>
    </Container>
  );
};

export default AppointmentManager;