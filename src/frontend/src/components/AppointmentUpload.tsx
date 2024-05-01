import React, { useState } from 'react';
import ResultsDisplay from './Results';
import LoadingWithMessages from './LoadingWithMessages';

const apiUrl = 'http://localhost:8000/api/v1/appointments/';

const DataSubmitter: React.FC = () => {
    const [userId, setUserId] = useState('');
    const [dataLocation, setDataLocation] = useState('');
    const [loading, setLoading] = useState(false);
    const [results, setResults] = useState<any>(null);
    const [showDialog, setShowDialog] = useState(false);

    const handleSubmit = async () => {
        const payload = {
            user_id: parseInt(userId, 10),
            data_location: dataLocation
        };

        setLoading(true);
        try {
            const response = await fetch(apiUrl, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify(payload),
            });

            if (response.ok) {
                const result = await response.json();
                setResults(result);
                setShowDialog(true);
            } else {
                alert('Failed to process data.');
            }
        } catch (error) {
            console.error('Submission error:', error);
            alert('An error occurred while submitting data.');
        } finally { 
            setLoading(false);
        }
    };
    const handleConfirm = () => {
        console.log("Analysis confirmed by user");
        setShowDialog(false);
        alert('Confirmation successful. Proceeding with the next steps.');
        // Additional actions after confirmation can be added here
    };

    const handleCancel = () => {
        console.log("User cancelled the confirmation");
        setShowDialog(false);
        alert('Confirmation cancelled. Please review or modify the data.');
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
            <button onClick={handleSubmit}>Submit</button>
            {loading ? <LoadingWithMessages /> : (showDialog && results && (
                <ResultsDisplay
                    results={results}
                    onConfirm={handleConfirm}
                    onCancel={handleCancel}
                />
            ))}
        </div>
    );
};

export default DataSubmitter;
