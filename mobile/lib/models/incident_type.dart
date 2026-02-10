import 'package:flutter/material.dart';

enum IncidentCategory {
  crimeAgainstPerson,
  propertyTheft,
  fraudFinancial,
  suspiciousActivity,
  publicOrder,
  trafficRoad,
  infrastructureEnvironment,
}

class IncidentType {
  final String id;
  final String name;
  final String description;
  final IconData icon;
  final IncidentCategory category;
  final Color color;

  const IncidentType({
    required this.id,
    required this.name,
    required this.description,
    required this.icon,
    required this.category,
    required this.color,
  });

  // Crime Against Person
  static const assault = IncidentType(
    id: 'assault',
    name: 'Assault',
    description: 'Physical attack on a person',
    icon: Icons.person_off,
    category: IncidentCategory.crimeAgainstPerson,
    color: Color(0xFFE53935),
  );

  static const threats = IncidentType(
    id: 'threats',
    name: 'Threats',
    description: 'Verbal or written threats',
    icon: Icons.warning_amber,
    category: IncidentCategory.crimeAgainstPerson,
    color: Color(0xFFE53935),
  );

  static const harassment = IncidentType(
    id: 'harassment',
    name: 'Harassment',
    description: 'Unwanted persistent behavior',
    icon: Icons.record_voice_over,
    category: IncidentCategory.crimeAgainstPerson,
    color: Color(0xFFE53935),
  );

  static const domesticDisturbance = IncidentType(
    id: 'domestic_disturbance',
    name: 'Domestic Disturbance',
    description: 'Family or household conflict',
    icon: Icons.home_work,
    category: IncidentCategory.crimeAgainstPerson,
    color: Color(0xFFE53935),
  );

  static const childAbuse = IncidentType(
    id: 'child_abuse',
    name: 'Child Abuse',
    description: 'Harm or mistreatment of a child',
    icon: Icons.child_care,
    category: IncidentCategory.crimeAgainstPerson,
    color: Color(0xFFE53935),
  );

  // Property & Theft
  static const theft = IncidentType(
    id: 'theft',
    name: 'Theft',
    description: 'Stealing of property',
    icon: Icons.shopping_bag,
    category: IncidentCategory.propertyTheft,
    color: Color(0xFFFF9800),
  );

  static const pickpocketing = IncidentType(
    id: 'pickpocketing',
    name: 'Pickpocketing',
    description: 'Theft from person',
    icon: Icons.back_hand,
    category: IncidentCategory.propertyTheft,
    color: Color(0xFFFF9800),
  );

  static const shoplifting = IncidentType(
    id: 'shoplifting',
    name: 'Shoplifting',
    description: 'Theft from store',
    icon: Icons.storefront,
    category: IncidentCategory.propertyTheft,
    color: Color(0xFFFF9800),
  );

  static const vehicleTheft = IncidentType(
    id: 'vehicle_theft',
    name: 'Vehicle/Motorbike Theft',
    description: 'Theft of vehicle',
    icon: Icons.directions_car,
    category: IncidentCategory.propertyTheft,
    color: Color(0xFFFF9800),
  );

  static const vandalism = IncidentType(
    id: 'vandalism',
    name: 'Vandalism',
    description: 'Deliberate property damage',
    icon: Icons.broken_image,
    category: IncidentCategory.propertyTheft,
    color: Color(0xFFFF9800),
  );

  // Fraud & Financial
  static const fraud = IncidentType(
    id: 'fraud',
    name: 'Fraud/Scam',
    description: 'Deceptive schemes for money',
    icon: Icons.money_off,
    category: IncidentCategory.fraudFinancial,
    color: Color(0xFF9C27B0),
  );

  static const mobileMoneyFraud = IncidentType(
    id: 'mobile_money_fraud',
    name: 'Mobile Money Fraud',
    description: 'Mobile payment scams',
    icon: Icons.phone_android,
    category: IncidentCategory.fraudFinancial,
    color: Color(0xFF9C27B0),
  );

