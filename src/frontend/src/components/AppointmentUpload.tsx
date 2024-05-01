import React, { useState } from 'react';

interface PdfUploaderProps {
}

const apiUrl = 'http://localhost:8000/api/v1/chat_w_data/upload-pdf/';

const PdfUploader: React.FC<PdfUploaderProps> = () => {
    const [file, setFile] = useState<File | null>(null);
    const [userId, setUserId] = useState<string>('');

    const handleFileChange = (event: React.ChangeEvent<HTMLInputElement>) => {
        setFile(event.target.files ? event.target.files[0] : null);
    };
    const handleUserIdChange = (event: React.ChangeEvent<HTMLInputElement>) => {
        setUserId(event.target.value);
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
                headers: { 
                    'x-user-id': userId,
                },
                body: formData,
            });

            if (response.ok) {
                const data = await response.json();
                alert(`File uploaded successfully! Server response: ${JSON.stringify(data)}`);
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
        <input type="text" placeholder="Enter user ID" value={userId} onChange={handleUserIdChange} />
        <input type="file" accept="application/pdf" onChange={handleFileChange} />
        <button onClick={handleUpload}>Upload</button>
    </div>
    );
};

export default PdfUploader;
