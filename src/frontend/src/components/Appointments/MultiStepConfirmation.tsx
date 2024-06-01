import React, { useState } from "react";
import {
  Box,
  Button,
  Input,
  Text,
  Textarea,
  VStack,
  HStack,
  List,
  ListItem,
  useToast,
} from "@chakra-ui/react";

interface PrescriptionData {
  technical_name: string;
  brand_name: string;
  instructions: string;
}

interface ProviderInfo {
  first_name: string;
  last_name: string;
  specialty: string;
}

interface ConfirmationData {
  prescriptions: PrescriptionData[];
  provider_info: ProviderInfo;
  follow_ups: string[];
  summary: string;
}

interface MultiStepConfirmationProps {
  data: ConfirmationData;
  onClose: () => void; // Function to call when the entire process is completed or canceled
  onSave: (updatedData: ConfirmationData) => void; // Function to call when the data is saved
}

const MultiStepConfirmation: React.FC<MultiStepConfirmationProps> = ({
  data,
  onClose,
  onSave,
}) => {
  const [step, setStep] = useState(1);
  const [formData, setFormData] = useState<ConfirmationData>(data);
  const toast = useToast();

  const handleNext = () => {
    if (step < 3) setStep(step + 1);
  };

  const handlePrevious = () => {
    if (step > 1) setStep(step - 1);
  };

  const handleChange = (e: React.ChangeEvent<HTMLInputElement | HTMLTextAreaElement>, field: string, index?: number) => {
    if (field === "first_name" || field === "last_name" || field === "specialty") {
      setFormData({
        ...formData,
        provider_info: {
          ...formData.provider_info,
          [field]: e.target.value,
        },
      });
    } else if (field === "prescriptions" && index !== undefined) {
      const newPrescriptions = [...formData.prescriptions];
      newPrescriptions[index] = {
        ...newPrescriptions[index],
        [e.target.name]: e.target.value,
      };
      setFormData({
        ...formData,
        prescriptions: newPrescriptions,
      });
    } else if (field === "follow_ups" && index !== undefined) {
      const newFollowUps = [...formData.follow_ups];
      newFollowUps[index] = e.target.value;
      setFormData({
        ...formData,
        follow_ups: newFollowUps,
      });
    }
  };

  const handleFinish = () => {
    onSave(formData); // Save the updated data
    toast({
      title: "Data Saved.",
      description: "Your changes have been saved.",
      status: "success",
      duration: 5000,
      isClosable: true,
    });
    onClose(); // Close the dialog
  };

  return (
    <Box className="modal" p={5} bg="white" borderRadius="md" shadow="md">
      <Box className="modal-content">
        {step === 1 && (
          <VStack spacing={4}>
            <Text fontSize="2xl">Confirm Provider Information</Text>
            <Input
              placeholder="First Name"
              value={formData.provider_info.first_name}
              onChange={(e) => handleChange(e, "first_name")}
            />
            <Input
              placeholder="Last Name"
              value={formData.provider_info.last_name}
              onChange={(e) => handleChange(e, "last_name")}
            />
            <Input
              placeholder="Specialty"
              value={formData.provider_info.specialty}
              onChange={(e) => handleChange(e, "specialty")}
            />
            <HStack spacing={4}>
              <Button onClick={handleNext} colorScheme="blue">
                Next
              </Button>
            </HStack>
          </VStack>
        )}
        {step === 2 && (
          <VStack spacing={4}>
            <Text fontSize="2xl">Confirm Prescriptions</Text>
            <List spacing={3}>
              {formData.prescriptions.map((drug, index) => (
                <ListItem key={index}>
                  <Input
                    placeholder="Brand Name"
                    name="brand_name"
                    value={drug.brand_name}
                    onChange={(e) => handleChange(e, "prescriptions", index)}
                  />
                  <Textarea
                    placeholder="Instructions"
                    name="instructions"
                    value={drug.instructions}
                    onChange={(e) => handleChange(e, "prescriptions", index)}
                  />
                </ListItem>
              ))}
            </List>
            <HStack spacing={4}>
              <Button onClick={handlePrevious}>Previous</Button>
              <Button onClick={handleNext} colorScheme="blue">
                Next
              </Button>
            </HStack>
          </VStack>
        )}
        {step === 3 && (
          <VStack spacing={4}>
            <Text fontSize="2xl">Confirm Follow Up Tasks</Text>
            <List spacing={3}>
              {formData.follow_ups.map((task, index) => (
                <ListItem key={index}>
                  <Textarea
                    placeholder="Follow Up Task"
                    value={task}
                    onChange={(e) => handleChange(e, "follow_ups", index)}
                  />
                </ListItem>
              ))}
            </List>
            <HStack spacing={4}>
              <Button onClick={handlePrevious}>Previous</Button>
              <Button onClick={handleFinish} colorScheme="green">
                Finish
              </Button>
            </HStack>
          </VStack>
        )}
      </Box>
    </Box>
  );
};

export default MultiStepConfirmation;