  static const forgery = IncidentType(
    id: 'forgery',
    name: 'Forgery',
    description: 'Fake documents or signatures',
    icon: Icons.description,
    category: IncidentCategory.fraudFinancial,
    color: Color(0xFF9C27B0),
  );

  static const breachOfTrust = IncidentType(
    id: 'breach_of_trust',
    name: 'Breach of Trust',
    description: 'Misuse of entrusted items',
    icon: Icons.handshake,
    category: IncidentCategory.fraudFinancial,
    color: Color(0xFF9C27B0),
  );

  // Suspicious Activity
  static const suspiciousPerson = IncidentType(
    id: 'suspicious_person',
    name: 'Suspicious Person',
    description: 'Unknown or unusual behavior',
    icon: Icons.person_search,
    category: IncidentCategory.suspiciousActivity,
    color: Color(0xFF607D8B),
  );

  static const suspiciousVehicle = IncidentType(
    id: 'suspicious_vehicle',
    name: 'Suspicious Vehicle',
    description: 'Unknown or unusual vehicle',
    icon: Icons.directions_car_filled,
    category: IncidentCategory.suspiciousActivity,
    color: Color(0xFF607D8B),
  );

  static const trespassing = IncidentType(
    id: 'trespassing',
    name: 'Trespassing',
    description: 'Unauthorized entry',
    icon: Icons.do_not_step,
    category: IncidentCategory.suspiciousActivity,
    color: Color(0xFF607D8B),
  );

  static const abandonedObject = IncidentType(
    id: 'abandoned_object',
    name: 'Abandoned Object',
    description: 'Unattended suspicious item',
    icon: Icons.inventory_2,
    category: IncidentCategory.suspiciousActivity,
    color: Color(0xFF607D8B),
  );

  // Public Order
  static const noiseDisturbance = IncidentType(
    id: 'noise_disturbance',
    name: 'Noise Disturbance',
    description: 'Excessive noise',
    icon: Icons.volume_up,
    category: IncidentCategory.publicOrder,
    color: Color(0xFF2196F3),
  );

  static const streetFights = IncidentType(
    id: 'street_fights',
    name: 'Street Fights',
    description: 'Public altercations',
    icon: Icons.sports_mma,
    category: IncidentCategory.publicOrder,
    color: Color(0xFF2196F3),
  );

  static const publicNuisance = IncidentType(
    id: 'public_nuisance',
    name: 'Public Nuisance',
    description: 'Disruptive public behavior',
    icon: Icons.groups,
    category: IncidentCategory.publicOrder,
    color: Color(0xFF2196F3),
  );

  static const illegalGatherings = IncidentType(
    id: 'illegal_gatherings',
    name: 'Illegal Gatherings',
    description: 'Unauthorized assemblies',
    icon: Icons.people,
    category: IncidentCategory.publicOrder,
    color: Color(0xFF2196F3),
  );

  // Traffic & Road
  static const recklessDriving = IncidentType(
    id: 'reckless_driving',
    name: 'Reckless Driving',
    description: 'Dangerous driving behavior',
    icon: Icons.speed,
    category: IncidentCategory.trafficRoad,
    color: Color(0xFF4CAF50),
  );

  static const illegalParking = IncidentType(
    id: 'illegal_parking',
    name: 'Illegal Parking',
    description: 'Parking violations',
    icon: Icons.local_parking,
    category: IncidentCategory.trafficRoad,
    color: Color(0xFF4CAF50),
  );

  static const brokenTrafficLight = IncidentType(
    id: 'broken_traffic_light',
    name: 'Broken Traffic Light',
    description: 'Malfunctioning signals',
    icon: Icons.traffic,
    category: IncidentCategory.trafficRoad,
    color: Color(0xFF4CAF50),
  );

  static const roadObstruction = IncidentType(
    id: 'road_obstruction',
    name: 'Road Obstruction',
    description: 'Blocked roadway',
    icon: Icons.block,
    category: IncidentCategory.trafficRoad,
    color: Color(0xFF4CAF50),
  );

