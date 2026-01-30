import React from "react";
import "../styles/Toast.css";

const Toast = ({ message, type = "success" }) => {
  const getIcon = () => {
    switch (type) {
      case "success":
        return "fa-check-circle";
      case "error":
        return "fa-exclamation-circle";
      case "info":
        return "fa-info-circle";
      default:
        return "fa-check-circle";
    }
  };

  return (
    <div className={`toast show ${type}`}>
      <i className={`fas ${getIcon()}`}></i>
      <span>{message}</span>
    </div>
  );
};

export default Toast;
