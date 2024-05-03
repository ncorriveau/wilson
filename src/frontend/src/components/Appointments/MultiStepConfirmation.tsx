import React, { useState } from 'react';

interface PrescriptionData {
    technical_name: string;
    brand_name: string;
    instructions: string;
}

interface ConfirmationData {
    prescriptions: PrescriptionData[];
    provider_info: {
        first_name: string;
        last_name: string;
        specialty: string;
    };
    follow_ups: string[];
    summary: string;
  };

interface MultiStepConfirmationProps {
    data: ConfirmationData;
    onClose: () => void; // Function to call when the entire process is completed or canceled
}

const MultiStepConfirmation: React.FC<MultiStepConfirmationProps> = ({ data, onClose }) => {
    
    console.log("Provider Info: ", data.provider_info);
    console.log("Perscriptions: ", data.prescriptions);
    console.log("Follow Ups: ", data.follow_ups);
    
    const [step, setStep] = useState(1);
    const handleNext = () => {
        if (step < 3) setStep(step + 1);
    };
    const handlePrevious = () => {
        if (step > 1) setStep(step - 1);
    };
    const handleFinish = () => {
        console.log("Finish");
        onClose(); // Perhaps send final confirmation to the server or close the dialog
    };

    return (
        <div className="modal">
            <div className="modal-content">
                {step === 1 && (
                    <>
                        <h2>Confirm Provider Information</h2>
                        <p>{data.provider_info.first_name} {data.provider_info.last_name}, {data.provider_info.specialty}</p>
                        <button onClick={handleNext}>Next</button>
                    </>
                )}
                {step === 2 && (
                    <>
                        <h2>Confirm Prescriptions</h2>
                        <ul>
                            {data.prescriptions.map((drug, index) => (
                                <li key={index}>{drug.brand_name}: {drug.instructions}</li>
                            ))}
                        </ul>
                        <button onClick={handlePrevious}>Previous</button>
                        <button onClick={handleNext}>Next</button>
                    </>
                )}
                {step === 3 && (
                    <>
                        <h2>Confirm Follow Up Tasks</h2>
                        <ul>
                            {data.follow_ups.map((task, index) => (
                                <li key={index}>{task}</li>
                            ))}
                        </ul>
                        <button onClick={handlePrevious}>Previous</button>
                        <button onClick={handleFinish}>Finish</button>
                    </>
                )}
            </div>
        </div>
    );
};

export default MultiStepConfirmation;
