const express = require("express");
const router = express.Router();
const mongoose = require("mongoose");
const auth = require("../middleware/auth");
const authorize = require("../middleware/authorize");

// Alert Schema
const alertSchema = new mongoose.Schema({
  title: { type: String, required: true },
  message: { type: String, required: true },
  type: {
    type: String,
    enum: ["emergency", "warning", "info", "safety_tip"],
    default: "info",
  },
  priority: {
    type: String,
    enum: ["high", "medium", "low"],
    default: "medium",
  },
  targetAreas: [
    {
      district: String,
      sector: String,
    },
  ],
  isActive: { type: Boolean, default: true },
  expiresAt: Date,
  createdBy: { type: mongoose.Schema.Types.ObjectId, ref: "User" },
  createdAt: { type: Date, default: Date.now },
  viewCount: { type: Number, default: 0 },
});

const Alert = mongoose.model("Alert", alertSchema);

// Get active alerts (public)
router.get("/", async (req, res) => {
  try {
    const { district, type, limit = 10 } = req.query;

    const filter = {
      isActive: true,
      $or: [{ expiresAt: null }, { expiresAt: { $gt: new Date() } }],
    };

    if (type) filter.type = type;
    if (district) {
      filter.$or = [
        { targetAreas: { $size: 0 } }, // Nationwide alerts
        { "targetAreas.district": district },
      ];
    }

    const alerts = await Alert.find(filter)
      .sort({ priority: -1, createdAt: -1 })
      .limit(parseInt(limit))
      .select("-viewCount -createdBy");

    res.json({
      success: true,
      count: alerts.length,
      data: alerts,
    });
  } catch (error) {
    res.status(500).json({ success: false, message: error.message });
  }
});

// Get alert by ID
router.get("/:id", async (req, res) => {
  try {
    const alert = await Alert.findById(req.params.id);

    if (!alert) {
      return res
        .status(404)
        .json({ success: false, message: "Alert not found" });
    }

    // Increment view count
    alert.viewCount += 1;
    await alert.save();

    res.json({
      success: true,
      data: alert,
    });
  } catch (error) {
    res.status(500).json({ success: false, message: error.message });
  }
});

// Create alert (admin only)
router.post(
  "/",
  [auth, authorize("admin", "super_admin")],
  async (req, res) => {
    try {
      const { title, message, type, priority, targetAreas, expiresAt } =
        req.body;

      const alert = await Alert.create({
        title,
        message,
        type,
        priority,
        targetAreas: targetAreas || [],
        expiresAt,
        createdBy: req.user.id,
      });

      res.status(201).json({
        success: true,
        message: "Alert created successfully",
        data: alert,
      });
    } catch (error) {
      res.status(500).json({ success: false, message: error.message });
    }
  },
);

// Update alert
router.patch(
  "/:id",
  [auth, authorize("admin", "super_admin")],
  async (req, res) => {
    try {
      const {
        title,
        message,
        type,
        priority,
        targetAreas,
        expiresAt,
        isActive,
      } = req.body;

      const alert = await Alert.findByIdAndUpdate(
        req.params.id,
        { title, message, type, priority, targetAreas, expiresAt, isActive },
        { new: true, runValidators: true },
      );

      if (!alert) {
        return res
          .status(404)
          .json({ success: false, message: "Alert not found" });
      }

      res.json({
        success: true,
        message: "Alert updated successfully",
        data: alert,
      });
    } catch (error) {
      res.status(500).json({ success: false, message: error.message });
    }
  },
);

// Delete alert
router.delete(
  "/:id",
  [auth, authorize("admin", "super_admin")],
  async (req, res) => {
    try {
      const alert = await Alert.findByIdAndDelete(req.params.id);

      if (!alert) {
        return res
          .status(404)
          .json({ success: false, message: "Alert not found" });
      }

      res.json({
        success: true,
        message: "Alert deleted successfully",
      });
    } catch (error) {
      res.status(500).json({ success: false, message: error.message });
    }
  },
);

module.exports = router;
