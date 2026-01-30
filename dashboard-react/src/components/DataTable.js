import React from "react";
import "../styles/DataTable.css";

const DataTable = ({
  columns,
  data,
  loading,
  emptyMessage = "No data found",
  onRowClick,
}) => {
  if (loading) {
    return (
      <table className="data-table">
        <thead>
          <tr>
            {columns.map((col, index) => (
              <th key={index}>{col.header}</th>
            ))}
          </tr>
        </thead>
        <tbody>
          <tr>
            <td colSpan={columns.length} className="loading">
              Loading...
            </td>
          </tr>
        </tbody>
      </table>
    );
  }

  if (!data || data.length === 0) {
    return (
      <table className="data-table">
        <thead>
          <tr>
            {columns.map((col, index) => (
              <th key={index}>{col.header}</th>
            ))}
          </tr>
        </thead>
        <tbody>
          <tr>
            <td colSpan={columns.length} className="loading">
              {emptyMessage}
            </td>
          </tr>
        </tbody>
      </table>
    );
  }

  return (
    <table className="data-table">
      <thead>
        <tr>
          {columns.map((col, index) => (
            <th key={index}>{col.header}</th>
          ))}
        </tr>
      </thead>
      <tbody>
        {data.map((row, rowIndex) => (
          <tr
            key={rowIndex}
            onClick={() => onRowClick && onRowClick(row)}
            style={{ cursor: onRowClick ? "pointer" : "default" }}
          >
            {columns.map((col, colIndex) => (
              <td key={colIndex}>
                {col.render ? col.render(row) : row[col.accessor]}
              </td>
            ))}
          </tr>
        ))}
      </tbody>
    </table>
  );
};

export default DataTable;
