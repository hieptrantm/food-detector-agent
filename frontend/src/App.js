import { useState, useEffect } from 'react';
import './App.css';
import Navbarr from './components/navbar/navbar';
import History  from './components/history/history.jsx';
import Detect from './components/detect/detect.jsx';
import { useAuth } from './service/auth/useAuth.js';
import toast from 'react-hot-toast';

function App() {
  const [mainContent, setMainContent] = useState("Detect")
  const { user, isLoaded } = useAuth();

  const onTabChange = (tab) => {
    if (!user) {
      toast.error("Please log in to access this feature.");
    }
    setMainContent(tab)
  }

  const renderScreen = () => {
    switch (mainContent) {
      case "Detect":
        return <Detect user={user} />;
      case "History":
        return user?.id
          ? <History userId={user.id} />
          : <Detect user={user} />;
      default:
        return <Detect user={user} />;
    }
  };

  return (
    <div className="app-container">
      {/* Main Content */}
      <div className='main-content'> 
        <div className='navbar'>
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