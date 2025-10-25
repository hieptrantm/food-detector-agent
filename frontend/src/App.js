import React, { useState } from 'react';
import './App.css';

function App() {
  const [email, setEmail] = useState('');
  const [provider, setProvider] = useState('google');
  const [token, setToken] = useState('');
  const [text, setText] = useState('');
  const [result, setResult] = useState(null);
  const [loading, setLoading] = useState(false);
  const [showMenu, setShowMenu] = useState(false);

  const handleLogin = async (e) => {
    e.preventDefault();
    setLoading(true);
    
    try {
      const response = await fetch('/auth/login', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ email, provider })
      });
      
      const data = await response.json();
      
      if (response.ok) {
        setToken(data.access_token);
        alert('Đăng nhập thành công!');
      } else {
        alert('Đăng nhập thất bại!');
      }
    } catch (error) {
      alert('Lỗi kết nối: ' + error.message);
    } finally {
      setLoading(false);
    }
  };

  const handleDetect = async (e) => {
    e.preventDefault();
    
    if (!token) {
      alert('Vui lòng đăng nhập trước!');
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

  const handleLogout = () => {
    setToken('');
    setResult(null);
    setShowMenu(false);
  };

  return (
    <div className="app-container">
      {/* Header */}
      <header className="app-header">
        <div className="header-content">
          <div className="logo">
            <span className="logo-icon"></span>
            <h1 className="app-title">Food Detection App</h1>
          </div>
          
          {token && (
            <div className="avatar-wrapper">
              <button
                onClick={() => setShowMenu(!showMenu)}
                className={`avatar-button ${showMenu ? 'active' : ''}`}
              >
                👤
              </button>
              
              {showMenu && (
                <div className="dropdown-menu">
                  <div className="dropdown-header">
                    Đã đăng nhập
                  </div>
                  <button onClick={handleLogout} className="logout-button">
                    🚪 Đăng xuất
                  </button>
                </div>
              )}
            </div>
          )}
        </div>
      </header>

      {/* Main Content */}
      <main className="main-content">
        {!token ? (
          <div className="login-container">
            <div className="login-section">
              <div className="login-header">
                <div className="logo-icon"></div>
                <h2 className="login-title">Đăng nhập</h2>
                <p className="login-subtitle">Đăng nhập để sử dụng dịch vụ phát hiện spam</p>
              </div>
              
              <div className="login-form">
                <div className="form-group">
                  <label className="form-label">Email</label>
                  <input
                    type="email"
                    placeholder="example@email.com"
                    value={email}
                    onChange={(e) => setEmail(e.target.value)}
                    className="form-input"
                  />
                </div>
                
                {/* <div className="form-group">
                  <label className="form-label"></label>
                  <select 
                    value={provider} 
                    onChange={(e) => setProvider(e.target.value)}
                    className="form-select"
                  >
                    <option value="google">Google</option>
                  </select>
                </div> */}
                
                <button 
                  onClick={handleLogin}
                  disabled={loading}
                  className="submit-button"
                >
                  {loading ? 'Đang xử lý...' : 'Đăng nhập'}
                </button>
              </div>
            </div>
          </div>
        ) : (
          <div className="main-section">
            <div className="detect-section">
              <div className="detect-header">
                <h2 className="detect-title">AI Spam Detection</h2>
                <p className="detect-subtitle">Nhập văn bản để kiểm tra spam với độ chính xác cao</p>
              </div>
              
              <div className="detect-form">
                <div className="form-group">
                  <label className="form-label">Văn bản cần kiểm tra</label>
                  <textarea
                    placeholder="Nhập hoặc dán văn bản cần kiểm tra spam tại đây..."
                    value={text}
                    onChange={(e) => setText(e.target.value)}
                    className="form-textarea"
                  />
                </div>
                
                <button 
                  onClick={handleDetect}
                  disabled={loading}
                  className="detect-button"
                >
                  {loading ? (
                    <>
                      <div className="spinner"></div>
                      Đang phát hiện...
                    </>
                  ) : (
                    <>
                      Phát hiện Spam
                    </>
                  )}
                </button>
              </div>
              
              {result && (
                <div className={`result ${result.is_spam ? 'spam' : 'safe'}`}>
                  <h3 className="result-title">
                    Kết quả phân tích
                  </h3>
                  <div className="result-content">
                    <div className="result-item">
                      <span className="result-label">Loại:</span>
                      <span className="result-value">{result.category}</span>
                    </div>
                    <div className="result-item">
                      <span className="result-label">Spam:</span>
                      <span className={`result-value ${result.is_spam ? 'spam-text' : 'safe-text'}`}>
                        {result.is_spam ? '⚠️ CÓ' : '✅ KHÔNG'}
                      </span>
                    </div>
                    <div className="result-item">
                      <span className="result-label">Độ tin cậy:</span>
                      <span className="result-value confidence-text">
                        {(result.confidence * 100).toFixed(1)}%
                      </span>
                    </div>
                  </div>
                </div>
              )}
            </div>
          </div>
        )}
      </main>
    </div>
  );
}

export default App;