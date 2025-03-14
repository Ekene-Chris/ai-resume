// frontend/src/pages/AnalysisStatus.jsx
import React, { useState, useEffect } from "react";
import { useParams, Link } from "react-router-dom";
import axios from "axios";

const AnalysisStatus = () => {
  const { analysisId } = useParams();
  const [analysis, setAnalysis] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => {
    const checkStatus = async () => {
      try {
        const response = await axios.get(`/api/cv/${analysisId}/status`);
        setAnalysis(response.data);

        // If still processing, poll again after 3 seconds
        if (response.data.status === "processing") {
          setTimeout(checkStatus, 3000);
        } else if (response.data.status === "failed") {
          // Stop polling if failed
          setError(
            `Analysis failed: ${response.data.error || "Unknown error"}`
          );
        }

        setLoading(false);
      } catch (err) {
        setError(
          `Error fetching analysis status: ${
            err.response?.data?.detail || err.message
          }`
        );
        setLoading(false);
      }
    };

    checkStatus();
  }, [analysisId]);

  if (loading) {
    return (
      <div className="max-w-md mx-auto mt-10 p-6 bg-white rounded-lg shadow-md">
        <div className="text-center">
          <h2 className="text-2xl font-bold text-gray-700 mb-4">
            Analyzing Resume...
          </h2>
          <div className="w-full bg-gray-200 rounded-full h-4 mb-4">
            <div
              className="bg-blue-600 h-4 rounded-full transition-all duration-500 ease-out"
              style={{ width: `${(analysis?.progress || 0) * 100}%` }}
            ></div>
          </div>
          <p className="text-gray-600">
            Estimated time remaining:{" "}
            {analysis?.estimated_time_remaining || "calculating..."} seconds
          </p>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="max-w-md mx-auto mt-10 p-6 bg-white rounded-lg shadow-md">
        <div className="text-center">
          <h2 className="text-2xl font-bold text-red-600 mb-4">
            Analysis Error
          </h2>
          <p className="mb-4 text-red-500">{error}</p>
          <div className="p-3 bg-red-50 border border-red-200 rounded mb-4">
            <p className="text-sm text-gray-700">
              There was an error processing your resume. This could be due to:
            </p>
            <ul className="text-sm text-gray-700 list-disc ml-5 mt-2">
              <li>
                File format issues (make sure it's a readable PDF or DOCX)
              </li>
              <li>Text extraction problems (avoid image-based PDFs)</li>
              <li>Service availability issues</li>
            </ul>
          </div>
          <Link
            to="/"
            className="px-4 py-2 bg-blue-600 text-white rounded hover:bg-blue-700 transition"
          >
            Try Again
          </Link>
        </div>
      </div>
    );
  }

  if (analysis?.status === "completed") {
    return (
      <div className="max-w-md mx-auto mt-10 p-6 bg-white rounded-lg shadow-md">
        <div className="text-center">
          <h2 className="text-2xl font-bold text-green-600 mb-4">
            Analysis Complete!
          </h2>
          <p className="mb-4">Your resume analysis is ready to view.</p>
          <Link
            to={`/analysis/${analysisId}/results`}
            className="px-4 py-2 bg-blue-600 text-white rounded hover:bg-blue-700 transition"
          >
            View Results
          </Link>
        </div>
      </div>
    );
  }

  if (analysis?.status === "failed") {
    return (
      <div className="max-w-md mx-auto mt-10 p-6 bg-white rounded-lg shadow-md">
        <div className="text-center">
          <h2 className="text-2xl font-bold text-red-600 mb-4">
            Analysis Failed
          </h2>
          <p className="mb-4 text-red-500">
            {analysis.error || "An unknown error occurred during analysis."}
          </p>
          <div className="p-3 bg-red-50 border border-red-200 rounded mb-4">
            <p className="text-sm text-gray-700">
              There was an error analyzing your resume. This could be due to:
            </p>
            <ul className="text-sm text-gray-700 list-disc ml-5 mt-2">
              <li>
                File format issues (make sure it's a readable PDF or DOCX)
              </li>
              <li>Text extraction problems (avoid image-based PDFs)</li>
              <li>Service availability issues</li>
            </ul>
          </div>
          <Link
            to="/"
            className="px-4 py-2 bg-blue-600 text-white rounded hover:bg-blue-700 transition"
          >
            Try Again
          </Link>
        </div>
      </div>
    );
  }

  return (
    <div className="max-w-md mx-auto mt-10 p-6 bg-white rounded-lg shadow-md">
      <div className="text-center">
        <h2 className="text-2xl font-bold text-gray-700 mb-4">Processing...</h2>
        <p className="mb-4">Status: {analysis?.status || "Unknown"}</p>
        <Link
          to="/"
          className="px-4 py-2 bg-gray-500 text-white rounded hover:bg-gray-600 transition"
        >
          Back to Upload
        </Link>
      </div>
    </div>
  );
};

export default AnalysisStatus;
