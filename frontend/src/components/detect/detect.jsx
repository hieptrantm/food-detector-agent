import "./detect.css";
import { useEffect, useState } from "react";
import ImageUpload from "../imageUpload/imageUpload";
import { ChefHat } from "lucide-react";
import { useCreateDetect } from "../../service/user/useDetectService";
import toast from "react-hot-toast";

const Detect = ({ userId }) => {
  const [uploadedImage, setUploadedImage] = useState(null);
  const [backendInfo, setBackendInfo] = useState("");
  const [recommendation, setRecommendation] = useState("");
  const [detectedIngredients, setDetectedIngredients] = useState([]);
  const createDetect = useCreateDetect();

  const handleCookForMe = async () => {
    try {
      // const recommendation = await fetchRecommendation(detectedIngredients);
      // if (!recommendation) {
      //   toast.error("No recommendation received.");
      //   throw new Error("No recommendation received.");
      // }
      // setRecommendation(recommendation);
      const cleanBase64 = uploadedImage.replace(
        /^data:image\/[a-zA-Z]+;base64,/,
        ""
      );

      const data = {
        user_id: userId,
        image_base64: cleanBase64,
        image_mime_type: "image/jpeg",
        detected_ingredients: detectedIngredients,
        recommendation: recommendation,
      };
      const response = await createDetect(data);

      if (!response) {
        toast.error("Failed to save history.");
        throw new Error("Failed to save history.");
      }
      console.log("Detect saved:", response);
      toast.success("History saved successfully!");
    } catch (error) {
      toast.error("Failed to fetch recommendations.");
    }
  };

  useEffect(() => {
    if (detectedIngredients.length > 0) {
      const counts = detectedIngredients.reduce((acc, item) => {
        acc[item] = (acc[item] || 0) + 1;
        return acc;
      }, {});

      const info =
        "Detected ingredients: " +
        Object.entries(counts)
          .map(([key, value]) => `${key} (${value})`)
          .join(", ");
      console.log("detected ingredients: ", detectedIngredients);
      setBackendInfo(info);
    }
  }, [detectedIngredients]);

  return (
    <div className="detect">
      <ImageUpload
        userId={userId}
        image={uploadedImage}
        onImageChange={setUploadedImage}
        setDetectedIngredients={setDetectedIngredients}
      />

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

        <label className="recommendation-label">Recommendations</label>

        <textarea
          className="recommendation-field"
          value={recommendation}
          onChange={(e) => setRecommendation(e.target.value)}
          placeholder="Recommendations will appear here"
          readOnly
          rows={4}
        />
      </div>
    </div>
  );
};

export default Detect;
