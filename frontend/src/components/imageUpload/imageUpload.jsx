"use client";

import './image.css';

const ImageUpload = ({ image, onImageChange, onSend, isLoading }) => {
  const handleImageUpload = (e) => {
    const file = e.target.files[0];
    if (file) {
      const reader = new FileReader();
      reader.onloadend = () => {
        onImageChange(reader.result);
      };
      reader.readAsDataURL(file);
    }
  };

  const handleDragOver = (e) => {
    e.preventDefault();
    e.currentTarget.classList.add('drag-over');
  };

  const handleDragLeave = (e) => {
    e.currentTarget.classList.remove('drag-over');
  };

  const handleDrop = (e) => {
    e.preventDefault();
    e.currentTarget.classList.remove('drag-over');
    
    const file = e.dataTransfer.files[0];
    if (file && file.type.startsWith('image/')) {
      const reader = new FileReader();
      reader.onloadend = () => {
        onImageChange(reader.result);
      };
      reader.readAsDataURL(file);
    }
  };

  return (
    <div className="image-upload-container">
      <input
        type="file"
        accept="image/*"
        onChange={handleImageUpload}
        id="image-input"
        className="image-input"
      />
      <label 
        htmlFor="image-input" 
        className="image-upload-area"
        onDragOver={handleDragOver}
        onDragLeave={handleDragLeave}
        onDrop={handleDrop}
      >
        {image ? (
          <img src={image} alt="Uploaded" className="uploaded-image" />
        ) : (
          <div className="upload-placeholder">
            <p>INSERT OR TAKE AN IMAGE</p>
            <div className="upload-icons">
              <span className="upload-icon">📁</span>
              <span className="upload-icon">📷</span>
            </div>
          </div>
        )}
      </label>
      <div className="analyze-button-container">
        <button 
          className="analyze-btn" 
          onClick={onSend} 
          disabled={!image || isLoading}
        >
          {isLoading ? 'DETECTING...' : 'SEND'}
        </button>
      </div>
    </div>
  );
};

export default ImageUpload;