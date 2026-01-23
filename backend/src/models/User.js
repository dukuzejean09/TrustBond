const mongoose = require("mongoose");
const bcrypt = require("bcryptjs");

const userSchema = new mongoose.Schema(
  {
    // Basic Info
    firstName: { type: String, required: true },
    lastName: { type: String, required: true },
    email: { type: String, unique: true, sparse: true },
    phone: { type: String, required: true, unique: true },

    // Authentication
    password: { type: String, required: true, select: false },

    // Role-based access
    role: {
      type: String,
      enum: ["citizen", "officer", "supervisor", "admin", "super_admin"],
      default: "citizen",
    },

    // For Law Enforcement
    badgeNumber: { type: String },
    rank: { type: String },
    station: { type: String },
    department: { type: String },

    // Location (for citizens)
    district: { type: String },
    sector: { type: String },

    // Profile
    profilePhoto: { type: String },
    nationalId: { type: String },

    // Status
    isActive: { type: Boolean, default: true },
    isVerified: { type: Boolean, default: false },
    verifiedAt: { type: Date },
    verifiedBy: { type: mongoose.Schema.Types.ObjectId, ref: "User" },

    // Security
    lastLogin: { type: Date },
    loginAttempts: { type: Number, default: 0 },
    lockUntil: { type: Date },

    // Push notifications
    fcmToken: { type: String },
    notificationsEnabled: { type: Boolean, default: true },

    // Preferences
    language: { type: String, enum: ["en", "rw", "fr"], default: "en" },
  },
  { timestamps: true },
);

// Hash password before saving
userSchema.pre("save", async function (next) {
  if (!this.isModified("password")) return next();
  this.password = await bcrypt.hash(this.password, 12);
  next();
});

// Compare password method
userSchema.methods.comparePassword = async function (candidatePassword) {
  return await bcrypt.compare(candidatePassword, this.password);
};

// Check if account is locked
userSchema.methods.isLocked = function () {
  return this.lockUntil && this.lockUntil > Date.now();
};

// Get full name
userSchema.virtual("fullName").get(function () {
  return `${this.firstName} ${this.lastName}`;
});

module.exports = mongoose.model("User", userSchema);
