import React, { useState, useEffect } from 'react';

interface Appointment {
  datetime: string;
  prescriptions: {
    drugs: {
      technical_name: string;
      brand_name: string;
      instructions: string;
    }[];
    };
  providerInfo: {
      first_name: string;
      last_name: string;
      specialty: string;
  };
  followUps: {
    tasks: string[];
  };
  summary: string;
}


const AppointmentList: React.FC<{ userId: number }> = ({ userId }) => {
    const [appointments, setAppointments] = useState<Appointment[]>([]);
    const [selectedAppointment, setSelectedAppointment] = useState<Appointment | null>(null);

    useEffect(() => {
        const fetchAppointments = async () => {
            const response = await fetch(`http://localhost:8000/appointments/${userId}`);
            if (response.ok) {
                const data = await response.json();
                setAppointments(data);
            }
        };

        fetchAppointments();
    }, [userId]);

    return (
        <div>
            <h1>Appointments</h1>
            <div>
                {appointments.map((appointment, index) => (
                    <div key={index} onClick={() => setSelectedAppointment(appointment)}>
                        <h2>{appointment.providerInfo.first_name} {appointment.providerInfo.last_name}</h2>
                        <p>{appointment.providerInfo.specialty}</p>
                        <p>{appointment.datetime}</p>
                    </div>
                ))}
            </div>
            {selectedAppointment && (
                <div>
                    <h2>Details for {selectedAppointment.providerInfo.first_name} {selectedAppointment.providerInfo.last_name}</h2>
                    <p>Summary: {selectedAppointment.summary}</p>
                    <h3>Prescriptions</h3>
                    <ul>
                        {selectedAppointment.prescriptions.drugs.map((drug, index) => (
                            <li key={index}>{drug.brand_name}: {drug.instructions}</li>
                        ))}
                    </ul>
                    <h3>Follow Up Tasks</h3>
                    <ul>
                        {selectedAppointment.followUps.tasks.map((task, index) => (
                            <li key={index}>{task}</li>
                        ))}
                    </ul>
                </div>
            )}
        </div>
    );
};

export default AppointmentList;
