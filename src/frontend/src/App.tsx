import { useEffect, useState } from "react";
import {
  BrowserRouter as Router,
  Route,
  Routes,
  Link,
  Navigate,
} from "react-router-dom";
import AppointmentManager from "./components/Appointments/Appointments";
import ChatApp from "./components/Chat/ChatApp";
import LoginPage from "./components/Auth/Login";
import Prescriptions from "./components/Prescriptions/Prescriptions";
import "./index.css";

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

  return (
    <Router>
      <div>
        <nav>
          <ul>
            <li>
              <Link to="/appointments">Appointments 🩺 </Link>
            </li>
            <li>
              <Link to="/chat">Chat with your data! 🤖 </Link>
            </li>
            <li>
              <Link to="/prescriptions">Prescriptions 💊 </Link>
            </li>
            <li>
              <Link to="/login">Login</Link>
            </li>
          </ul>
        </nav>

        <Routes>
          {token && userId ? (
            <>
              <Route
                path="/appointments"
                element={<AppointmentManager token={token} userId={userId} />}
              />
              <Route
                path="/chat"
                element={<ChatApp token={token} userId={userId} />}
              />
              <Route
                path="/prescriptions"
                element={<Prescriptions token={token} userId={userId} />}
              />
            </>
          ) : (
            <Navigate to="/login" />
          )}
          <Route
            path="/login"
            element={<LoginPage setToken={handleSetToken} />}
          />
        </Routes>
      </div>
    </Router>
  );
};

export default App;
