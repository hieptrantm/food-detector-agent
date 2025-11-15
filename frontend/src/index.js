import React from 'react';
import ReactDOM from 'react-dom/client';
import './index.css';
import App from './App';
import { BrowserRouter as Router, Route, Routes } from 'react-router-dom';
import SignIn from './app/sign-in/sign-in.jsx';
import SignUp from './app/sign-up/sign-up.jsx';
import AuthProvider from './service/auth/authProvider';
import GoogleAuthProvider from './service/auth/googleProvider';


const root = ReactDOM.createRoot(document.getElementById('root'));
root.render(
  <React.StrictMode>
    <AuthProvider>
      <GoogleAuthProvider>
        <Router>
          <Routes>
            <Route path="/" element={<App />} />
            <Route path="/sign-in" element={<SignIn />} />
            <Route path="/sign-up" element={<SignUp />} />
            <Route path="*" element={<h1>404 Not Found</h1>} />
          </Routes>
        </Router>
      </GoogleAuthProvider>
    </AuthProvider>
  </React.StrictMode>
);