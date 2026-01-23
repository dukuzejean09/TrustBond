const express = require("express");
const router = express.Router();
const { body, validationResult } = require("express-validator");
const jwt = require("jsonwebtoken");
const User = require("../models/User");

// Register new user (citizen)
router.post(
  "/register",
  [
    body("firstName").trim().notEmpty().withMessage("First name is required"),
    body("lastName").trim().notEmpty().withMessage("Last name is required"),
    body("phone").trim().notEmpty().withMessage("Phone number is required"),
    body("password")
      .isLength({ min: 6 })
      .withMessage("Password must be at least 6 characters"),
  ],
  async (req, res) => {
    try {
      const errors = validationResult(req);
      if (!errors.isEmpty()) {
        return res.status(400).json({ success: false, errors: errors.array() });
      }

      const { firstName, lastName, email, phone, password, district, sector } =
        req.body;

      // Check if user exists
      const existingUser = await User.findOne({ $or: [{ phone }, { email }] });
      if (existingUser) {
        return res.status(400).json({
          success: false,
          message: "User with this phone or email already exists",
        });
      }

      // Create user
      const user = await User.create({
        firstName,
        lastName,
        email,
        phone,
        password,
        district,
        sector,
        role: "citizen",
      });

      // Generate JWT
      const token = jwt.sign(
        { id: user._id, role: user.role },
        process.env.JWT_SECRET,
        { expiresIn: process.env.JWT_EXPIRES_IN },
      );

      res.status(201).json({
        success: true,
        message: "Registration successful",
        token,
        user: {
          id: user._id,
          firstName: user.firstName,
          lastName: user.lastName,
          phone: user.phone,
          role: user.role,
        },
      });
    } catch (error) {
      res.status(500).json({ success: false, message: error.message });
    }
  },
);

// Login
router.post(
  "/login",
  [
    body("phone").trim().notEmpty().withMessage("Phone number is required"),
    body("password").notEmpty().withMessage("Password is required"),
  ],
  async (req, res) => {
    try {
      const errors = validationResult(req);
      if (!errors.isEmpty()) {
        return res.status(400).json({ success: false, errors: errors.array() });
      }

      const { phone, password } = req.body;

      // Find user with password
      const user = await User.findOne({ phone }).select("+password");
      if (!user) {
        return res.status(401).json({
          success: false,
          message: "Invalid credentials",
        });
      }

      // Check if account is locked
      if (user.isLocked()) {
        return res.status(423).json({
          success: false,
          message: "Account is temporarily locked. Try again later.",
        });
      }

      // Verify password
      const isMatch = await user.comparePassword(password);
      if (!isMatch) {
        user.loginAttempts += 1;
        if (user.loginAttempts >= 5) {
          user.lockUntil = Date.now() + 30 * 60 * 1000; // Lock for 30 mins
        }
        await user.save();
        return res.status(401).json({
          success: false,
          message: "Invalid credentials",
        });
      }

      // Reset login attempts on successful login
      user.loginAttempts = 0;
      user.lockUntil = undefined;
      user.lastLogin = new Date();
      await user.save();

      // Generate JWT
      const token = jwt.sign(
        { id: user._id, role: user.role },
        process.env.JWT_SECRET,
        { expiresIn: process.env.JWT_EXPIRES_IN },
      );

      res.json({
        success: true,
        message: "Login successful",
        token,
        user: {
          id: user._id,
          firstName: user.firstName,
          lastName: user.lastName,
          phone: user.phone,
          email: user.email,
          role: user.role,
          station: user.station,
          rank: user.rank,
        },
      });
    } catch (error) {
      res.status(500).json({ success: false, message: error.message });
    }
  },
);

// Dashboard Login (for law enforcement)
router.post(
  "/dashboard/login",
  [
    body("email").isEmail().withMessage("Valid email is required"),
    body("password").notEmpty().withMessage("Password is required"),
  ],
  async (req, res) => {
    try {
      const errors = validationResult(req);
      if (!errors.isEmpty()) {
        return res.status(400).json({ success: false, errors: errors.array() });
      }

      const { email, password } = req.body;

      // Find law enforcement user
      const user = await User.findOne({
        email,
        role: { $in: ["officer", "supervisor", "admin", "super_admin"] },
      }).select("+password");

      if (!user) {
        return res.status(401).json({
          success: false,
          message: "Invalid credentials or unauthorized access",
        });
      }

      if (!user.isActive) {
        return res.status(403).json({
          success: false,
          message: "Account is deactivated. Contact administrator.",
        });
      }

      const isMatch = await user.comparePassword(password);
      if (!isMatch) {
        return res.status(401).json({
          success: false,
          message: "Invalid credentials",
        });
      }

      user.lastLogin = new Date();
      await user.save();

      const token = jwt.sign(
        { id: user._id, role: user.role, station: user.station },
        process.env.JWT_SECRET,
        { expiresIn: "12h" }, // Shorter expiry for dashboard
      );

      res.json({
        success: true,
        message: "Login successful",
        token,
        user: {
          id: user._id,
          firstName: user.firstName,
          lastName: user.lastName,
          email: user.email,
          role: user.role,
          station: user.station,
          rank: user.rank,
          badgeNumber: user.badgeNumber,
        },
      });
    } catch (error) {
      res.status(500).json({ success: false, message: error.message });
    }
  },
);

module.exports = router;
