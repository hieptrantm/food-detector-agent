"use client";

import { useState } from "react";
import { useNavigate } from "react-router-dom";
import { useAuthActions, useAuthTokens } from "../../service/auth/useAuth.js";
import { useAuthLoginService } from "../../service/auth/useAuthService.js";
import "./sign-in.css";

// Sign In Component
const SignIn = () => {
  const [formData, setFormData] = useState({
    email: "",
    password: "",
  });

  const navigate = useNavigate();

  const handleExit = () => {
    navigate(-1);
  };

  const handleSignUp = () => {
    navigate("/sign-up");
  };

  const handleChange = (e) => {
    setFormData({
      ...formData,
      [e.target.name]: e.target.value,
    });
  };

  const { setUser } = useAuthActions();
  const { setTokensInfo } = useAuthTokens();
  const fetchAuthLogin = useAuthLoginService();

  const handleSubmit = async (e) => {
    e.preventDefault();

    try {
      console.log("Sign in:", formData);

      const res = await fetchAuthLogin({
        email: formData.email,
        password: formData.password,
        provider: "email",
      });

      setTokensInfo({
        token: res.access_token,
        refreshToken: res.refresh_token,
        tokenExpires: res.token_expires,
      });

      if (res.user) {
        setUser(res.user);
      }

      navigate("/");
    } catch (error) {
      console.error("Login failed:", error);
      alert("Đăng nhập thất bại. Vui lòng kiểm tra lại thông tin!");
    }
  };

  return (
    <div className="container" onClick={handleExit}>
      <div className="auth-modal" onClick={(e) => e.stopPropagation()}>
        <button className="close-btn" onClick={handleExit}>
          ×
        </button>

        <div className="auth-header">
          <h2>Đăng nhập</h2>
          <p>Chào mừng bạn trở lại!</p>
        </div>

        <div className="auth-form">
          <div className="form-group">
            <label htmlFor="email">Email</label>
            <input
              type="email"
              id="email"
              name="email"
              value={formData.email}
              onChange={handleChange}
              placeholder="Nhập email của bạn"
            />
          </div>

          <div className="form-group">
            <label htmlFor="password">Mật khẩu</label>
            <input
              type="password"
              id="password"
              name="password"
              value={formData.password}
              onChange={handleChange}
              placeholder="Nhập mật khẩu"
            />
          </div>

          <div className="form-options">
            <label className="remember-me">
              <input type="checkbox" />
              <span>Ghi nhớ đăng nhập</span>
            </label>
            <button className="forgot-password">Quên mật khẩu?</button>
          </div>

          <button className="auth-submit-btn" onClick={handleSubmit}>
            Đăng nhập
          </button>
        </div>

        <div className="auth-divider">
          <span>hoặc</span>
        </div>

        <div className="social-login">
          <button className="social-btn google-btn">
            <span className="social-icon">G</span>
            Đăng nhập với Google
          </button>
          {/* <button className="social-btn facebook-btn">
            <span className="social-icon">f</span>
            Đăng nhập với Facebook
          </button> */}
        </div>

        <div className="auth-footer">
          <p>
            Chưa có tài khoản?{" "}
            <button className="switch-btn" onClick={handleSignUp}>
              Đăng ký ngay
            </button>
          </p>
        </div>
      </div>
    </div>
  );
};

export default SignIn;
