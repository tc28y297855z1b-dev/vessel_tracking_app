# -*- coding: utf-8 -*-
"""
Vessel Tracking Application - Mock Database & Simulation Logic
This file defines real-world representative vessels for China-Japan trade,
their operational routes, and detailed port-by-port schedules.
VESSELS_DB is now loaded from a JSON file for dynamic updates.
"""

import json
import os
from datetime import datetime, timedelta

# Path to the JSON database file
DB_FILE = os.path.join(os.path.dirname(__file__), "vessels_db.json")

def load_vessels_db():
    """Load VESSELS_DB from JSON file. Returns empty dict if file doesn't exist or is invalid."""
    if os.path.exists(DB_FILE):
        try:
            with open(DB_FILE, "r", encoding="utf-8") as f:
                content = f.read().strip()
                if not content:
                    return {}
                return json.loads(content)
        except (json.JSONDecodeError, ValueError, IOError) as e:
            print(f"Warning: Failed to load vessels_db.json: {e}. Using empty database.")
            return {}
    return {}

def save_vessels_db(db):
    """Save VESSELS_DB to JSON file."""
    with open(DB_FILE, "w", encoding="utf-8") as f:
        json.dump(db, f, indent=2, ensure_ascii=False)

# Default vessel data as fallback when JSON file is empty or fails to load
DEFAULT_VESSELS = {
    "9785809": {
        "imo": "9785809",
        "name": "COSCO SHIPPING SAGITTARIUS",
        "company": "COSCO",
        "flag": "Hong Kong",
        "type": "Container Ship",
        "built": 2018,
        "gt": 141823,
        "dwt": 134850,
        "length": 366,
        "width": 48,
        "route_name": "China-Japan Express (CJX)",
        "base_lat": 31.2,
        "base_lon": 122.5,
        "speed_knots": 16.5,
        "status": "Underway using Engine",
        "destination": "OSAKA",
        "delay_hours": 36,
        "delay_reason": "Shanghai Port Congestion & Typhoon Side-effects"
    },
    "9847865": {
        "imo": "9847865",
        "name": "ONE APUS",
        "company": "ONE",
        "flag": "Japan",
        "type": "Container Ship",
        "built": 2019,
        "gt": 146694,
        "dwt": 139500,
        "length": 364,
        "width": 51,
        "route_name": "East Asia to Japan Loop (EA1)",
        "base_lat": 33.5,
        "base_lon": 136.2,
        "speed_knots": 18.2,
        "status": "Underway using Engine",
        "destination": "TOKYO",
        "delay_hours": 8,
        "delay_reason": "Dense fog in East China Sea"
    },
    "9470741": {
        "imo": "9470741",
        "name": "OOCL NAGOYA",
        "company": "OOCL",
        "flag": "Hong Kong",
        "type": "Container Ship",
        "built": 2009,
        "gt": 40164,
        "dwt": 50500,
        "length": 260,
        "width": 32,
        "route_name": "Kanto-Kansai Service (KTX3)",
        "base_lat": 29.8,
        "base_lon": 123.1,
        "speed_knots": 15.0,
        "status": "At Anchor",
        "destination": "NAGOYA",
        "delay_hours": 48,
        "delay_reason": "Ningbo-Zhoushan terminal custom system outage & berth waiting"
    },
    "9243760": {
        "imo": "9243760",
        "name": "SITC SHANGHAI",
        "company": "SITC",
        "flag": "Panama",
        "type": "Container Ship",
        "built": 2001,
        "gt": 9531,
        "dwt": 12000,
        "length": 140,
        "width": 22,
        "route_name": "SITC China-Japan Shuttle",
        "base_lat": 34.2,
        "base_lon": 134.9,
        "speed_knots": 12.4,
        "status": "Moored",
        "destination": "OSAKA",
        "delay_hours": 0,
        "delay_reason": "Normal operations"
    }
}

# Load the database from JSON file, fall back to defaults if empty
VESSELS_DB = load_vessels_db()
if not VESSELS_DB:
    VESSELS_DB = dict(DEFAULT_VESSELS)
    # Save defaults to JSON file for persistence
    try:
        save_vessels_db(VESSELS_DB)
    except Exception:
        pass

