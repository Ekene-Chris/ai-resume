// frontend/src/components/ResumeUpload.jsx
import React, { useState } from "react";
import axios from "axios";

const ResumeUpload = () => {
  const [name, setName] = useState("");
  const [email, setEmail] = useState("");
  const [file, setFile] = useState(null);
  const [targetRole, setTargetRole] = useState("devops_engineer");
  const [experienceLevel, setExperienceLevel] = useState("mid");
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState("");
  const [success, setSuccess] = useState(false);
  const [analysisId, setAnalysisId] = useState("");

  const roles = [
    { id: "devops_engineer", name: "DevOps Engineer" },
    { id: "cloud_architect", name: "Cloud Architect" },
    { id: "backend_developer", name: "Backend Developer" },
    { id: "frontend_developer", name: "Frontend Developer" },
  ];

  const experienceLevels = [
    { id: "junior", name: "Junior (0-2 years)" },
    { id: "mid", name: "Mid-Level (3-5 years)" },
    { id: "senior", name: "Senior (6+ years)" },
  ];

  const handleFileChange = (e) => {
    const selectedFile = e.target.files[0];
    setFile(selectedFile);
  };

  const handleSubmit = async (e) => {
    e.preventDefault();

    if (!name || !email || !file) {
      setError("Please fill in all required fields");
      return;
    }

    setIsLoading(true);
    setError("");

    try {
      // Create form data
      const formData = new FormData();
      formData.append("name", name);
      formData.append("email", email);
      formData.append("file", file);
      formData.append("target_role", targetRole);
      formData.append("experience_level", experienceLevel);

      // Send to backend
      const response = await axios.post("/api/cv/upload", formData, {
        headers: {
          "Content-Type": "multipart/form-data",
        },
      });

      setAnalysisId(response.data.analysis_id);
      setSuccess(true);
    } catch (err) {
      setError(`Upload failed: ${err.response?.data?.detail || err.message}`);
    } finally {
      setIsLoading(false);
    }
  };

  if (success) {
    return (
      <div className="max-w-md mx-auto mt-10 p-6 bg-white rounded-lg shadow-md">
        <div className="text-center">
          <h2 className="text-2xl font-bold text-green-600 mb-4">
            Resume Uploaded Successfully!
          </h2>
          <p className="mb-4">
            We're analyzing your resume now. You'll receive the results at{" "}
            {email} shortly.
          </p>
          <p className="text-sm text-gray-500 mb-4">
            Analysis ID: {analysisId}
          </p>
          <button
            onClick={() => setSuccess(false)}
            className="px-4 py-2 bg-blue-600 text-white rounded hover:bg-blue-700 transition"
          >
            Submit Another Resume
          </button>
        </div>
      </div>
    );
  }

  return (
    <div className="max-w-md mx-auto mt-10 p-6 bg-white rounded-lg shadow-md">
      <h2 className="text-2xl font-bold text-center mb-6">
        AI Resume Analyzer
      </h2>

      {error && (
        <div className="mb-4 p-3 bg-red-100 text-red-700 rounded">{error}</div>
      )}

      <form onSubmit={handleSubmit}>
        <div className="mb-4">
          <label
            htmlFor="name"
            className="block text-gray-700 font-medium mb-2"
          >
            Full Name *
          </label>
          <input
            type="text"
            id="name"
            value={name}
            onChange={(e) => setName(e.target.value)}
            className="w-full px-3 py-2 border border-gray-300 rounded focus:outline-none focus:ring-2 focus:ring-blue-500"
            required
          />
        </div>

        <div className="mb-4">
          <label
            htmlFor="email"
            className="block text-gray-700 font-medium mb-2"
          >
            Email Address *
          </label>
          <input
            type="email"
            id="email"
            value={email}
            onChange={(e) => setEmail(e.target.value)}
            className="w-full px-3 py-2 border border-gray-300 rounded focus:outline-none focus:ring-2 focus:ring-blue-500"
            required
          />
        </div>

        <div className="mb-4">
          <label
            htmlFor="targetRole"
            className="block text-gray-700 font-medium mb-2"
          >
            Target Role
          </label>
          <select
            id="targetRole"
            value={targetRole}
            onChange={(e) => setTargetRole(e.target.value)}
            className="w-full px-3 py-2 border border-gray-300 rounded focus:outline-none focus:ring-2 focus:ring-blue-500"
          >
            {roles.map((role) => (
              <option key={role.id} value={role.id}>
                {role.name}
              </option>
            ))}
          </select>
        </div>

        <div className="mb-4">
          <label
            htmlFor="experienceLevel"
            className="block text-gray-700 font-medium mb-2"
          >
            Experience Level
          </label>
          <select
            id="experienceLevel"
            value={experienceLevel}
            onChange={(e) => setExperienceLevel(e.target.value)}
            className="w-full px-3 py-2 border border-gray-300 rounded focus:outline-none focus:ring-2 focus:ring-blue-500"
          >
            {experienceLevels.map((level) => (
              <option key={level.id} value={level.id}>
                {level.name}
              </option>
            ))}
          </select>
        </div>

        <div className="mb-6">
          <label
            htmlFor="resume"
            className="block text-gray-700 font-medium mb-2"
          >
            Upload Resume (PDF, DOCX) *
          </label>
          <input
            type="file"
            id="resume"
            onChange={handleFileChange}
            className="w-full px-3 py-2 border border-gray-300 rounded focus:outline-none focus:ring-2 focus:ring-blue-500"
            accept=".pdf,.docx,.doc"
            required
          />
          <p className="mt-1 text-xs text-gray-500">Max file size: 10MB</p>
        </div>

        <button
          type="submit"
          disabled={isLoading}
          className={`w-full py-2 px-4 rounded font-medium ${
            isLoading
              ? "bg-gray-400 cursor-not-allowed"
              : "bg-blue-600 hover:bg-blue-700 text-white transition"
          }`}
        >
          {isLoading ? "Uploading..." : "Analyze Resume"}
        </button>
      </form>
    </div>
  );
};

export default ResumeUpload;
