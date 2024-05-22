import { useEffect, useState } from "react";
import AppointmentManager from "./components/Appointments/Appointments";
import ChatApp from "./components/Chat/ChatApp";
import LoginPage from "./components/Auth/Login";
import Prescriptions from "./components/Prescriptions/Prescriptions";

const App = () => {
  const [token, setToken] = useState<string | null>(null);
  const [userId, setUserId] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);

  const handleSetToken = (token: string, userId: string) => {
    setToken(token);
    setUserId(userId);
  };
  useEffect(() => {
    const savedToken = localStorage.getItem("token");
    const savedUserId = localStorage.getItem("userId");

    if (savedToken && savedUserId) {
      handleSetToken(savedToken, savedUserId);
    }
    setLoading(false); // Finished checking local storage
  }, []);

  console.log("token is: ", token);
  console.log("userId is: ", userId);

  if (loading) {
    return <div>Loading...</div>;
  }

  if (!token || !userId) {
    return <LoginPage setToken={handleSetToken} />;
  }
  return (
    <div className="App">
      <ChatApp token={token} userId={userId} />
    </div>
  );
};

export default App;
