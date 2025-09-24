import { useEffect } from "react";
import "./App.css";
import { BrowserRouter, Routes, Route } from "react-router-dom";
import axios from "axios";
import RealEstatePage from "./components/RealEstatePage";
import AdminPanel from "./components/AdminPanel";

const API_BASE = process.env.REACT_APP_API_URL || 'http://localhost:8000';
const API = `${API_BASE}/api`;

function App() {
  // Test API connection on app load
  useEffect(() => {
    const testApi = async () => {
      try {
        const response = await axios.get(`${API}/`);
        console.log('API connected:', response.data.message);
      } catch (e) {
        console.error('API connection error:', e);
      }
    };
    testApi();
  }, []);

  return (
    <div className="App">
      <BrowserRouter>
        <Routes>
          <Route path="/" element={<RealEstatePage />} />
          <Route path="/admin" element={<AdminPanel />} />
        </Routes>
      </BrowserRouter>
    </div>
  );
}

export default App;
