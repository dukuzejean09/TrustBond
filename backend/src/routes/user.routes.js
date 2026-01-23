const express = require("express");
const router = express.Router();
const User = require("../models/User");
const auth = require("../middleware/auth");
const authorize = require("../middleware/authorize");

// Get all users (admin only)
router.get("/", [auth, authorize("admin", "super_admin")], async (req, res) => {
  try {
    const { role, station, isActive, page = 1, limit = 20 } = req.query;

    const filter = {};
    if (role) filter.role = role;
    if (station) filter.station = station;
    if (isActive !== undefined) filter.isActive = isActive === "true";

    const skip = (page - 1) * limit;

    const [users, total] = await Promise.all([
      User.find(filter)
        .select("-password")
        .sort({ createdAt: -1 })
        .skip(skip)
        .limit(parseInt(limit)),
      User.countDocuments(filter),
    ]);

    res.json({
      success: true,
      data: users,
      pagination: {
        current: parseInt(page),
        pages: Math.ceil(total / limit),
        total,
      },
    });
  } catch (error) {
    res.status(500).json({ success: false, message: error.message });
  }
});

// Get user by ID
router.get(
  "/:id",
  [auth, authorize("admin", "super_admin")],
  async (req, res) => {
    try {
      const user = await User.findById(req.params.id).select("-password");

      if (!user) {
        return res
          .status(404)
          .json({ success: false, message: "User not found" });
      }

      res.json({
        success: true,
        data: user,
      });
    } catch (error) {
      res.status(500).json({ success: false, message: error.message });
    }
  },
);

// Create officer account (admin only)
router.post(
  "/officer",
  [auth, authorize("admin", "super_admin")],
  async (req, res) => {
    try {
      const {
        firstName,
        lastName,
        email,
        phone,
        password,
        rank,
        badgeNumber,
        station,
        department,
      } = req.body;

      // Check if badge number already exists
      const existingBadge = await User.findOne({ badgeNumber });
      if (existingBadge) {
        return res
          .status(400)
          .json({ success: false, message: "Badge number already registered" });
      }

      // Check if email already exists
      const existingEmail = await User.findOne({ email });
      if (existingEmail) {
        return res
          .status(400)
          .json({ success: false, message: "Email already registered" });
      }

      const officer = await User.create({
        firstName,
        lastName,
        email,
        phone,
        password,
        role: "officer",
        rank,
        badgeNumber,
        station,
        department,
      });

      res.status(201).json({
        success: true,
        message: "Officer account created successfully",
        data: {
          id: officer._id,
          firstName: officer.firstName,
          lastName: officer.lastName,
          badgeNumber: officer.badgeNumber,
          rank: officer.rank,
          station: officer.station,
        },
      });
    } catch (error) {
      res.status(500).json({ success: false, message: error.message });
    }
  },
);

// Update user role
router.patch(
  "/:id/role",
  [auth, authorize("super_admin")],
  async (req, res) => {
    try {
      const { role } = req.body;
      const validRoles = ["citizen", "officer", "supervisor", "admin"];

      if (!validRoles.includes(role)) {
        return res
          .status(400)
          .json({ success: false, message: "Invalid role" });
      }

      const user = await User.findByIdAndUpdate(
        req.params.id,
        { role },
        { new: true },
      ).select("-password");

      if (!user) {
        return res
          .status(404)
          .json({ success: false, message: "User not found" });
      }

      res.json({
        success: true,
        message: "User role updated",
        data: user,
      });
    } catch (error) {
      res.status(500).json({ success: false, message: error.message });
    }
  },
);

// Activate/Deactivate user
router.patch(
  "/:id/status",
  [auth, authorize("admin", "super_admin")],
  async (req, res) => {
    try {
      const { isActive } = req.body;

      const user = await User.findByIdAndUpdate(
        req.params.id,
        { isActive },
        { new: true },
      ).select("-password");

      if (!user) {
        return res
          .status(404)
          .json({ success: false, message: "User not found" });
      }

      res.json({
        success: true,
        message: `User ${isActive ? "activated" : "deactivated"} successfully`,
        data: user,
      });
    } catch (error) {
      res.status(500).json({ success: false, message: error.message });
    }
  },
);

// Update user profile (self)
router.patch("/profile/me", auth, async (req, res) => {
  try {
    const { firstName, lastName, phone, address } = req.body;

    const user = await User.findByIdAndUpdate(
      req.user.id,
      { firstName, lastName, phone, address },
      { new: true },
    ).select("-password");

    res.json({
      success: true,
      message: "Profile updated successfully",
      data: user,
    });
  } catch (error) {
    res.status(500).json({ success: false, message: error.message });
  }
});

// Get current user profile
router.get("/profile/me", auth, async (req, res) => {
  try {
    const user = await User.findById(req.user.id).select("-password");

    res.json({
      success: true,
      data: user,
    });
  } catch (error) {
    res.status(500).json({ success: false, message: error.message });
  }
});

// Delete user (super_admin only)
router.delete("/:id", [auth, authorize("super_admin")], async (req, res) => {
  try {
    const user = await User.findByIdAndDelete(req.params.id);

    if (!user) {
      return res
        .status(404)
        .json({ success: false, message: "User not found" });
    }

    res.json({
      success: true,
      message: "User deleted successfully",
    });
  } catch (error) {
    res.status(500).json({ success: false, message: error.message });
  }
});

module.exports = router;
