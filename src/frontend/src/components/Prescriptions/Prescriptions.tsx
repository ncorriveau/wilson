import React, { useState, useEffect } from "react";
import axios from "axios";
import {
    Box,
    Heading,
    Text,
    Spinner,
    HStack,
    Icon,
    useColorModeValue,
  } from '@chakra-ui/react';
import { CheckCircleIcon, WarningIcon } from '@chakra-ui/icons';

// import './Prescriptions.css';

interface PrescriptionProps {
  token: string;
  userId: string;
}

interface ProviderInfo  {
    firstName: string;
    lastName: string;
    specialty: string;
}

interface Prescription {
id: number;
brandName: string;
technicalName: string;
instructions: string;
providerInfo: ProviderInfo;
isActive: boolean;
}


const apiUrl = "http://localhost:8000/api/v1/prescriptions/";

const Prescriptions: React.FC<PrescriptionProps> = ({ token, userId }) => {
    const [prescriptions, setPrescriptions] = useState<Prescription[]>([]);
    const [loading, setLoading] = useState(false);
    const cardBg = useColorModeValue('white', 'gray.800');

    useEffect(() => {
        const fetchPrescriptions = async () => {
            try {
                setLoading(true);
                const response = await axios.get(`${apiUrl}${userId}`, {
                    headers: {
                        Authorization: `Bearer ${token}`,
                    }
                });
                if (response.status === 200) {
                    const data = await response.data;
                    console.log('data ', data)
                    setPrescriptions(data);
                }
            } catch (error) {
                console.error("Error fetching prescriptions:", error);
            } finally {
                setLoading(false);
            }
        };
        fetchPrescriptions();
    }, [userId, token]);

    const toggleActiveStatus = async (prescription: Prescription) => {
        if (window.confirm("Are you sure you want to change the status of this prescription?")) {
            try {
                const updatedPrescription = { ...prescription, isActive: !prescription.isActive };
                console.log('updatedPrescription ', updatedPrescription)
                const response = await axios.put(`${apiUrl}status/${prescription.id}`, 
                {
                    id: updatedPrescription.id,
                    isActive: updatedPrescription.isActive,
                
                }, {
                    headers: {
                        Authorization: `Bearer ${token}`,
                    }
                });
                if (response.status === 200) {
                    setPrescriptions(prev =>
                        prev.map(p =>
                            p.id === prescription.id ? updatedPrescription : p
                        )
                    );
                }
            } catch (error) {
                console.error("Error updating prescription:", error);
            }
        }
    };

    return (
        <Box p={5}>
          <Heading mb={6}>Prescriptions</Heading>
          {loading ? (
            <Spinner size="xl" />
          ) : (
            prescriptions && prescriptions.map(prescription => (
              <Box
                key={prescription.id}
                p={5}
                shadow="md"
                borderWidth="1px"
                borderRadius="md"
                bg={cardBg}
                mb={4}
              >
                <Heading size="md" mb={2}>{prescription.brandName}</Heading>
                <Text fontSize="sm" mb={2}><strong>Technical Name:</strong> {prescription.technicalName}</Text>
                <Text fontSize="sm" mb={2}><strong>Instructions:</strong> {prescription.instructions}</Text>
                <Text fontSize="sm" mb={2}><strong>Prescribing Physician:</strong> {`${prescription.providerInfo.firstName} ${prescription.providerInfo.lastName}, ${prescription.providerInfo.specialty}`}</Text>
                <HStack mt={4}>
                  <Icon
                    as={prescription.isActive ? CheckCircleIcon : WarningIcon}
                    color={prescription.isActive ? 'green.500' : 'red.500'}
                    boxSize={6}
                    cursor="pointer"
                    onClick={() => toggleActiveStatus(prescription)}
                  />
                  <Text color={prescription.isActive ? 'green.500' : 'red.500'}>
                    {prescription.isActive ? "Active" : "Inactive"}
                  </Text>
                </HStack>
              </Box>
            ))
          )}
        </Box>
      );
    };
    
    export default Prescriptions;
