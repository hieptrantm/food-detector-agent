"use client";

import "./sidebar.css";
import { X } from "lucide-react";

const Sidebar = ({ sidebarOpen, setSidebarOpen }) => {
  return (
    <div className={`sidebar ${sidebarOpen ? "open" : "closed"}`}>
      <div className="sidebar-content">
        <div className="sidebar-header">
          <h2 className="sidebar-title">Calendar Menu</h2>
          <button
            onClick={() => setSidebarOpen(false)}
            className="close-button"
          >
            <X size={24} />
          </button>
        </div>
        <div className="sidebar-body">
          <div className="sidebar-date">April 12, 2024 — 3:47 PM</div>
        </div>
      </div>
    </div>
  );
};

export default Sidebar;
