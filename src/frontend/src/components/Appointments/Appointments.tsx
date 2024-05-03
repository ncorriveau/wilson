import React, { useState } from 'react';
import MultiStepConfirmation from './MultiStepConfirmation';
import AppointmentList from './AppointmentList';
import './Appointments.css';

const apiUrl = 'http://localhost:8000/api/v1/appointments/';


const AppointmentManager: React.FC = () => {
    // const [loading, setLoading] = useState(false);
    const [dataLocation, setDataLocation] = useState('');
    const [userId, setUserId] = useState('');
    const [modalOpen, setModalOpen] = useState(false);
    const [analysisResults, setAnalysisResults] = useState<any>(null);

    const handleSubmit = async () => {
        const payload = {
            user_id: parseInt(userId, 10),
            data_location: dataLocation
        };
    
        try {
            const response = await fetch(`${apiUrl}upload`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify(payload),
            });
    
            if (response.ok) {
                const result = await response.json();
                console.log(result)
                setAnalysisResults(result);
                setModalOpen(true);
            } else {
                alert('Failed to process data.');
            }
        } catch (error) {
            console.error('Submission error:', error);
            alert('An error occurred while submitting data.');
        } finally { 
        }
    };

    const handleClose = () => {
        // Perform any cleanup or final actions before closing the modal
        console.log("Closing modal and cleaning up");
        setModalOpen(false); // Close the modal
    };

    return (
        <div className="data-submitter">
            <h1>Submit Data</h1>
            <input
                type="text"
                value={userId}
                onChange={(e) => setUserId(e.target.value)}
                placeholder="Enter User ID"
            />
            <input
                type="text"
                value={dataLocation}
                onChange={(e) => setDataLocation(e.target.value)}
                placeholder="Enter Data Location"
            />
            <button onClick={handleSubmit}>Get Appointment Analysis</button>
            {modalOpen && analysisResults && (
                <MultiStepConfirmation data={analysisResults} onClose={handleClose} />
            )}
            <AppointmentList userId={ userId }/>
        </div>
    );

};

export default AppointmentManager;
