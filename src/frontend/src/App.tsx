import { useState } from "react";
import AppointmentManager from "./components/Appointments/Appointments";
import ChatApp from "./components/Chat/ChatApp";
import LoginPage from "./components/Auth/Login";
import Prescriptions from "./components/Prescriptions/Prescriptions";

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
      { !token || !userId ? <LoginPage setToken={handleSetToken} /> : <ChatApp token={ token } userId={ userId }/> }
    </div>
  );
};

export default App;

// return (
//   <Router>
//     <div className="App">
//       <Routes>
//         <Route path="/prescriptions" element={ 
//           !token || !userId ? <LoginPage setToken={handleSetToken} /> : <Prescriptions token={token} userId={userId} />
//         } />
//         <Route path="/" element={
//           !token || !userId ? <LoginPage setToken={handleSetToken} /> : <AppointmentManager token={token} userId={userId} />
//         } />
//       </Routes>
//     </div>
//   </Router>
// );
// };