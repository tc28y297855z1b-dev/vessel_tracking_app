# -*- coding: utf-8 -*-
"""
Vessel Tracking Application - Data Scraping & Merging Logic
This module attempts to scrape real-time positions from VesselFinder and falls back
to mock simulations if blocked or if mock-mode is chosen.
"""

import requests
from bs4 import BeautifulSoup
import re
import random
from datetime import datetime
from mock_data import VESSELS_DB, generate_schedule, interpolate_vessel_position

# HTTP Headers to mimic a real web browser and avoid quick bot detection
HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8",
    "Accept-Language": "en-US,en;q=0.9,ja;q=0.8",
    "Referer": "https://www.google.com/",
    "Cache-Control": "max-age=0"
}

def get_vessel_realtime_data(imo):
    """
    Attempts to scrape real-time position of a vessel using its IMO number.
    If scraping fails (blocked by Cloudflare/network issue), falls back gracefully.
    """
    vessel_info = VESSELS_DB.get(str(imo))
    if not vessel_info:
        # If vessel not in our pre-defined list, try to create a generic mock structure
        vessel_info = {
            "imo": str(imo),
            "name": f"SHIP-{imo}",
            "company": "UNKNOWN",
            "flag": "Unknown",
            "type": "Container Ship",
            "built": 2015,
            "gt": 50000,
            "dwt": 60000,
            "length": 250,
            "width": 32,
            "route_name": "Asia Pacific Service",
            "base_lat": 31.0,
            "base_lon": 125.0,
            "speed_knots": 15.0,
            "status": "Underway using Engine",
            "destination": "JAPAN",
            "delay_hours": 12,
            "delay_reason": "General congestion"
        }

    # URL patterns for VesselFinder search by IMO
    search_url = f"https://www.vesselfinder.com/vessels?name={imo}"
    
    try:
        # 1. Search for the vessel detail page URL
        response = requests.get(search_url, headers=HEADERS, timeout=10)
        
        if response.status_code == 200:
            soup = BeautifulSoup(response.text, 'html.parser')
            # Look for link containing /vessels/
            vessel_link = None
            for link in soup.find_all('a', href=True):
                if '/vessels/' in link['href'] and f"IMO-{imo}" in link['href'].upper():
                    vessel_link = "https://www.vesselfinder.com" + link['href']
                    break
            
            if vessel_link:
                # 2. Get the actual detail page containing live map coords
                detail_resp = requests.get(vessel_link, headers=HEADERS, timeout=10)
                if detail_resp.status_code == 200:
                    detail_soup = BeautifulSoup(detail_resp.text, 'html.parser')
                    
                    # Extract latitude/longitude
                    # VesselFinder often embeds coordinates in JS or custom attributes
                    # E.g., <div class="map-container" data-lat="31.234" data-lon="122.345"> or in script
                    html_content = detail_resp.text
                    
                    # Try finding lat/lon via Regex
                    lat_match = re.search(r'"lat"\s*:\s*(-?\d+\.\d+)', html_content)
                    lon_match = re.search(r'"lon"\s*:\s*(-?\d+\.\d+)', html_content)
                    course_match = re.search(r'"course"\s*:\s*(\d+)', html_content)
                    speed_match = re.search(r'"speed"\s*:\s*(\d+\.?\d*)', html_content)
                    status_match = re.search(r'"status"\s*:\s*"([^"]+)"', html_content)
                    dest_match = re.search(r'"destination"\s*:\s*"([^"]+)"', html_content)
                    
                    if lat_match and lon_match:
                        # Success scraping real data
                        return {
                            "imo": imo,
                            "name": vessel_info["name"],
                            "company": vessel_info["company"],
                            "flag": vessel_info["flag"],
                            "type": vessel_info["type"],
                            "built": vessel_info["built"],
                            "gt": vessel_info["gt"],
                            "dwt": vessel_info["dwt"],
                            "length": vessel_info["length"],
                            "width": vessel_info["width"],
                            "route_name": vessel_info["route_name"],
                            "lat": float(lat_match.group(1)),
                            "lon": float(lon_match.group(1)),
                            "speed_knots": float(speed_match.group(1)) if speed_match else vessel_info["speed_knots"],
                            "course": int(course_match.group(1)) if course_match else 0,
                            "status": status_match.group(1) if status_match else "Underway",
                            "destination": dest_match.group(1) if dest_match else vessel_info["destination"],
                            "is_realtime": True,
                            "delay_hours": vessel_info["delay_hours"],
                            "delay_reason": vessel_info["delay_reason"],
                            "source": "VesselFinder (Live AIS)"
                        }
                        
                    # Alternative: Extract from HTML table
                    # VesselFinder has a "Vessel Position" table with Lat/Lon in text, e.g. "31.2345 N / 122.3456 E"
                    pos_table = detail_soup.find('table', class_='aparams')
                    if pos_table:
                        text = pos_table.get_text()
                        # Match coordinates pattern like "31.2222 N / 121.4581 E" or similar
                        coords = re.findall(r'(\d+\.\d+)\s*([NS])\s*/\s*(\d+\.\d+)\s*([EW])', text)
                        if coords:
                            lat_val, lat_dir, lon_val, lon_dir = coords[0]
                            lat = float(lat_val) * (1 if lat_dir == 'N' else -1)
                            lon = float(lon_val) * (1 if lon_dir == 'E' else -1)
                            
                            return {
                                "imo": imo,
                                "name": vessel_info["name"],
                                "company": vessel_info["company"],
                                "flag": vessel_info["flag"],
                                "type": vessel_info["type"],
                                "built": vessel_info["built"],
                                "gt": vessel_info["gt"],
                                "dwt": vessel_info["dwt"],
                                "length": vessel_info["length"],
                                "width": vessel_info["width"],
                                "route_name": vessel_info["route_name"],
                                "lat": lat,
                                "lon": lon,
                                "speed_knots": vessel_info["speed_knots"],
                                "course": 0,
                                "status": "Underway",
                                "destination": vessel_info["destination"],
                                "is_realtime": True,
                                "delay_hours": vessel_info["delay_hours"],
                                "delay_reason": vessel_info["delay_reason"],
                                "source": "VesselFinder (AIS Table Parser)"
                            }
    except Exception as e:
        # Gracefully print error or log it (won't crash the app)
        print(f"Scraping attempt failed for IMO {imo}: {e}")

    # Fallback to smart simulated interpolation (this gives very realistic China-Japan ship positions)
    simulated_pos = interpolate_vessel_position(imo)
    if simulated_pos:
        return {
            "imo": imo,
            "name": vessel_info["name"],
            "company": vessel_info["company"],
            "flag": vessel_info["flag"],
            "type": vessel_info["type"],
            "built": vessel_info["built"],
            "gt": vessel_info["gt"],
            "dwt": vessel_info["dwt"],
            "length": vessel_info["length"],
            "width": vessel_info["width"],
            "route_name": vessel_info["route_name"],
            "lat": simulated_pos["lat"],
            "lon": simulated_pos["lon"],
            "speed_knots": vessel_info["speed_knots"],
            "course": 45, # Simulated northeastern heading to Japan
            "status": simulated_pos["status"],
            "destination": simulated_pos["destination"],
            "is_realtime": False,
            "delay_hours": vessel_info["delay_hours"],
            "delay_reason": vessel_info["delay_reason"],
            "source": "Maritime Schedule & Position Simulation (Robust)"
        }
    
    # Absolute default fallback
    return {
        "imo": imo,
        "name": vessel_info["name"],
        "company": vessel_info["company"],
        "flag": vessel_info["flag"],
        "type": vessel_info["type"],
        "built": vessel_info["built"],
        "gt": vessel_info["gt"],
        "dwt": vessel_info["dwt"],
        "length": vessel_info["length"],
        "width": vessel_info["width"],
        "route_name": vessel_info["route_name"],
        "lat": vessel_info["base_lat"],
        "lon": vessel_info["base_lon"],
        "speed_knots": vessel_info["speed_knots"],
        "course": 0,
        "status": vessel_info["status"],
        "destination": vessel_info["destination"],
        "is_realtime": False,
        "delay_hours": vessel_info["delay_hours"],
        "delay_reason": vessel_info["delay_reason"],
        "source": "Default Vessel DB Profile"
    }

def get_integrated_vessel_tracker(imo, current_date=None):
    """
    Main integrated endpoint. Combines:
    1. Realtime AIS coordinates & speed
    2. Long Range Port-by-Port planned vs estimated ETD/ETA schedule
    """
    pos_data = get_vessel_realtime_data(imo)
    schedule = generate_schedule(imo, current_date)
    
    return {
        "vessel": pos_data,
        "schedule": schedule
    }
