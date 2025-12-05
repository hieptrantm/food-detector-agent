import "./detect.css";
import { useState } from "react";
import ImageUpload from "../imageUpload/imageUpload";
import { ChefHat } from "lucide-react";
import toast from "react-hot-toast";

const Detect = () => {
  const [uploadedImage, setUploadedImage] = useState(null);
  const [backendInfo, setBackendInfo] = useState("");
  const [recommendation, setRecommendation] = useState("");

  const handleCookForMe = () => {
    console.log("Cook something for me clicked!");
  };

  return (
    <div className="detect">
      <ImageUpload image={uploadedImage} onImageChange={setUploadedImage} />

      <div className="info-section">
        <div className="info-row">
          <textarea
            className="info-field"
            value={backendInfo}
            onChange={(e) => setBackendInfo(e.target.value)}
            placeholder="Backend info will display here"
            readOnly
            rows={3}
          />
          <button className="cook-button" onClick={handleCookForMe}>
            <ChefHat size={20} />
            <span className="cook-button-text">Cook something for me!</span>
          </button>
        </div>

        <label className="recommendation-label">Recommendation</label>

        <textarea
          className="recommendation-field"
          value={recommendation}
          onChange={(e) => setRecommendation(e.target.value)}
          placeholder="Recommendation will appear here"
          readOnly
          rows={4}
        />
      </div>
    </div>
  );
};

export default Detect;
