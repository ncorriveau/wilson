import { useState } from "react";
import AppointmentManager from "./components/Appointments/Appointments";
import ChatApp from "./components/Chat/ChatApp";
import LoginPage from "./components/Auth/Login";
import Prescriptions from "./components/Prescriptions/Prescriptions";

const App = () => {
  const [token, setToken] = useState<string | null>(null);
  const [userId, setUserId] = useState<string | null>(null);

  const handleSetToken = (token: string, userId: string) => {
    setToken(token);
    setUserId(userId);
  };

  return (
    <div className="App">
      {!token || !userId ? (
        <LoginPage setToken={handleSetToken} />
      ) : (
        <ChatApp token={token} userId={userId} />
      )}
    </div>
  );
};

export default App;
