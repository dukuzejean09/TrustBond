const express = require("express");
const router = express.Router();
const multer = require("multer");
const path = require("path");
const { body, validationResult } = require("express-validator");
const Report = require("../models/Report");
const auth = require("../middleware/auth");

// Configure multer for file uploads
const storage = multer.diskStorage({
  destination: (req, file, cb) => {
    cb(null, "uploads/evidence/");
  },
  filename: (req, file, cb) => {
    const uniqueSuffix = Date.now() + "-" + Math.round(Math.random() * 1e9);
    cb(null, uniqueSuffix + path.extname(file.originalname));
  },
});

const upload = multer({
  storage,
  limits: { fileSize: 50 * 1024 * 1024 }, // 50MB
  fileFilter: (req, file, cb) => {
    const allowedTypes = /jpeg|jpg|png|gif|mp4|mov|avi|mp3|wav|pdf/;
    const extname = allowedTypes.test(
      path.extname(file.originalname).toLowerCase(),
    );
    const mimetype = allowedTypes.test(file.mimetype);
    if (mimetype && extname) {
      return cb(null, true);
    }
    cb(new Error("Invalid file type"));
  },
});

// Submit a new report
router.post(
  "/",
  [
    body("incidentType").notEmpty().withMessage("Incident type is required"),
    body("description")
      .isLength({ min: 10 })
      .withMessage("Description must be at least 10 characters"),
    body("location.latitude")
      .isNumeric()
      .withMessage("Valid latitude is required"),
    body("location.longitude")
      .isNumeric()
      .withMessage("Valid longitude is required"),
    body("incidentDate").isISO8601().withMessage("Valid date is required"),
  ],
  async (req, res) => {
    try {
      const errors = validationResult(req);
      if (!errors.isEmpty()) {
        return res.status(400).json({ success: false, errors: errors.array() });
      }

      const reportData = {
        ...req.body,
        status: "submitted",
        submittedAt: new Date(),
      };

      // If not anonymous and user is authenticated
      if (!req.body.isAnonymous && req.user) {
        reportData.reporter = req.user.id;
      }

      const report = await Report.create(reportData);

      res.status(201).json({
        success: true,
        message: "Report submitted successfully",
        data: {
          reportId: report.reportId,
          status: report.status,
          submittedAt: report.submittedAt,
        },
      });
    } catch (error) {
      res.status(500).json({ success: false, message: error.message });
    }
  },
);

// Upload evidence
router.post(
  "/:reportId/evidence",
  upload.array("files", 10),
  async (req, res) => {
    try {
      const report = await Report.findOne({ reportId: req.params.reportId });
      if (!report) {
        return res
          .status(404)
          .json({ success: false, message: "Report not found" });
      }

      const evidence = req.files.map((file) => ({
        type: file.mimetype.startsWith("image")
          ? "photo"
          : file.mimetype.startsWith("video")
            ? "video"
            : file.mimetype.startsWith("audio")
              ? "audio"
              : "document",
        url: `/uploads/evidence/${file.filename}`,
        filename: file.originalname,
      }));

      report.evidence.push(...evidence);
      await report.save();

      res.json({
        success: true,
        message: "Evidence uploaded successfully",
        data: evidence,
      });
    } catch (error) {
      res.status(500).json({ success: false, message: error.message });
    }
  },
);

// Get user's reports
router.get("/my-reports", auth, async (req, res) => {
  try {
    const reports = await Report.find({ reporter: req.user.id })
      .sort({ createdAt: -1 })
      .select("reportId incidentType status submittedAt location.address");

    res.json({
      success: true,
      count: reports.length,
      data: reports,
    });
  } catch (error) {
    res.status(500).json({ success: false, message: error.message });
  }
});

// Get report by ID
router.get("/:reportId", async (req, res) => {
  try {
    const report = await Report.findOne({ reportId: req.params.reportId })
      .populate("assignedOfficer", "firstName lastName rank station")
      .populate("statusHistory.changedBy", "firstName lastName");

    if (!report) {
      return res
        .status(404)
        .json({ success: false, message: "Report not found" });
    }

    res.json({
      success: true,
      data: report,
    });
  } catch (error) {
    res.status(500).json({ success: false, message: error.message });
  }
});

// Track report status (public - by report ID)
router.get("/track/:reportId", async (req, res) => {
  try {
    const report = await Report.findOne({
      reportId: req.params.reportId,
    }).select(
      "reportId status statusHistory incidentType submittedAt updatedAt",
    );

    if (!report) {
      return res
        .status(404)
        .json({ success: false, message: "Report not found" });
    }

    res.json({
      success: true,
      data: {
        reportId: report.reportId,
        status: report.status,
        incidentType: report.incidentType,
        submittedAt: report.submittedAt,
        lastUpdated: report.updatedAt,
        timeline: report.statusHistory,
      },
    });
  } catch (error) {
    res.status(500).json({ success: false, message: error.message });
  }
});

module.exports = router;