def generate_schedule(vessel_imo, current_date=None):
    """
    Generates realistic port-by-port schedules for China-Japan routes.
    Includes original planned schedule vs estimated/actual schedule based on current delay.
    """
    if current_date is None:
        current_date = datetime.now() # Use actual current time in production
    
    vessel = VESSELS_DB.get(vessel_imo)
    if not vessel:
        return []
    
    delay_hours = vessel["delay_hours"]
    
    # Let's map routes
    if vessel_imo == "9785809": # COSCO (Shanghai -> Osaka -> Kobe -> Nagoya -> Tokyo)
        base_time = current_date - timedelta(days=3) # Departed Shanghai 3 days ago
        ports = [
            {"port": "SHANGHAI (China)", "type": "POL (Port of Loading)", "transit_days": 0, "stay_hours": 18},
            {"port": "OSAKA (Japan)", "type": "POD (Port of Discharge)", "transit_days": 2.5, "stay_hours": 12},
            {"port": "KOBE (Japan)", "type": "POD (Port of Discharge)", "transit_days": 3.2, "stay_hours": 12},
            {"port": "NAGOYA (Japan)", "type": "POD (Port of Discharge)", "transit_days": 4.2, "stay_hours": 14},
            {"port": "TOKYO (Japan)", "type": "POD (Port of Discharge)", "transit_days": 5.5, "stay_hours": 18}
        ]
    elif vessel_imo == "9847865": # ONE APUS (Ningbo -> Shenzhen -> Tokyo -> Yokohama -> Shimizu)
        base_time = current_date - timedelta(days=4.5) # Departed Ningbo
        ports = [
            {"port": "NINGBO (China)", "type": "POL (Port of Loading)", "transit_days": 0, "stay_hours": 24},
            {"port": "SHENZHEN (China)", "type": "POL (Port of Loading)", "transit_days": 1.5, "stay_hours": 20},
            {"port": "TOKYO (Japan)", "type": "POD (Port of Discharge)", "transit_days": 5.0, "stay_hours": 16},
            {"port": "YOKOHAMA (Japan)", "type": "POD (Port of Discharge)", "transit_days": 5.8, "stay_hours": 12},
            {"port": "SHIMIZU (Japan)", "type": "POD (Port of Discharge)", "transit_days": 6.5, "stay_hours": 10}
        ]
    elif vessel_imo == "9470741": # OOCL NAGOYA (Shanghai -> Xiamen -> Osaka -> Kobe -> Nagoya)
        base_time = current_date - timedelta(days=2)
        ports = [
            {"port": "SHANGHAI (China)", "type": "POL (Port of Loading)", "transit_days": 0, "stay_hours": 20},
            {"port": "XIAMEN (China)", "type": "POL (Port of Loading)", "transit_days": 1.8, "stay_hours": 16},
            {"port": "OSAKA (Japan)", "type": "POD (Port of Discharge)", "transit_days": 4.5, "stay_hours": 12},
            {"port": "KOBE (Japan)", "type": "POD (Port of Discharge)", "transit_days": 5.1, "stay_hours": 12},
            {"port": "NAGOYA (Japan)", "type": "POD (Port of Discharge)", "transit_days": 6.2, "stay_hours": 14}
        ]
    else: # SITC SHANGHAI (Qingdao -> Lianyungang -> Osaka -> Kobe)
        base_time = current_date - timedelta(days=4)
        ports = [
            {"port": "QINGDAO (China)", "type": "POL (Port of Loading)", "transit_days": 0, "stay_hours": 16},
            {"port": "LIANYUNGANG (China)", "type": "POL (Port of Loading)", "transit_days": 1.0, "stay_hours": 14},
            {"port": "OSAKA (Japan)", "type": "POD (Port of Discharge)", "transit_days": 3.8, "stay_hours": 12},
            {"port": "KOBE (Japan)", "type": "POD (Port of Discharge)", "transit_days": 4.5, "stay_hours": 12}
        ]

    schedule = []
    accumulated_delay = delay_hours # delay propagates but can vary
    
    for i, port in enumerate(ports):
        # Calculate planned times
        planned_arrival = base_time + timedelta(days=port["transit_days"])
        planned_departure = planned_arrival + timedelta(hours=port["stay_hours"])
        
        # Calculate actual/estimated times (incorporating the delay)
        # POL departures and POD arrivals are delayed.
        actual_arrival = planned_arrival + timedelta(hours=accumulated_delay)
        actual_departure = planned_departure + timedelta(hours=accumulated_delay)
        
        # Determine status (Arrived, Departed, Estimated)
        if actual_departure < current_date:
            status = "Departed"
        elif actual_arrival < current_date <= actual_departure:
            status = "Berthing"
        else:
            status = "Estimated"
            
        schedule.append({
            "port": port["port"],
            "type": port["type"],
            "planned_eta": planned_arrival,
            "planned_etd": planned_departure,
            "estimated_eta": actual_arrival,
            "estimated_etd": actual_departure,
            "delay_hours": accumulated_delay,
            "status": status
        })
        
        # Slightly adjust delay for next port due to "catching up" (speed up) or additional port congestion
        if i > 0 and accumulated_delay > 0:
            # Container ships speed up to recover up to 4 hours per transit leg
            accumulated_delay = max(0, accumulated_delay - 4)

    return schedule

