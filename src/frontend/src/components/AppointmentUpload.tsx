import React, { useState } from 'react';

const apiUrl = 'http://localhost:8000/api/v1/appointments/';

const DataSubmitter: React.FC = () => {
    const [userId, setUserId] = useState('');
    const [dataLocation, setDataLocation] = useState('');
    const [response, setResponse] = useState('');

    const handleSubmit = async () => {
        const payload = {
            user_id: parseInt(userId, 10),
            data_location: dataLocation
        };

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
                setResponse('Data processed successfully: ' + JSON.stringify(result));
            } else {
                setResponse('Failed to process data.');
            }
        } catch (error) {
            console.error('Submission error:', error);
            setResponse('An error occurred while submitting data.');
        }
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
            <p>{response}</p>
        </div>
    );
};

export default DataSubmitter;
