"use client";

import "./navbar.css";
import { useNavigate } from "react-router-dom";
import { useAuthActions } from "../../service/auth/useAuth";
import { useTestEmail } from "../../service/auth/useAuthService";
import { useAuthRequestPasswordChangeService } from "../../service/auth/useAuthService";
import { useAuthRequestEmailVerificationService } from "../../service/auth/useAuthService";
import toast from "react-hot-toast";
import { ScanSearch, Clock, User, LogOut } from "lucide-react";

const Navbarr = ({ onTabChange, user, isLoaded }) => {
  const { logOut } = useAuthActions();
  const navigate = useNavigate();
  const testEmail = useTestEmail();
  const sendLinkPassword = useAuthRequestPasswordChangeService();
  const sendLinkEmailVerification = useAuthRequestEmailVerificationService();

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

  const handleVerifyEmail = async () => {
    if (user && user.email) {
      try {
        const res = await sendLinkEmailVerification({
          email: user.email,
        });
        toast.success("Verification email sent!");
      } catch (error) {
        toast.error("Failed to send verification email: " + error.message);
      }
    } else {
      toast.error("User email not available");
    }
  };

  const handleSetPassword = async () => {
    if (user && user.email) {
      try {
        const res = await sendLinkPassword();
        if (!res.ok) {
          toast.error("Password set email fault");
        }
        toast.success("Password set email sent!");
      } catch (error) {
        toast.error("Error setting password:", error);
      }
    } else {
      toast.error("User email not available");
    }
  };

  const handleResetPassword = async () => {
    if (user && user.email) {
      try {
        const res = await sendLinkPassword();
        if (!res.ok) {
          toast.error("Password reset email fault");
        }
        toast.success("Password reset email sent!");
      } catch (error) {
        toast.error("Failed to send password reset email: " + error.message);
      }
    } else {
      toast.error("User email not available");
    }
  };

  const handleTestEmail = async () => {
    if (user && user.email) {
      try {
        const res = await testEmail({
          email: user.email,
          username: user.username,
        });
        if (!res.ok) {
          toast.error("Test email failed");
        }
        toast.success(res.message);
      } catch (error) {
        toast.error("Failed to send test email: " + error.message);
      }
    } else {
      toast.error("User email not available");
    }
  };

  return (
    <nav className="header">
      <div className="header-title-btn">
        <h1 className="header-title">UET Smart Foody</h1>
        <div className="header-tabs">
          <button className="tab" onClick={() => onTabChange("Detect")}>
            <ScanSearch className="tab-icon" size={16} />
            <span className="tab-text">Detection</span>
          </button>

          <button className="tab" onClick={() => onTabChange("History")}>
            <Clock className="tab-icon" size={16} />
            <span className="tab-text">History</span>
          </button>
        </div>
      </div>
      <div className="header-actions">
        {!isLoaded ? (
          <div className="loading-indicator">Loading...</div>
        ) : user ? (
          <>
            <div className="dropdown">
              <button className="tab">
                <User className="user-icon" size={16} />
                <span className="tab-text">{user.username || user.email}</span>
              </button>

              <div className="dropdown-content">
                <div className="user-container">
                  <div className="detail-row">
                    <strong>Username:</strong>{" "}
                    <span id="username">{user.username}</span>
                  </div>
                  <div className="detail-row">
                    <strong>Email:</strong> <span id="email">{user.email}</span>
                  </div>
                  <div className="detail-row">
                    <strong>Email Verified:</strong>{" "}
                    <span id="email-verified">
                      {user.email_verified ? "Yes" : "No"}
                    </span>
                  </div>
                  <div className="detail-row">
                    <strong>Provider:</strong>{" "}
                    <span id="provider">{user.provider}</span>
                  </div>
                  <div className="detail-row">
                    <strong>Providers:</strong>{" "}
                    <span id="provider">{user.providers?.join(", ")}</span>
                  </div>

                  {user.email_verified === true ? null : (
                    <button
                      className="btn verify-btn"
                      id="verifyBtn"
                      onClick={handleVerifyEmail}
                    >
                      Verify Email
                    </button>
                  )}

                  {user.has_password === true ? (
                    <button
                      className="btn pwd-btn"
                      id="pwdBtn"
                      onClick={handleResetPassword}
                    >
                      Change Password
                    </button>
                  ) : (
                    <button
                      className="btn pwd-btn"
                      id="pwdBtn"
                      onClick={handleSetPassword}
                    >
                      Set Password
                    </button>
                  )}
                </div>
              </div>
            </div>
            <button className="tab" onClick={handleLogout}>
              <LogOut className="logout-icon" size={16} />
              <span className="tab-text">Đăng xuất</span>
            </button>
            {/* |
            <button
              className="header-btn test-email-btn"
              onClick={handleTestEmail}
            >
              Test Email
            </button> */}
          </>
        ) : (
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
