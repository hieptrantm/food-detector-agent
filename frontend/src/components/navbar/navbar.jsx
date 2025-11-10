"use client";

import "./navbar.css";
import { useNavigate } from "react-router-dom";
import { useAuth, useAuthActions } from "../../service/auth/useAuth.js";

const Navbarr = ({ onMenuClick }) => {
  const { user, isLoaded } = useAuth();
  const { logOut } = useAuthActions();
  const navigate = useNavigate();

  const handleSignUp = () => {
    navigate("/sign-up");
  };

  const handleSignIn = () => {
    navigate("/sign-in");
  };

  const handleLogout = async () => {
    await logOut();
    navigate("/");
  };

  const handleProfile = () => {
    navigate("/profile");
  };

  return (
    <nav className="header">
      <button className="menu-btn" onClick={onMenuClick}>
        <div className="menu-icon"></div>
      </button>
      <h1 className="header-title">INGRIDIENTS DETECTION</h1>
      <div className="header-tabs">
        <button className="tab">Food detection</button>
        <button className="tab">History</button>
      </div>
      <div className="header-actions">
        {!isLoaded ? (
          <div className="loading-indicator">Loading...</div>
        ) : user ? (
          <>
            <span className="user-name">
              Xin chào, {user.username || user.email}
            </span>
            {/* <button className="user-avatar" onClick={handleProfile}>
              {user.photoURL ? (
                <img src={user.photoURL} alt="Avatar" className="avatar-img" />
              ) : (
                <span className="avatar-initial">
                  {(user.displayName || user.email || "U")[0].toUpperCase()}
                </span>
              )}
            </button> */}
            <button className="header-btn logout-btn" onClick={handleLogout}>
              Đăng xuất
            </button>
          </>
        ) : (
          // Logged out state
          <>
            <button className="header-btn" onClick={handleSignUp}>
              Đăng ký
            </button>
            <button className="header-btn" onClick={handleSignIn}>
              Đăng nhập
            </button>
          </>
        )}
      </div>
    </nav>
  );
};

export default Navbarr;
