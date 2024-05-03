import React, { useState, useEffect } from 'react';

interface Appointment {
  id: number;
  date: string;
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

const apiUrl = 'http://localhost:8000/api/v1/appointments/'

const AppointmentList: React.FC<{ userId: string }> = ({ userId }) => {
    const [appointments, setAppointments] = useState<Appointment[]>([]);
    const [selectedAppointment, setSelectedAppointment] = useState<Appointment | null>(null);

    useEffect(() => {
        const fetchAppointments = async () => {
            try { 
                    const response = await fetch(`${apiUrl}${userId}`);
                    if (response.ok) {
                        const data = await response.json();
                        console.log('data', data)
                        setAppointments(data.appointments);
                    }
            } catch (error) {
                console.error('Error fetching appointments:', error);
            }
        };
        fetchAppointments();
    }, [userId]);

    console.log('appointments: ', appointments)
    
    return (
        <div>
            <h1>Appointments</h1>
            { <div>
                {appointments && (appointments.map((appointment) => (
                    <div key={appointment.id} onClick={() => setSelectedAppointment(appointment)}>
                        <h2>{appointment.provider_info.first_name} {appointment.provider_info.last_name}, {appointment.provider_info.specialty}, {appointment.date}</h2>
                    </div>
                )))}
            </div>}
            {selectedAppointment && (
                <div>
                    <h3>Summary</h3> 
                    <p>{selectedAppointment.summary}</p>
                    <h3>Prescriptions</h3>
                    <ul>
                        {selectedAppointment.prescriptions.drugs.map((drug, index) => (
                            <li key={index}>{drug.brand_name}: {drug.instructions}</li>
                        ))}
                    </ul>
                    <h3>Follow Up Tasks</h3>
                    <ul>
                        {selectedAppointment.follow_ups.map((task, index) => (
                            <li key={index}>{task}</li>
                        ))}
                    </ul>
                </div>
            )} 
        </div>
    );
};

export default AppointmentList;
