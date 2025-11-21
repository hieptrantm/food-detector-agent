import { useState, useEffect } from 'react';
import './App.css';
import Navbarr from './components/navbar/navbar';
import Sidebar from './components/sidebar/sidebar';
import ImageUpload from './components/imageUpload/imageUpload';
import { useAuth } from './service/auth/useAuth.js';
import { Toaster } from "react-hot-toast";

function App() {
  const [sidebarCollapsed, setSidebarCollapsed] = useState(false);
  const [uploadedImage, setUploadedImage] = useState(null);
  const [isMobile, setIsMobile] = useState(false);

  const { user, isLoaded } = useAuth();
  
  const checkMobile = () => {
    const mobile = window.innerWidth <= 768;
    setIsMobile(mobile);
    if (mobile) {
      setSidebarCollapsed(false);
    }
  };
  
  useEffect(() => {

    checkMobile();
    window.addEventListener('resize', checkMobile);
    return () => window.removeEventListener('resize', checkMobile);
  }, [isLoaded]);

  const toggleSidebar = () => {
    setSidebarCollapsed(!sidebarCollapsed);
  };

  return (
    <div className="app-container">
      <Toaster position='bottom-right' />
      {/* Header */}
      <Sidebar isCollapsed={sidebarCollapsed} onToggle={toggleSidebar} />

      {/* Main Content */}
      <div className={`main-content ${sidebarCollapsed ? 'expanded' : ''}`}>
        <Navbarr user={user} isLoaded={isLoaded}/>
        <div className="content-area">
          <ImageUpload image={uploadedImage} onImageChange={setUploadedImage} />
          THE RECIPES ARE HERE 
        </div>
      </div>
    </div>
  );
}

export default App;