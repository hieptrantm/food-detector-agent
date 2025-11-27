import "./detect.css";
import { useState } from "react";
import ImageUpload from "../imageUpload/imageUpload";

const Detect = () => {
  const [uploadedImage, setUploadedImage] = useState(null);

  return (
    <div className="detect">
      <ImageUpload image={uploadedImage} onImageChange={setUploadedImage} />
      <div></div>
    </div>
  );
};

export default Detect;
