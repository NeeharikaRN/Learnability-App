import React, { useState } from 'react';
import axios from 'axios';
import './App.css'; // Import your CSS

const FileUploader = () => {
    const [file, setFile] = useState(null);
    const [audioUrl, setAudioUrl] = useState('');
    const [summaryAudioUrl, setSummaryAudioUrl] = useState(''); // New state for summary audio URL
    const [isUploading, setIsUploading] = useState(false);
    const [isSubmitted, setIsSubmitted] = useState(false);

    const handleFileChange = (event) => {
        setFile(event.target.files[0]);
        setAudioUrl('');
        setSummaryAudioUrl(''); // Reset summary audio URL
        setIsSubmitted(false);
    };

    const handleUpload = async () => {
        if (!file || isUploading) return;

        setIsUploading(true);
        setIsSubmitted(true); // Disable button after the first click
        const formData = new FormData();
        formData.append('file', file);

        try {
            const response = await axios.post('http://localhost:5000/upload', formData, {
                headers: {
                    'Content-Type': 'multipart/form-data',
                },
            });
            setAudioUrl(response.data.audioUrl);
            setSummaryAudioUrl(response.data.summaryAudioUrl); // Set summary audio URL
        } catch (error) {
            console.error('Error uploading file:', error);
        } finally {
            setIsUploading(false);
        }
    };

    return (
        <div>
            <h1>Upload Document</h1>
            <input type="file" accept=".pdf,.docx" onChange={handleFileChange} />
            <button onClick={handleUpload} disabled={isUploading || isSubmitted}>
                {isUploading ? 'Generating...' : 'Upload and Convert'}
            </button>

            {audioUrl && (
                <div>
                    <h2>Complete Context</h2>
                    <audio controls>
                        <source src={audioUrl} type="audio/mpeg" />
                        Your browser does not support the audio element.
                    </audio>
                </div>
            )}

            {summaryAudioUrl && (
                <div>
                    <h2>Summary</h2>
                    <audio controls>
                        <source src={summaryAudioUrl} type="audio/mpeg" />
                        Your browser does not support the audio element.
                    </audio>
                </div>
            )}
        </div>
    );
};

export default FileUploader;