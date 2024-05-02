// MultiStepConfirmation.tsx
import React, { useState } from 'react';


interface ConfirmationData {
    Perscriptions: {
      drugs: {
        technical_name: string;
        brand_name: string;
        instructions: string;
      }[];
    };
    AppointmentMeta: {
      provider_info: {
        first_name: string;
        last_name: string;
        degree: string;
        email: string | null;
        phone_number: string | null;
        npi: string;
        location: string | null;
        specialty: string;
      };
      datetime: string;
    };
    FollowUps: {
      tasks: {
        task: string;
      }[];
    };
    Summary: {
      summary: string;
    };
  }

interface MultiStepConfirmationProps {
    data: ConfirmationData;
    onClose: () => void; // Function to call when the entire process is completed or canceled
}

const MultiStepConfirmation: React.FC<MultiStepConfirmationProps> = ({ data, onClose }) => {
    
    console.log("Provider Info: ", data.AppointmentMeta.provider_info);
    console.log("Perscriptions: ", data.Perscriptions);
    console.log("Follow Ups: ", data.FollowUps);
    
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
                        <p>{data.AppointmentMeta.provider_info.first_name} {data.AppointmentMeta.provider_info.last_name}, {data.AppointmentMeta.provider_info.specialty}</p>
                        <button onClick={handleNext}>Next</button>
                    </>
                )}
                {step === 2 && (
                    <>
                        <h2>Confirm Prescriptions</h2>
                        <ul>
                            {data.Perscriptions.drugs.map((drug, index) => (
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
                            {data.FollowUps.tasks.map((task, index) => (
                                <li key={index}>{task.task}</li>
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
