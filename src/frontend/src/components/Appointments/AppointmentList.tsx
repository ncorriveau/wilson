import React, { useState, useEffect } from "react";
import axios from "axios";
import {
  Box,
  Heading,
  Text,
  VStack,
  HStack,
  Icon,
} from "@chakra-ui/react";
import { FiChevronDown, FiChevronUp } from "react-icons/fi";

interface Appointment {
  id: number;
  date: string;
  isOpen: boolean;
  prescriptions: {
    drugs: {
      technical_name: string;
      brand_name: string;
      instructions: string;
    }[];
  };
  provider_info: {
    first_name: string;
    last_name: string;
    specialty: string;
  };
  follow_ups: string[];
  summary: string;
}

interface AppointmentManagerProps {
  token: string;
  userId: string;
}

const apiUrl = "http://localhost:8000/api/v1/appointments/";

const AppointmentList: React.FC<AppointmentManagerProps> = ({ token, userId }) => {
  const [appointments, setAppointments] = useState<Appointment[]>([]);

  useEffect(() => {
    const fetchAppointments = async () => {
      try {
        const response = await axios.get(`${apiUrl}${userId}`, {
          headers: {
              'Authorization': `Bearer ${token}`,
          },
      });
        if (response.status === 200) {
          const data = await response.data;
          const updatedAppointments = data.appointments.map(
            (appointment: Appointment) => ({
              ...appointment,
              isOpen: false,
            }),
          );
          setAppointments(updatedAppointments);
        }
      } catch (error) {
        console.error("Error fetching appointments:", error);
      }
    };
    fetchAppointments();
  }, [userId]);

  const toggleAppointment = (id: number) => {
    const updatedAppointments = appointments.map((appointment) => ({
      ...appointment,
      isOpen: appointment.id === id ? !appointment.isOpen : appointment.isOpen,
    }));
    setAppointments(updatedAppointments);
  };

  // const handleCheckboxChange = (appointmentId: number, index: number) => {
  //   const updatedAppointments = appointments.map((appointment) => {
  //     if (appointment.id === appointmentId) {
  //       const updatedFollowUps = appointment.follow_ups.map((task, taskIndex) => {
  //         if (taskIndex === index) {
  //           return task.completed ? { ...task, completed: false } : { ...task, completed: true };
  //         }
  //         return task;
  //       });
  //       return { ...appointment, follow_ups: updatedFollowUps };
  //     }
  //     return appointment;
  //   });
  //   setAppointments(updatedAppointments);
  // };

  return (
    <VStack spacing={5} w="100%" mt={10}>
      <Heading fontFamily="serif" size="lg" color="green.800">Appointments</Heading>
      {appointments.map((appointment) => (
        <Box key={appointment.id} w="100%" p={5} borderWidth="1px" borderRadius="md" boxShadow="md" bg="white">
          <HStack justifyContent="space-between" onClick={() => toggleAppointment(appointment.id)} cursor="pointer">
            <Heading fontFamily="serif" size="md">
              {appointment.provider_info.first_name} {appointment.provider_info.last_name} - {appointment.provider_info.specialty}, {appointment.date}
            </Heading>
            <Icon as={appointment.isOpen ? FiChevronUp : FiChevronDown} w={6} h={6} />
          </HStack>
          {appointment.isOpen && (
            <VStack mt={5} spacing={3} align="start">
              <Box>
                <Heading size="sm">Summary</Heading>
                <Text>{appointment.summary}</Text>
              </Box>
              <Box>
                <Heading size="sm">Prescriptions</Heading>
                <ul>
                  {appointment.prescriptions.drugs.map((drug, index) => (
                    <li key={index}>
                      <Text>{drug.brand_name}: {drug.instructions}</Text>
                    </li>
                  ))}
                </ul>
              </Box>
              <Box>
                <Heading size="sm">Follow Up Tasks</Heading>
                <ul>
                  {appointment.follow_ups.map((task, index) => (
                    <li key={index}>
                      <HStack>
                        {/* <Checkbox
                          isChecked={task.completed}
                          onChange={() => handleCheckboxChange(appointment.id, index)}
                        /> */}
                        <Text> {task} </Text>
                      </HStack>
                    </li>
                  ))}
                </ul>
              </Box>
            </VStack>
          )}
        </Box>
      ))}
    </VStack>
  );
};

export default AppointmentList;
