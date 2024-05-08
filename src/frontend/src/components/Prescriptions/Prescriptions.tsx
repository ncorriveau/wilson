import React, { useState, useEffect } from "react";
import axios from "axios";

interface PrescriptionProps {
  token: string;
  userId: string;
}

interface ProviderInfo  {
    firstName: string;
    lastName: string;
    specialty: string;
}

interface Prescription {
    id: number;
    brandName: string;
    technicalName: string;
    instructions: string;
    providerInfo: ProviderInfo;
    isActive: boolean;
}


const apiUrl = "http://localhost:8000/api/v1/prescriptions/";

const Prescriptions: React.FC<PrescriptionProps> = ({ token, userId }) => {
    const [prescriptions, setPrescriptions] = useState<Prescription[]>([]);
    const [loading, setLoading] = useState(false);

    useEffect(() => {
        const fetchPrescriptions = async () => {
            try {
                setLoading(true);
                const response = await axios.get(`${apiUrl}${userId}`, {
                    headers: {
                        Authorization: `Bearer ${token}`,
                    }
                });
                if (response.status === 200) {
                    const data = await response.data;
                    console.log('data ', data)
                    setPrescriptions(data);
                }
            } catch (error) {
                console.error("Error fetching prescriptions:", error);
            } finally {
                setLoading(false);
            }
        };
        fetchPrescriptions();
    }, [userId, token]);

    const toggleActiveStatus = async (prescription: Prescription) => {
        if (window.confirm("Are you sure you want to change the status of this prescription?")) {
            try {
                const updatedPrescription = { ...prescription, isActive: !prescription.isActive };
                const response = await axios.put(`${apiUrl}${prescription.id}`, updatedPrescription, {
                    headers: {
                        Authorization: `Bearer ${token}`,
                    }
                });
                if (response.status === 200) {
                    setPrescriptions(prev =>
                        prev.map(p =>
                            p.id === prescription.id ? updatedPrescription : p
                        )
                    );
                }
            } catch (error) {
                console.error("Error updating prescription:", error);
            }
        }
    };

    return (
        <div className="prescriptions">
            <h1>Prescriptions</h1>
            {loading ? (
                <p>Loading...</p>
            ) : (
                prescriptions && prescriptions.map(prescription => (
                    <div key={prescription.id} className="prescription">
                        <h2>{prescription.brandName}</h2>
                        <p>Technical Name: {prescription.technicalName}</p>
                        <p>Instructions: {prescription.instructions}</p>
                        <p>Prescribing Physician: {`${prescription.providerInfo.firstName} ${prescription.providerInfo.lastName}, ${prescription.providerInfo.specialty}`}</p>
                        <div className="status">`
                            <span
                                className={`status-icon ${prescription.isActive ? 'active' : 'inactive'}`}
                                onClick={() => toggleActiveStatus(prescription)}
                            >
                                {prescription.isActive ? '✅ ' : '⛔️'}
                            </span>
                            {prescription.isActive ? "Active" : "Inactive"}
                        </div>
                    </div>
                ))
            )}
        </div>
    );
};

export default Prescriptions;
