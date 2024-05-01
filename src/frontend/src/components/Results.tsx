import React from "react";
import './Results.css';

interface ConfirmationDialogProps {
    results: any;
    onConfirm: () => void;
    onCancel: () => void;
}

const ResultsDisplay: React.FC<ConfirmationDialogProps> = ({ results, onConfirm, onCancel }) => {
    console.log(results)
    return (
        <div className="modal">
          <div className="modal-content">
            <h2>Confirm Information</h2>
            <p>Extracted Provider: {results?.AppointmentMeta.provider_info.first_name} {results?.AppointmentMeta.provider_info.last_name}, {results?.AppointmentMeta.provider_info.specialty}</p>
            {/* Display other results similarly */}
            <button onClick={onConfirm}>Confirm</button>
            <button onClick={onCancel}>Cancel</button>
          </div>
        </div>
      );
};
export default ResultsDisplay;