import React, { useState } from "react";
import { useDropzone } from "react-dropzone";
import axios from "axios";
import "./ReceiptUploader.css";

// Dynamic API base URL - works in both development and production
const API_BASE_URL = process.env.NODE_ENV === 'production' 
  ? '' // Use relative path in production (same domain as frontend)
  : 'http://127.0.0.1:5000'; // Use localhost in development

const ReceiptUploader = () => {
  const [isAnalyzing, setIsAnalyzing] = useState(false);
  const [results, setResults] = useState(null);
  const [error, setError] = useState(null);

  // Handle file upload to Flask backend
  const uploadFile = async (file) => {
    setIsAnalyzing(true);
    setError(null);

    const formData = new FormData();
    formData.append("file", file);

    try {
      const response = await axios.post(
        `${API_BASE_URL}/analyze-receipt`,
        formData,
        {
          headers: {
            "Content-Type": "multipart/form-data",
          },
        }
      );

      setResults(response.data);
    } catch (err) {
      setError(err.response?.data?.error || "Failed to analyze receipt");
    } finally {
      setIsAnalyzing(false);
    }
  };

  // Configure dropzone
  const { getRootProps, getInputProps, isDragActive } = useDropzone({
    accept: {
      "image/*": [".jpeg", ".jpg", ".png", ".gif", ".bmp", ".tiff"],
    },
    maxFiles: 1,
    onDrop: (acceptedFiles) => {
      if (acceptedFiles.length > 0) {
        uploadFile(acceptedFiles[0]);
      }
    },
  });

  const downloadResults = () => {
    const dataString = JSON.stringify(results, null, 2);
    const dataBlob = new Blob([dataString], { type: "application/json" });
    const url = URL.createObjectURL(dataBlob);
    const link = document.createElement("a");
    link.href = url;
    link.download = `receipt-analysis-${Date.now()}.json`;
    link.click();
    URL.revokeObjectURL(url);
  };

  return (
    <div className="receipt-uploader">
      <h1>AI Receipt Analyzer</h1>

      {/* Dropzone Area */}
      <div
        {...getRootProps()}
        className={`dropzone ${isDragActive ? "active" : ""}`}
      >
        <input {...getInputProps()} />
        {isAnalyzing ? (
          <div className="analyzing">
            <div className="spinner"></div>
            <p>Analyzing receipt...</p>
          </div>
        ) : (
          <div className="upload-prompt">
            <p>📄 Drop your receipt here, or click to select</p>
            <small>Supports: JPG, PNG, GIF, BMP, TIFF</small>
          </div>
        )}
      </div>

      {/* Error Display */}
      {error && (
        <div className="error">
          <p>❌ Error: {error}</p>
        </div>
      )}

      {/* Results Display */}
      {results && results.success && (
        <div className="results">
          <h2>📊 Analysis Results</h2>
          {results && results.success && (
            <div className="results">
              <h2>📊 Analysis Results</h2>
              <button className="download-btn" onClick={downloadResults}>
                💾 Download Results
              </button>
              {/* Your existing results display code stays here */}
            </div>
          )}
          {results.data.map((receipt, index) => (
            <div key={index} className="receipt-data">
              {/* Basic Info */}
              <div className="info-section">
                <h3>🏪 Merchant Information</h3>
                <div className="info-row">
                  <strong>Name:</strong> {receipt.merchant_name || "Not found"}
                  {receipt.merchant_confidence && (
                    <span className="confidence">
                      ({Math.round(receipt.merchant_confidence * 100)}%
                      confident)
                    </span>
                  )}
                </div>
                <div className="info-row">
                  <strong>Address:</strong>{" "}
                  {receipt.merchant_address || "Not found"}
                </div>
                <div className="info-row">
                  <strong>Phone:</strong>{" "}
                  {receipt.merchant_phone || "Not found"}
                </div>
              </div>

              {/* Transaction Details */}
              <div className="info-section">
                <h3>💰 Transaction Details</h3>
                <div className="info-row">
                  <strong>Date:</strong>{" "}
                  {receipt.transaction_date || "Not found"}
                </div>
                <div className="info-row">
                  <strong>Time:</strong>{" "}
                  {receipt.transaction_time || "Not found"}
                </div>
                <div className="info-row total">
                  <strong>Total:</strong> ${receipt.total || "Not found"}
                  {receipt.total_confidence && (
                    <span className="confidence">
                      ({Math.round(receipt.total_confidence * 100)}% confident)
                    </span>
                  )}
                </div>
                <div className="info-row">
                  <strong>Subtotal:</strong> ${receipt.subtotal || "Not found"}
                </div>
                <div className="info-row">
                  <strong>Tax:</strong> ${receipt.tax || "Not found"}
                </div>
              </div>

              {/* Items List */}
              {receipt.items && receipt.items.length > 0 && (
                <div className="info-section">
                  <h3>🛍️ Items ({receipt.items.length})</h3>
                  <div className="items-list">
                    {receipt.items.map((item, itemIndex) => (
                      <div key={itemIndex} className="item-row">
                        <div className="item-description">
                          {item.description || `Item ${itemIndex + 1}`}
                        </div>
                        <div className="item-details">
                          {item.quantity && <span>Qty: {item.quantity}</span>}
                          {item.price && <span>@ ${item.price}</span>}
                          {item.total_price && (
                            <span className="item-total">
                              ${item.total_price}
                            </span>
                          )}
                        </div>
                      </div>
                    ))}
                  </div>
                </div>
              )}
            </div>
          ))}
        </div>
      )}
    </div>
  );
};

export default ReceiptUploader;
