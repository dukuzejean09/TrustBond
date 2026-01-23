const express = require("express");
const cors = require("cors");
const helmet = require("helmet");
const rateLimit = require("express-rate-limit");
require("dotenv").config();

const connectDB = require("./config/database");
const authRoutes = require("./routes/auth.routes");
const reportRoutes = require("./routes/report.routes");
const userRoutes = require("./routes/user.routes");
const alertRoutes = require("./routes/alert.routes");
const dashboardRoutes = require("./routes/dashboard.routes");

// Connect to MongoDB
connectDB();

const app = express();

// Security middleware
app.use(helmet());
app.use(
  cors({
    origin: [
      "http://localhost:3000", // Dashboard
      "http://localhost:8080", // Mobile web
      process.env.DASHBOARD_URL,
      process.env.MOBILE_URL,
    ],
    credentials: true,
  }),
);

// Rate limiting
const limiter = rateLimit({
  windowMs: 15 * 60 * 1000, // 15 minutes
  max: 100, // limit each IP to 100 requests per windowMs
});
app.use(limiter);

// Body parsing
app.use(express.json({ limit: "50mb" }));
app.use(express.urlencoded({ extended: true, limit: "50mb" }));

// Static files for uploads
app.use("/uploads", express.static("uploads"));

// API Routes
app.use("/api/auth", authRoutes);
app.use("/api/reports", reportRoutes);
app.use("/api/users", userRoutes);
app.use("/api/alerts", alertRoutes);
app.use("/api/dashboard", dashboardRoutes);

// Health check
app.get("/api/health", (req, res) => {
  res.json({
    status: "OK",
    message: "TrustBond API is running",
    timestamp: new Date().toISOString(),
  });
});

// Error handling middleware
app.use((err, req, res, next) => {
  console.error(err.stack);
  res.status(500).json({
    success: false,
    message: "Something went wrong!",
    error: process.env.NODE_ENV === "development" ? err.message : undefined,
  });
});

// 404 handler
app.use((req, res) => {
  res.status(404).json({
    success: false,
    message: "Route not found",
  });
});

const PORT = process.env.PORT || 5000;

app.listen(PORT, () => {
  console.log(`
  ╔═══════════════════════════════════════════════╗
  ║     TrustBond API Server                      ║
  ║     Rwanda National Police                    ║
  ╠═══════════════════════════════════════════════╣
  ║  Status:  Running                             ║
  ║  Port:    ${PORT}                                ║
  ║  Mode:    ${process.env.NODE_ENV || "development"}                        ║
  ╚═══════════════════════════════════════════════╝
  `);
});

module.exports = app;
