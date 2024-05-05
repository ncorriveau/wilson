import { useState } from "react";
import AppointmentManager from "./components/Appointments/Appointments";
import LoginPage from "./components/Auth/Login";

// import './App.css'

const App = () => {
  const [token, setToken] = useState<string | null>(null);
  const [userId, setUserId] = useState<string | null>(null);
  
  const handleSetToken = (token: string, userId: string) => {
    setToken(token);
    setUserId(userId);
  }

  return (
    <div className="App">
      { !token ? <LoginPage setToken={handleSetToken} /> : <AppointmentManager /> }
    </div>
  );
};

export default App;
