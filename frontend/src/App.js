import { useState, useEffect } from 'react';
import './App.css';
import Navbarr from './components/navbar/navbar';
import Sidebar from './components/sidebar/sidebar';
import History  from './components/history/history.jsx';
import Detect from './components/detect/detect.jsx';
import { useAuth } from './service/auth/useAuth.js';
import { Toaster } from "react-hot-toast";
import {Menu} from "lucide-react"

function App() {
  const [sidebarOpen, setSidebarOpen] = useState(true);
  const [mainContent, setMainContent] = useState("Detect")

  const { user, isLoaded } = useAuth();
  
  useEffect(() => {
    const handleResize = () => {
      if (window.innerWidth < 768) {
        setSidebarOpen(false);
      } else {
        setSidebarOpen(true);
      }
    };
    
    handleResize(); // Check on mount
    window.addEventListener('resize', handleResize);
    return () => window.removeEventListener('resize', handleResize);
  }, []);

  const onTabChange = (tab) => {
    setMainContent(tab)
  }

  const renderScreen = () => {
    switch (mainContent) {
      case "Detect":
        return <Detect />;
      case "History":
        return <History />;
      default:
        return <Detect />;
    }
  };

  return (
    <div className="app-container">
      <Toaster position='bottom-right' />
      {/* Header */}
      <div>
        <Sidebar  sidebarOpen={sidebarOpen} setSidebarOpen={setSidebarOpen} />
      </div>
      {/* Main Content */}
      <div className='main-content'> 
        <div className='navbar'>
          <button
            onClick={() => setSidebarOpen(true)}
            className="menu-button"
          >
            <Menu size={20} />
          </button>
            <Navbarr onTabChange={onTabChange} user={user} isLoaded={isLoaded}/>
        </div>
        <div>
          {renderScreen()}
        </div>
      </div>
    </div>
  );
}

export default App;