def interpolate_vessel_position(vessel_imo, current_date=None):
    """
    Simulates real-time latitude/longitude for vessels based on their current leg
    and delay in the schedule. Keeps the map coordinates dynamically moving.
    """
    if current_date is None:
        current_date = datetime.now() # Use actual current time in production
        
    vessel = VESSELS_DB.get(vessel_imo)
    if not vessel:
        return None
        
    schedule = generate_schedule(vessel_imo, current_date)
    if not schedule:
        return None
        
    # Find current leg
    current_port = None
    next_port = None
    
    # We find where the current_date falls
    for i in range(len(schedule) - 1):
        dep_time = schedule[i]["estimated_etd"]
        arr_time = schedule[i+1]["estimated_eta"]
        
        if dep_time <= current_date <= arr_time:
            current_port = schedule[i]
            next_port = schedule[i+1]
            break
            
    # Port coordinates map for visualization
    PORT_COORDS = {
        "SHANGHAI (China)": (31.2222, 121.4581),
        "NINGBO (China)": (29.8683, 121.5440),
        "SHENZHEN (China)": (22.5431, 114.0579),
        "QINGDAO (China)": (36.0671, 120.3826),
        "LIANYUNGANG (China)": (34.5966, 119.2213),
        "XIAMEN (China)": (24.4798, 118.0894),
        "OSAKA (Japan)": (34.6432, 135.4310),
        "KOBE (Japan)": (34.6750, 135.2210),
        "NAGOYA (Japan)": (35.0506, 136.8486),
        "TOKYO (Japan)": (35.6171, 139.7744),
        "YOKOHAMA (Japan)": (35.4431, 139.6542),
        "SHIMIZU (Japan)": (35.0163, 138.5034),
    }

    if current_port and next_port:
        # Vessel is at sea between current_port and next_port
        p1_coords = PORT_COORDS.get(current_port["port"], (vessel["base_lat"], vessel["base_lon"]))
        p2_coords = PORT_COORDS.get(next_port["port"], (34.6, 135.4))
        
        total_duration = (next_port["estimated_eta"] - current_port["estimated_etd"]).total_seconds()
        elapsed = (current_date - current_port["estimated_etd"]).total_seconds()
        
        fraction = max(0.0, min(1.0, elapsed / total_duration))
        
        lat = p1_coords[0] + (p2_coords[0] - p1_coords[0]) * fraction
        lon = p1_coords[1] + (p2_coords[1] - p1_coords[1]) * fraction
        
        status = "Underway using Engine"
        dest = next_port["port"]
    else:
        # At port or before/after entire journey
        # Check if currently at some port
        at_port = None
        for port in schedule:
            if port["estimated_eta"] <= current_date <= port["estimated_etd"]:
                at_port = port
                break
        
        if at_port:
            coords = PORT_COORDS.get(at_port["port"], (vessel["base_lat"], vessel["base_lon"]))
            lat, lon = coords[0], coords[1]
            status = "Moored" if "Japan" in at_port["port"] else "Berthing"
            dest = at_port["port"]
        else:
            # Default fallback coordinates
            lat, lon = vessel["base_lat"], vessel["base_lon"]
            status = vessel["status"]
            dest = vessel["destination"]
            
    return {
        "lat": lat,
        "lon": lon,
        "status": status,
        "destination": dest
    }
