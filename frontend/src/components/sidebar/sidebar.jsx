"use client";

import './sidebar.css';

const Sidebar = ({ isCollapsed, onToggle }) => {
  return (
    <div className={`sidebar ${isCollapsed ? 'collapsed' : ''}`}>
      <div className="sidebar-header">
      </div>
      <button className="collapse-btn" onClick={onToggle}>
        {isCollapsed ? '▶' : '◀'} Thu gọn
      </button>
    </div>
  );
};

export default Sidebar