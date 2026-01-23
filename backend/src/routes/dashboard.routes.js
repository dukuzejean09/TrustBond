const express = require("express");
const router = express.Router();
const Report = require("../models/Report");
const User = require("../models/User");
const auth = require("../middleware/auth");
const authorize = require("../middleware/authorize");

// Dashboard statistics
router.get(
  "/stats",
  [auth, authorize("officer", "supervisor", "admin", "super_admin")],
  async (req, res) => {
    try {
      const today = new Date();
      today.setHours(0, 0, 0, 0);

      const thisMonth = new Date(today.getFullYear(), today.getMonth(), 1);
      const lastMonth = new Date(today.getFullYear(), today.getMonth() - 1, 1);

      // Get report counts
      const [
        totalReports,
        pendingReports,
        inProgressReports,
        resolvedReports,
        todayReports,
        thisMonthReports,
        lastMonthReports,
      ] = await Promise.all([
        Report.countDocuments(),
        Report.countDocuments({
          status: { $in: ["submitted", "under_review"] },
        }),
        Report.countDocuments({ status: "investigating" }),
        Report.countDocuments({ status: "resolved" }),
        Report.countDocuments({ createdAt: { $gte: today } }),
        Report.countDocuments({ createdAt: { $gte: thisMonth } }),
        Report.countDocuments({
          createdAt: { $gte: lastMonth, $lt: thisMonth },
        }),
      ]);

      // Calculate trend
      const trend =
        lastMonthReports > 0
          ? (
              ((thisMonthReports - lastMonthReports) / lastMonthReports) *
              100
            ).toFixed(1)
          : 0;

      // Get reports by type
      const reportsByType = await Report.aggregate([
        {
          $group: {
            _id: "$incidentType",
            count: { $sum: 1 },
          },
        },
        { $sort: { count: -1 } },
      ]);

      // Get reports by district
      const reportsByDistrict = await Report.aggregate([
        {
          $group: {
            _id: "$location.district",
            count: { $sum: 1 },
          },
        },
        { $sort: { count: -1 } },
        { $limit: 10 },
      ]);

      // Get recent reports (last 7 days trend)
      const last7Days = new Date(today);
      last7Days.setDate(last7Days.getDate() - 7);

      const dailyReports = await Report.aggregate([
        {
          $match: { createdAt: { $gte: last7Days } },
        },
        {
          $group: {
            _id: { $dateToString: { format: "%Y-%m-%d", date: "$createdAt" } },
            count: { $sum: 1 },
          },
        },
        { $sort: { _id: 1 } },
      ]);

      res.json({
        success: true,
        data: {
          overview: {
            totalReports,
            pendingReports,
            inProgressReports,
            resolvedReports,
            todayReports,
            thisMonthReports,
            monthlyTrend: parseFloat(trend),
          },
          reportsByType,
          reportsByDistrict,
          dailyTrend: dailyReports,
        },
      });
    } catch (error) {
      res.status(500).json({ success: false, message: error.message });
    }
  },
);

// Get all reports with filters (for officers)
router.get(
  "/reports",
  [auth, authorize("officer", "supervisor", "admin", "super_admin")],
  async (req, res) => {
    try {
      const {
        status,
        incidentType,
        district,
        startDate,
        endDate,
        assigned,
        page = 1,
        limit = 20,
        sortBy = "createdAt",
        sortOrder = "desc",
      } = req.query;

      // Build filter
      const filter = {};
      if (status) filter.status = status;
      if (incidentType) filter.incidentType = incidentType;
      if (district) filter["location.district"] = district;
      if (startDate || endDate) {
        filter.createdAt = {};
        if (startDate) filter.createdAt.$gte = new Date(startDate);
        if (endDate) filter.createdAt.$lte = new Date(endDate);
      }
      if (assigned === "me") filter.assignedOfficer = req.user.id;
      if (assigned === "unassigned") filter.assignedOfficer = null;

      // Pagination
      const skip = (page - 1) * limit;
      const sort = { [sortBy]: sortOrder === "asc" ? 1 : -1 };

      const [reports, total] = await Promise.all([
        Report.find(filter)
          .populate("assignedOfficer", "firstName lastName rank badgeNumber")
          .populate("reporter", "firstName lastName phone")
          .sort(sort)
          .skip(skip)
          .limit(parseInt(limit)),
        Report.countDocuments(filter),
      ]);

      res.json({
        success: true,
        data: reports,
        pagination: {
          current: parseInt(page),
          pages: Math.ceil(total / limit),
          total,
          limit: parseInt(limit),
        },
      });
    } catch (error) {
      res.status(500).json({ success: false, message: error.message });
    }
  },
);

