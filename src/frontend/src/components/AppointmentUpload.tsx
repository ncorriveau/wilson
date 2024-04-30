import React, { useState } from 'react';

interface PdfUploaderProps {
}

const apiUrl = 'http://localhost:8000/api/v1/appointments';

const PdfUploader: React.FC<PdfUploaderProps> = () => {
    const [file, setFile] = useState<File | null>(null);

    const handleFileChange = (event: React.ChangeEvent<HTMLInputElement>) => {
        setFile(event.target.files ? event.target.files[0] : null);
    };

    const handleUpload = async () => {
        if (!file) {
            alert('Please select a file first!');
            return;
        }

        const formData = new FormData();
        formData.append('file', file);

        try {
            const response = await fetch(apiUrl, {
                method: 'POST',
                body: formData,
            });

            if (response.ok) {
                alert('File uploaded successfully!');
            } else {
                alert('Failed to upload the file.');
            }
        } catch (error) {
            alert('An error occurred while uploading the file.');
            console.error('Upload error:', error);
        }
    };

    return (
        <div className="uploader">
            <h1>Upload PDF</h1>
            <input type="file" accept=".pdf" onChange={handleFileChange} />
            <button onClick={handleUpload}>Upload</button>
        </div>
    );
};

export default PdfUploader;
