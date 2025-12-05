import React, { useState, useEffect } from "react";
import { useParams, useNavigate } from "react-router-dom";
import "./detect-detail.css";
import { useGetDetectDetail } from "../../service/user/useDetectService";

// Simple encoding/decoding functions
const encodeId = (id) => {
  const SECRET = 12345;
  return (id ^ SECRET).toString(36);
};

const decodeId = (encoded) => {
  const SECRET = 12345;
  return parseInt(encoded, 36) ^ SECRET;
};

const DetectionDetail = () => {
  const { encodedId } = useParams();
  const navigate = useNavigate();
  const [detection, setDetection] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const getDetectDetail = useGetDetectDetail();

  console.log("Encoded ID from URL:", encodedId);

  useEffect(() => {
    const fetchDetection = async () => {
      try {
        setLoading(true);
        const detectId = decodeId(encodedId);

        console.log("Decoded Detection ID:", detectId);

        // Replace with your actual API endpoint
        const response = getDetectDetail(detectId);

        if (!response) {
          throw new Error("Detection not found");
        }

        const data = await response;
        setDetection(data);
      } catch (err) {
        setError(err.message);
      } finally {
        setLoading(false);
      }
    };

    fetchDetection();
  }, [encodedId]);

  const handleBack = () => {
    navigate(-1);
  };

  if (loading) {
    return (
      <div className="detection-detail">
        <div className="loading-spinner">
          <div className="spinner"></div>
          <p>Loading detection...</p>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="detection-detail">
        <div className="error-container">
          <h2>Error</h2>
          <p>{error}</p>
          <button onClick={handleBack} className="btn-back">
            Go Back
          </button>
        </div>
      </div>
    );
  }

  if (!detection) {
    return null;
  }

  return (
    <div className="detection-detail">
      <div className="detail-container">
        <button onClick={handleBack} className="btn-back">
          ← Back to Detections
        </button>

        <div className="detail-content">
          <div className="image-section">
            <img
              src={
                detection.imageUrl ||
                `data:${detection.image_mime_type};base64,${detection.image}`
              }
              alt="Detection"
              className="detection-image"
            />
            <div className="image-info">
              <span className="detection-date">
                {new Date(detection.created_at).toLocaleDateString("en-US", {
                  year: "numeric",
                  month: "long",
                  day: "numeric",
                  hour: "2-digit",
                  minute: "2-digit",
                })}
              </span>
            </div>
          </div>

          <div className="info-section">
            <div className="ingredients-block">
              <h2>Detected Ingredients</h2>
              {detection.detected_ingredients &&
              detection.detected_ingredients.length > 0 ? (
                <div className="ingredients-grid">
                  {detection.detected_ingredients.map((ingredient, index) => (
                    <div key={index} className="ingredient-tag">
                      {ingredient}
                    </div>
                  ))}
                </div>
              ) : (
                <p className="no-data">No ingredients detected</p>
              )}
            </div>

            <div className="recommendation-block">
              <h2>Recommendation</h2>
              {detection.recommendation ? (
                <div className="recommendation-content">
                  <p>{detection.recommendation}</p>
                </div>
              ) : (
                <p className="no-data">No recommendation available</p>
              )}
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

export { encodeId, decodeId };
export default DetectionDetail;
