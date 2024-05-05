import React, { useState, useEffect } from "react";
import axios from "axios";
import "./AppointmentList.css";
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

  console.log("appointments: ", appointments);

  return (
    <div className="appointment-list">
      <h2>Appointments</h2>
      {appointments.map((appointment) => (
        <React.Fragment key={appointment.id}>
          <div
            className={`appointment-header ${appointment.isOpen ? "open" : ""}`}
            onClick={() => toggleAppointment(appointment.id)}
          >
            <div className={`caret ${appointment.isOpen ? "open" : ""}`}></div>
            <h2>
              {appointment.provider_info.first_name}{" "}
              {appointment.provider_info.last_name} -{" "}
              {appointment.provider_info.specialty}, {appointment.date}
            </h2>
          </div>
          {appointment.isOpen && (
            <div className="appointment-details">
              <h3>Summary</h3>
              <p>{appointment.summary}</p>
              <h3>Prescriptions</h3>
              <ul>
                {appointment.prescriptions.drugs.map((drug, index) => (
                  <li key={index}>
                    {drug.brand_name}: {drug.instructions}
                  </li>
                ))}
              </ul>
              <h3>Follow Up Tasks</h3>
              <ul>
                {appointment.follow_ups.map((task, index) => (
                  <li key={index}>{task}</li>
                ))}
              </ul>
            </div>
          )}
        </React.Fragment>
      ))}
    </div>
  );
};

export default AppointmentList;
