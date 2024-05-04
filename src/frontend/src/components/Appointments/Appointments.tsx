import React, { useState, useCallback } from 'react';
import { useDropzone } from 'react-dropzone';
import MultiStepConfirmation from './MultiStepConfirmation';
import AppointmentList from './AppointmentList';
import './Appointments.css';
import axios from 'axios';
import LoadingWithMessages from './LoadingWithMessages';

const apiUrl = 'http://localhost:8000/api/v1/appointments/';

const AppointmentManager: React.FC = () => {
    const [file, setFile] = useState<File | null>(null);
    const [modalOpen, setModalOpen] = useState(false);
    const [analysisResults, setAnalysisResults] = useState<any>(null);
    const [loading, setLoading] = useState(false);
    // const [userID, setUserId] = useState<string>('');

    const onDrop = useCallback((acceptedFiles: File[]) => {
        const uploadedFile = acceptedFiles[0];
        if (uploadedFile.type === 'application/pdf') {
            setFile(uploadedFile);
        } else {
            alert('Only PDF files are accepted.');
        }
    }, []);

    const { getRootProps, getInputProps, isDragActive } = useDropzone({
        onDrop,
        multiple: false,
        // @ts-ignore
        accept: 'application/pdf',
    });

    const handleSubmit = async () => {
        if (!file) {
            alert('Please upload a PDF file.');
            return;
        }
    
        // this would need to be form eventually 
        setLoading(true);
        try {
            const response = await axios.post(`${apiUrl}upload`, {
                data_location: 'data',
                user_id: '1',
            });
            
            if (response.status === 200) {
                const result = response.data;
                console.log(result);
                setAnalysisResults(result);
                setModalOpen(true);
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

    const handleClose = () => {
        console.log("Closing modal and cleaning up");
        setModalOpen(false);
    };

    return (
        <div className="data-submitter">
            <h1>Upload Appointment Data</h1>
            {loading ? <LoadingWithMessages /> : (
            <div {...getRootProps()} className="dropzone">
                {/* @ts-ignore */}
                <input {...getInputProps()} />
                {
                    isDragActive ?
                    <p>Drop the PDF here ...</p> :
                    <p>Drag 'n' drop a PDF file here, or click to select a file</p>
                }
                {file && <div>Uploaded File: {file.name}</div>}
            </div>)}
            <button onClick={handleSubmit}>Analyze your appointment 🤖</button>
            {modalOpen && analysisResults && (
                <MultiStepConfirmation data={analysisResults} onClose={handleClose} />
            )}
            <AppointmentList userId={'1'} />
        </div>
    );
};

export default AppointmentManager;
