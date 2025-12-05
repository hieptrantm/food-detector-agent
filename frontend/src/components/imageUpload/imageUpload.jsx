"use client";

import { useState } from "react";
import { useUploadImageService } from "../../service/ai/useUpload";
import toast from "react-hot-toast";
import "../imageUpload/image.css";

const ImageUpload = ({ image, onImageChange }) => {
  const [selectedFile, setSelectedFile] = useState(null);
  const [isUploading, setIsUploading] = useState(false);
  const uploadImageService = useUploadImageService();

  const handleImageUpload = (e) => {
    const file = e.target.files[0];
    if (file) {
      // save selected file to state
      setSelectedFile(file);
      // use for preview
      const reader = new FileReader();
      reader.onloadend = () => {
        onImageChange(reader.result);
      };
      reader.readAsDataURL(file);
    }
  };
  const handleSendClick = async () => {
    if (!selectedFile) {
      toast.error("Please select an image first.");
      return;
    }
    try {
      setIsUploading(true);
      const result = await uploadImageService(selectedFile);
      console.log("Upload successful:", result);
      toast.success("Image uploaded successfully!");
    } catch (error) {
      console.error("Upload failed:", error);
      toast.error("Failed to upload image: " + error.message);
    } finally {
      setIsUploading(false);
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
      <label htmlFor="image-input" className="image-upload-area">
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
          onClick={handleSendClick}
          disabled={isUploading}
        >
          {isUploading ? "Uploading..." : "SEND"}
        </button>
      </div>
    </div>
  );
};

export default ImageUpload;