// Update report status
router.patch(
  "/reports/:reportId/status",
  [auth, authorize("officer", "supervisor", "admin", "super_admin")],
  async (req, res) => {
    try {
      const { status, notes } = req.body;
      const validStatuses = [
        "submitted",
        "under_review",
        "investigating",
        "resolved",
        "closed",
        "rejected",
      ];

      if (!validStatuses.includes(status)) {
        return res
          .status(400)
          .json({ success: false, message: "Invalid status" });
      }

      const report = await Report.findOne({ reportId: req.params.reportId });
      if (!report) {
        return res
          .status(404)
          .json({ success: false, message: "Report not found" });
      }

      // Add to status history
      report.statusHistory.push({
        status,
        notes,
        changedBy: req.user.id,
        changedAt: new Date(),
      });

      report.status = status;
      if (status === "resolved") {
        report.resolvedAt = new Date();
      }

      await report.save();

      res.json({
        success: true,
        message: "Report status updated",
        data: { reportId: report.reportId, status: report.status },
      });
    } catch (error) {
      res.status(500).json({ success: false, message: error.message });
    }
  },
);

// Assign officer to report
router.patch(
  "/reports/:reportId/assign",
  [auth, authorize("supervisor", "admin", "super_admin")],
  async (req, res) => {
    try {
      const { officerId } = req.body;

      const [report, officer] = await Promise.all([
        Report.findOne({ reportId: req.params.reportId }),
        User.findOne({ _id: officerId, role: "officer", isActive: true }),
      ]);

      if (!report) {
        return res
          .status(404)
          .json({ success: false, message: "Report not found" });
      }
      if (!officer) {
        return res
          .status(404)
          .json({ success: false, message: "Officer not found or inactive" });
      }

      report.assignedOfficer = officerId;
      report.status = "under_review";
      report.statusHistory.push({
        status: "under_review",
        notes: `Assigned to Officer ${officer.firstName} ${officer.lastName} (${officer.badgeNumber})`,
        changedBy: req.user.id,
        changedAt: new Date(),
      });

      await report.save();

      res.json({
        success: true,
        message: "Officer assigned successfully",
        data: {
          reportId: report.reportId,
          assignedOfficer: {
            id: officer._id,
            name: `${officer.firstName} ${officer.lastName}`,
            badgeNumber: officer.badgeNumber,
          },
        },
      });
    } catch (error) {
      res.status(500).json({ success: false, message: error.message });
    }
  },
);

// Get officers list (for assignment)
router.get(
  "/officers",
  [auth, authorize("supervisor", "admin", "super_admin")],
  async (req, res) => {
    try {
      const { station, available } = req.query;

      const filter = { role: "officer", isActive: true };
      if (station) filter.station = station;

      const officers = await User.find(filter).select(
        "firstName lastName rank badgeNumber station department",
      );

      // Get active case count for each officer
      const officerData = await Promise.all(
        officers.map(async (officer) => {
          const activeCases = await Report.countDocuments({
            assignedOfficer: officer._id,
            status: { $in: ["under_review", "investigating"] },
          });
          return {
            ...officer.toObject(),
            activeCases,
          };
        }),
      );

      res.json({
        success: true,
        count: officerData.length,
        data: officerData,
      });
    } catch (error) {
      res.status(500).json({ success: false, message: error.message });
    }
  },
);

// Add investigation notes
router.post(
  "/reports/:reportId/notes",
  [auth, authorize("officer", "supervisor", "admin")],
  async (req, res) => {
    try {
      const { content, isInternal } = req.body;

      const report = await Report.findOne({ reportId: req.params.reportId });
      if (!report) {
        return res
          .status(404)
          .json({ success: false, message: "Report not found" });
      }

      if (!report.investigationNotes) {
        report.investigationNotes = [];
      }

      report.investigationNotes.push({
        content,
        isInternal: isInternal || false,
        createdBy: req.user.id,
        createdAt: new Date(),
      });

      await report.save();

      res.json({
        success: true,
        message: "Note added successfully",
      });
    } catch (error) {
      res.status(500).json({ success: false, message: error.message });
    }
  },
);

module.exports = router;