  // Infrastructure & Environment
  static const brokenStreetlight = IncidentType(
    id: 'broken_streetlight',
    name: 'Broken Streetlight',
    description: 'Non-working street lamp',
    icon: Icons.lightbulb_outline,
    category: IncidentCategory.infrastructureEnvironment,
    color: Color(0xFF795548),
  );

  static const waterLeak = IncidentType(
    id: 'water_leak',
    name: 'Water Leak',
    description: 'Water infrastructure issue',
    icon: Icons.water_drop,
    category: IncidentCategory.infrastructureEnvironment,
    color: Color(0xFF795548),
  );

  static const openManhole = IncidentType(
    id: 'open_manhole',
    name: 'Open Manhole',
    description: 'Uncovered manhole',
    icon: Icons.warning,
    category: IncidentCategory.infrastructureEnvironment,
    color: Color(0xFF795548),
  );

  static const wasteDumping = IncidentType(
    id: 'waste_dumping',
    name: 'Waste Dumping',
    description: 'Illegal garbage disposal',
    icon: Icons.delete,
    category: IncidentCategory.infrastructureEnvironment,
    color: Color(0xFF795548),
  );

  static const strayAnimals = IncidentType(
    id: 'stray_animals',
    name: 'Stray Animals',
    description: 'Uncontrolled animals',
    icon: Icons.pets,
    category: IncidentCategory.infrastructureEnvironment,
    color: Color(0xFF795548),
  );

  // Other (catch-all category)
  static const other = IncidentType(
    id: 'other',
    name: 'Other',
    description: 'Other incident type',
    icon: Icons.help_outline,
    category: IncidentCategory.suspiciousActivity,
    color: Color(0xFF9E9E9E),
  );

  // Get all types
  static List<IncidentType> get allTypes => [
    assault, threats, harassment, domesticDisturbance, childAbuse,
    theft, pickpocketing, shoplifting, vehicleTheft, vandalism,
    fraud, mobileMoneyFraud, forgery, breachOfTrust,
    suspiciousPerson, suspiciousVehicle, trespassing, abandonedObject,
    noiseDisturbance, streetFights, publicNuisance, illegalGatherings,
    recklessDriving, illegalParking, brokenTrafficLight, roadObstruction,
    brokenStreetlight, waterLeak, openManhole, wasteDumping, strayAnimals,
    other,
  ];

  // Get by category
  static List<IncidentType> getByCategory(IncidentCategory category) {
    return allTypes.where((t) => t.category == category).toList();
  }

  // Category names
  static String getCategoryName(IncidentCategory category) {
    switch (category) {
      case IncidentCategory.crimeAgainstPerson:
        return 'Crime Against Person';
      case IncidentCategory.propertyTheft:
        return 'Property & Theft';
      case IncidentCategory.fraudFinancial:
        return 'Fraud & Financial';
      case IncidentCategory.suspiciousActivity:
        return 'Suspicious Activity';
      case IncidentCategory.publicOrder:
        return 'Public Order';
      case IncidentCategory.trafficRoad:
        return 'Traffic & Road';
      case IncidentCategory.infrastructureEnvironment:
        return 'Infrastructure & Environment';
    }
  }

  // Category icons
  static IconData getCategoryIcon(IncidentCategory category) {
    switch (category) {
      case IncidentCategory.crimeAgainstPerson:
        return Icons.person;
      case IncidentCategory.propertyTheft:
        return Icons.home;
      case IncidentCategory.fraudFinancial:
        return Icons.account_balance;
      case IncidentCategory.suspiciousActivity:
        return Icons.visibility;
      case IncidentCategory.publicOrder:
        return Icons.gavel;
      case IncidentCategory.trafficRoad:
        return Icons.directions_car;
      case IncidentCategory.infrastructureEnvironment:
        return Icons.construction;
    }
  }

  // Search types
  static List<IncidentType> search(String query) {
    if (query.isEmpty) return allTypes;
    final lowerQuery = query.toLowerCase();
    return allTypes.where((t) =>
      t.name.toLowerCase().contains(lowerQuery) ||
      t.description.toLowerCase().contains(lowerQuery)
    ).toList();
  }
}
