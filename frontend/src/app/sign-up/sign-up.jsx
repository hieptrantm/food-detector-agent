"use client";

import { useState } from "react";
import { useNavigate } from "react-router-dom";
import Cookies from "js-cookie";
import "./sign-up.css";

const SignUp = () => {
  const [formData, setFormData] = useState({
    username: "",
    email: "",
    password: "",
    confirmPassword: "",
  });

  const navigate = useNavigate();

  const handleExit = () => {
    navigate(-1);
  };

  const handleSignIn = () => {
    navigate("/sign-in");
  };

  const handleChange = (e) => {
    setFormData({
      ...formData,
      [e.target.name]: e.target.value,
    });
  };

  const handleSubmit = async () => {
    if (formData.password !== formData.confirmPassword) {
      alert("Mật khẩu không khớp!");
      return;
    }

    try {
      const response = await fetch("/auth/register", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({
          username: formData.fullName,
          email: formData.email,
          password: formData.password,
        }),
      });

      if (!response.ok) {
        const errorData = await response.json();
        throw new Error(errorData.detail || "Đăng ký thất bại!");
      }

      const data = await response.json();

      Cookies.set("access_token", data.access_token, { expires: 1 });

      alert("Đăng ký thành công!");
      navigate("/");
    } catch (error) {
      console.error("Registration error:", error);
      alert(error.message || "Đăng ký thất bại!");
    }
  };

  return (
    <div className="container">
      <div className="auth-modal" onClick={(e) => e.stopPropagation()}>
        <button className="close-btn" onClick={handleExit}>
          ×
        </button>

        <div className="auth-header">
          <h2>Đăng ký</h2>
          <p>Tạo tài khoản mới để bắt đầu</p>
        </div>

        <div className="auth-form">
          <div className="form-group">
            <label htmlFor="fullName">Họ và tên</label>
            <input
              type="text"
              id="fullName"
              name="fullName"
              value={formData.fullName}
              onChange={handleChange}
              placeholder="Nhập họ và tên"
            />
          </div>

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
              placeholder="Tạo mật khẩu (tối thiểu 8 ký tự)"
            />
          </div>

          <div className="form-group">
            <label htmlFor="confirmPassword">Xác nhận mật khẩu</label>
            <input
              type="password"
              id="confirmPassword"
              name="confirmPassword"
              value={formData.confirmPassword}
              onChange={handleChange}
              placeholder="Nhập lại mật khẩu"
            />
          </div>

          <button className="auth-submit-btn" onClick={handleSubmit}>
            Đăng ký
          </button>
        </div>

        <div className="auth-divider">
          <span>hoặc</span>
        </div>

        <div className="social-login">
          <button className="social-btn google-btn">
            <span className="social-icon">G</span>
            Đăng ký với Google
          </button>
          {/* <button className="social-btn facebook-btn">
            <span className="social-icon">f</span>
            Đăng ký với Facebook
          </button> */}
        </div>

        <div className="auth-footer">
          <p>
            Đã có tài khoản?{" "}
            <button className="switch-btn" onClick={handleSignIn}>
              Đăng nhập
            </button>
          </p>
        </div>
      </div>
    </div>
  );
};

export default SignUp;
