"use client";

import { useState } from "react";
import { useUploadImageService } from "../../service/ai/useUpload";
import toast from "react-hot-toast";
import "./image.css";

const ImageUpload = ({ image, onImageChange, setDetectedIngredients }) => {
  const [selectedFile, setSelectedFile] = useState(null);
  const [isUploading, setIsUploading] = useState(false);
  const [detections, setDetections] = useState([]);
  const uploadImageService = useUploadImageService();

  const handleImageUpload = (e) => {
    const file = e.target.files[0];
    if (file) {
      setDetections([]);
      setSelectedFile(file);
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

      // Store detections from server response
      if (result.detections) {
        setDetections(result.detections);
        const ingredients = result.detections.map((det) => det.label);
        setDetectedIngredients(ingredients);
      }

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
          <div className="image-container">
            <img src={image} alt="Uploaded" className="uploaded-image" />
            {/* Render bounding boxes */}
            {detections.map((detection, index) => {
              const [x1, y1, x2, y2] = detection.bbox;
              const width = x2 - x1;
              const height = y2 - y1;

              return (
                <div
                  key={index}
                  className="bounding-box"
                  style={{
                    left: `${x1}px`,
                    top: `${y1}px`,
                    width: `${width}px`,
                    height: `${height}px`,
                  }}
                >
                  <span className="detection-label">
                    {detection.label} ({Math.round(detection.confidence * 100)}
                    %)
                  </span>
                </div>
              );
            })}
          </div>
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
