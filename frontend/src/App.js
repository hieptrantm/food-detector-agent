import React, { useState, useEffect } from 'react';
import './App.css';
import Navbarr from './components/navbar/navbar';
import Sidebar from './components/sidebar/sidebar';
import ImageUpload from './components/imageUpload/imageUpload';
import { useAuth } from './service/auth/useAuth.js';

function App() {
  const [token, setToken] = useState('');
  const [text, setText] = useState('');
  const [result, setResult] = useState(null);
  const [loading, setLoading] = useState(false);

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

  const handleDetect = async (e) => {
    e.preventDefault();
    
    // if (!token) {
    //   alert('Vui lòng đăng nhập trước!');
    //   return;
    // }
    
    setLoading(true);
    
    try {
      const response = await fetch('/ai/detect', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${token}`
        },
        body: JSON.stringify({ text })
      });
      
      const data = await response.json();
      
      if (response.ok) {
        setResult(data);
      } else {
        alert('Phát hiện thất bại: ' + data.detail);
      }
    } catch (error) {
      alert('Lỗi kết nối: ' + error.message);
    } finally {
      setLoading(false);
    }
  };

  const handleImageDetect = async () => {
    // if (!token) {
    //   alert('Vui lòng đăng nhập trước!');
    //   return;
    // }

    if (!uploadedImage) {
      alert('Vui lòng chọn ảnh trước!');
      return;
    }

    
    setLoading(true);
    
    try {
      const response = await fetch('/ai/detect', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${token}`
        },
        body: JSON.stringify({ image: uploadedImage })
      });

      const data = await response.json();

      if (response.ok) {
        setResult(data);
      } else {
        alert('Phát hiện thất bại: ' + data.detail);
      }
    } catch (error) {
      alert('Lỗi kết nối: ' + error.message);
    } finally {
      setLoading(false);
    }
  };

  const handleLogout = () => {
    setToken('');
    setResult(null);
    setShowMenu(false);
  };

  return (
    <div className="app-container">
      {/* Header */}
      <Sidebar isCollapsed={sidebarCollapsed} onToggle={toggleSidebar} />

      {/* Main Content */}
      <div className={`main-content ${sidebarCollapsed ? 'expanded' : ''}`}>
        <Navbarr user={user} isLoaded={isLoaded}/>
        <div className="content-area">
          <ImageUpload image={uploadedImage} onImageChange={setUploadedImage} />
          THE RECIPES ARE HERE 
        {/* Main Content */}
        <div className={`main-content ${sidebarCollapsed ? 'expanded' : ''}`}>
          <Navbarr />
          <div className="content-area">
            <ImageUpload 
              image={uploadedImage} 
              onImageChange={setUploadedImage}
              onSend={handleImageDetect}
              isLoading={loading}
            />
            {result && (
              <div className="detection-result">
                <h2>Kết quả phát hiện:</h2>
                <pre>{JSON.stringify(result, null, 2)}</pre>
              </div>
            )}
            THE RECIPES ARE HERE 
          </div>
        </div>
      </div>
    </div>
  );
}

export default App;