import React from "react";
import "../styles/StatCard.css";

const StatCard = ({
  icon,
  iconColor,
  value,
  label,
  subtitle,
  change,
  changeType = "neutral",
  cardType = "default",
  onClick,
}) => {
  const getChangeIcon = () => {
    if (changeType === "positive") return "fa-arrow-up";
    if (changeType === "negative") return "fa-arrow-down";
    return "fa-minus";
  };

  return (
    <div className={`stat-card ${cardType}`} onClick={onClick}>
      <div className="stat-header">
        <div className={`stat-icon ${iconColor}`}>
          <i className={`fas ${icon}`}></i>
        </div>
        {change !== undefined && (
          <span className={`stat-change ${changeType}`}>
            <i className={`fas ${getChangeIcon()}`}></i>
            {Math.abs(change)}%
          </span>
        )}
      </div>
      <div className="stat-content">
        <h3>{typeof value === "number" ? value.toLocaleString() : value}</h3>
        <p>{label}</p>
        {subtitle && <span className="stat-subtitle">{subtitle}</span>}
      </div>
    </div>
  );
};

export default StatCard;
