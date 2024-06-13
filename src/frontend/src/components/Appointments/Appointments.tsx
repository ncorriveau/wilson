import React, { useState, useCallback } from "react";
import { useDropzone } from "react-dropzone";
import MultiStepConfirmation from "./MultiStepConfirmation";
import AppointmentList from "./AppointmentList";
import axios from "axios";

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
} from "@chakra-ui/react";
import { FiUploadCloud } from "react-icons/fi";

interface AppointmentManagerProps {
  token: string;
  userId: string;
}

const apiUrl = "http://localhost:8000/api/v1/appointments/";

const AppointmentManager: React.FC<AppointmentManagerProps> = ({
  token,
  userId,
}) => {
  const [file, setFile] = useState<File | null>(null);
  const [modalOpen, setModalOpen] = useState(false);
  const [analysisResults, setAnalysisResults] = useState<any>(null);
  const [loading, setLoading] = useState(false);
  // const [fileUrl, setFileUrl] = useState<string>("");
  const toast = useToast();

  const onDrop = useCallback((acceptedFiles: File[]) => {
    const uploadedFile = acceptedFiles[0];
    if (uploadedFile.type === "application/pdf") {
      setFile(uploadedFile);
    } else {
      toast({
        title: "Invalid file type.",
        description: "Please upload a PDF file.",
        status: "error",
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
        title: "No file selected.",
        description: "Please upload a PDF file before submitting.",
        status: "error",
        duration: 5000,
        isClosable: true,
      });
      return;
    }

    const formData = new FormData();
    formData.append("file", file);
    setLoading(true);
    console.log("Sending file to server");
    try {
      const uploadResponse = await axios.post(`${apiUrl}upload`, formData, {
        headers: {
          Authorization: `Bearer ${token}`,
          "Content-Type": "multipart/form-data",
          "x-user-id": userId,
        },
      });
      const s3Uri = uploadResponse.data.s3_uri;
      console.log("S3 URI: ", s3Uri);

      const response = await axios.post(
        `${apiUrl}analyze`,
        {
          data_location: s3Uri,
          user_id: userId,
        },
        {
          headers: {
            Authorization: `Bearer ${token}`,
            "Content-Type": "application/json",
          },
        },
      );

      if (response.status === 200) {
        const result = response.data;
        console.log(result);
        setAnalysisResults(result);
        setModalOpen(true);
        toast({
          title: "Analysis successful.",
          description: "Your appointment data has been analyzed.",
          status: "success",
          duration: 5000,
          isClosable: true,
        });
      } else {
        toast({
          title: "Analysis failed.",
          description: "There was an issue analyzing your appointment data.",
          status: "error",
          duration: 5000,
          isClosable: true,
        });
      }
    } catch (error) {
      console.error("Submission error:", error);
      toast({
        title: "Submission error.",
        description: "An error occurred while submitting data.",
        status: "error",
        duration: 5000,
        isClosable: true,
      });
    } finally {
      setLoading(false);
    }
  };

  const handleSave = async (updatedData: any) => {
    try {
      console.log("Saving data:", updatedData);
      // await axios.post(`${apiUrl}save`, updatedData, {
      //   headers: {
      //     Authorization: `Bearer ${token}`,
      //     "Content-Type": "application/json",
      //   },
      // });
      setAnalysisResults(updatedData); // Update the state with the new data
      toast({
        title: "Data saved.",
        description: "Your changes have been saved successfully.",
        status: "success",
        duration: 5000,
        isClosable: true,
      });
    } catch (error) {
      console.error("Error saving data:", error);
      toast({
        title: "Error saving data.",
        description: "An error occurred while saving data.",
        status: "error",
        duration: 5000,
        isClosable: true,
      });
    }
  };

  const handleClose = () => {
    console.log("Closing modal and cleaning up");
    setModalOpen(false);
  };

  return (
    <Container maxW="container.md" py={10} centerContent>
      <VStack spacing={5} w="100%" p={6} borderRadius="md" boxShadow="xl">
        <Heading>Upload Appointment Data</Heading>
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
              <Icon as={FiUploadCloud} boxSize={12} color="green.800" />
              {isDragActive ? (
                <Text>Drop the PDF here ...</Text>
              ) : (
                <Text>
                  Drag 'n' drop a PDF file here, or click to select a file
                </Text>
              )}
              {file && <Text mt={2}>Uploaded File: {file.name}</Text>}
            </Stack>
          </Box>
        )}
        <Button
          colorScheme="green"
          onClick={handleSubmit}
          isLoading={loading}
          variant="solid"
          size="lg"
        >
          🤖 Analyze your appointment 🤖
        </Button>
        {modalOpen && analysisResults && (
          <MultiStepConfirmation
            data={analysisResults}
            onClose={handleClose}
            onSave={handleSave}
          />
        )}
        <AppointmentList token={token} userId={userId} />
      </VStack>
    </Container>
  );
};

export default AppointmentManager;
