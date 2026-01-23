const mongoose = require("mongoose");

const reportSchema = new mongoose.Schema(
  {
    // Report Identification
    reportId: {
      type: String,
      unique: true,
      required: true,
    },

    // Incident Details
    incidentType: {
      type: String,
      required: true,
      enum: [
        "theft",
        "robbery",
        "assault",
        "burglary",
        "vandalism",
        "fraud",
        "domestic_violence",
        "traffic_accident",
        "drug_related",
        "cybercrime",
        "missing_person",
        "suspicious_activity",
        "public_disturbance",
        "other",
      ],
    },

    description: {
      type: String,
      required: true,
      minlength: 10,
      maxlength: 5000,
    },

    // Location
    location: {
      latitude: { type: Number, required: true },
      longitude: { type: Number, required: true },
      address: { type: String },
      district: { type: String },
      sector: { type: String },
      cell: { type: String },
      village: { type: String },
    },

    // Time of Incident
    incidentDate: { type: Date, required: true },
    incidentTime: { type: String },

    // Reporter Information
    isAnonymous: { type: Boolean, default: false },
    reporter: {
      type: mongoose.Schema.Types.ObjectId,
      ref: "User",
      required: function () {
        return !this.isAnonymous;
      },
    },
    reporterPhone: { type: String }, // For anonymous contact

    // Evidence
    evidence: [
      {
        type: { type: String, enum: ["photo", "video", "audio", "document"] },
        url: String,
        filename: String,
        uploadedAt: { type: Date, default: Date.now },
      },
    ],

    // Status & Assignment
    status: {
      type: String,
      enum: [
        "submitted",
        "under_review",
        "investigating",
        "verified",
        "resolved",
        "closed",
        "rejected",
      ],
      default: "submitted",
    },

    priority: {
      type: String,
      enum: ["low", "medium", "high", "critical"],
      default: "medium",
    },

    assignedOfficer: {
      type: mongoose.Schema.Types.ObjectId,
      ref: "User",
    },

    assignedStation: {
      type: String,
    },

    // Response & Resolution
    officerNotes: [
      {
        note: String,
        addedBy: { type: mongoose.Schema.Types.ObjectId, ref: "User" },
        addedAt: { type: Date, default: Date.now },
      },
    ],

    resolution: {
      summary: String,
      actionTaken: String,
      resolvedBy: { type: mongoose.Schema.Types.ObjectId, ref: "User" },
      resolvedAt: Date,
    },

    // Tracking
    statusHistory: [
      {
        status: String,
        changedBy: { type: mongoose.Schema.Types.ObjectId, ref: "User" },
        changedAt: { type: Date, default: Date.now },
        reason: String,
      },
    ],

    // Metadata
    submittedAt: { type: Date, default: Date.now },
    updatedAt: { type: Date, default: Date.now },

    // For offline sync
    offlineId: String,
    syncedAt: Date,
  },
  { timestamps: true },
);

// Generate unique report ID before saving
reportSchema.pre("save", async function (next) {
  if (!this.reportId) {
    const date = new Date();
    const year = date.getFullYear().toString().slice(-2);
    const month = (date.getMonth() + 1).toString().padStart(2, "0");
    const count = (await this.constructor.countDocuments()) + 1;
    this.reportId = `RNP-${year}${month}-${count.toString().padStart(5, "0")}`;
  }
  next();
});

// Index for efficient queries
reportSchema.index({ status: 1, createdAt: -1 });
reportSchema.index({ "location.district": 1 });
reportSchema.index({ incidentType: 1 });
reportSchema.index({ assignedOfficer: 1 });

module.exports = mongoose.model("Report", reportSchema);
