# -*- coding: utf-8 -*-
"""
Vessel Tracking Application - Streamlit Web Interface
A professional, interactive dashboard to track container ships, 
analyze multiple port ETDs (from China to Japanese ports), and monitor delays.
"""

import streamlit as st
import pandas as pd
import folium
from streamlit_folium import st_folium
from datetime import datetime

from mock_data import VESSELS_DB
from tracker import get_integrated_vessel_tracker

# Page configuration
st.set_page_config(
    page_title="日中コンテナ船 ETD & 運行状況追跡アプリ",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS for styling
st.markdown("""
<style>
    .metric-container {
        background-color: #f0f2f6;
        padding: 15px;
        border-radius: 10px;
        margin-bottom: 10px;
    }
    .delay-text {
        color: #ff4b4b;
        font-weight: bold;
    }
    .ontime-text {
        color: #09ab3b;
        font-weight: bold;
    }
    .port-badge {
        background-color: #1c83e1;
        color: white;
        padding: 3px 8px;
        border-radius: 5px;
        font-size: 0.8em;
    }
</style>
""", unsafe_allow_html=True)

# Application Header (Compact size, no emoji)
st.header("日中コンテナ船 ETD & 運行状況追跡システム")
st.markdown("""
中国から日本へ輸入されるコンテナを搭載した船舶の日本各港（大阪・名古屋・東京等）への到着予定（ETA）・出発予定（ETD）、遅延要因、およびリアルタイム位置を一元管理します。
""")

# Sidebar settings
st.sidebar.header("🔍 追跡・検索パネル")

# 1. Company Selection
companies = sorted(list(set(v["company"] for v in VESSELS_DB.values())))
selected_company = st.sidebar.selectbox("1. 船舶会社を選択", ["すべて"] + companies)

# Filter vessels based on company
if selected_company == "すべて":
    filtered_vessels = VESSELS_DB
else:
    filtered_vessels = {k: v for k, v in VESSELS_DB.items() if v["company"] == selected_company}

# 2. Vessel Selection
vessel_options = {f"{v['company']} - {v['name']} (IMO: {k})": k for k, v in filtered_vessels.items()}
selected_vessel_label = st.sidebar.selectbox("2. 追跡する船舶を選択", list(vessel_options.keys()))
selected_imo = vessel_options[selected_vessel_label]

# Get the vessel company for container tracking link
current_vessel_company = VESSELS_DB[selected_imo]["company"]

# 3. Container / BL Number Input
st.sidebar.markdown("---")
st.sidebar.subheader("📦 コンテナ・B/L個別追跡")
tracking_no = st.sidebar.text_input(
    "コンテナ番号 または B/L番号を入力",
    placeholder="例: ONEY1234567, COSU6123456",
    value=""
)

# Deep link generation logic based on shipping line and tracking number
def get_cargo_tracking_link(company, number):
    if not number:
        return None
    num_clean = number.strip()
    if company == "ONE":
        return f"https://ecomm.one-line.com/one-ecom/manage-shipment/cargo-tracking?asTrackingType=C&asTrackingValue={num_clean}"
    elif company == "COSCO":
        return f"https://lines.coscoshipping.com/ebusiness/cargoTracking?searchType=CONTAINER&searchKeys={num_clean}"
    elif company == "OOCL":
        return f"https://www.oocl.com/eng/ourservices/container-tracking/Pages/default.aspx?key={num_clean}&type=container"
    elif company == "SITC":
        return f"https://webtracking.sitc.com/WebTracking/search.do?containerNo={num_clean}"
    return None

if tracking_no:
    tracking_link = get_cargo_tracking_link(current_vessel_company, tracking_no)
    if tracking_link:
        st.sidebar.success(f"👉 {current_vessel_company} の追跡URLが生成されました")
        st.sidebar.link_button(
            f"🚀 {current_vessel_company} で直接コンテナを追跡",
            tracking_link,
            use_container_width=True
        )
    else:
        st.sidebar.warning("この船舶会社の自動追跡リンクは現在サポートされていません。下のリンク一覧をご利用ください。")

st.sidebar.markdown("---")

# For production, use actual current time
current_sim_datetime = datetime.now() # Use actual current time in production

# Optional: If you still want to offer a 

st.sidebar.markdown("---")
st.sidebar.info("""
💡 **追跡のポイント**
* 船舶番号（IMO番号）をキーに、グローバルAISデータからリアルタイムの位置を取得します。
* 経由する全ての日本港（大阪、神戸、名古屋、東京など）のETA/ETDは、各海運会社の長期運行スケジュール（Long Range Schedule）と動的遅延補正から自動計算されます。
""")

# Get integrated vessel tracker data
tracker_data = get_integrated_vessel_tracker(selected_imo, current_sim_datetime)
vessel = tracker_data["vessel"]
schedule = tracker_data["schedule"]

# ==================== DELAY ALERT BOARD (HIGH PRIORITY) ====================
delay_hours = vessel["delay_hours"]
if delay_hours > 0:
    st.error(f"""
    🚨 **遅延警告 (Delay Warning)**  
    * **遅延時間**: {delay_hours} 時間遅れ  
    * **遅延要因**: **{vessel["delay_reason"]}**  
    * **注意事項**: 中国側積出港での混雑や天候の影響によりスケジュールが乱れています。これに伴い、後続の日本各港（大阪・神戸・名古屋・東京等）への**ETA（到着予定）およびETD（出発予定）もすべて同等の遅れが波及する見込み**です。今後の港湾の混雑状況によっては、さらに遅延が拡大する可能性がありますので十分にご注意ください。
    """)
else:
    st.success(f"""
    🟢 **正常運航中 (On Schedule)**  
    * **運航状況**: 定時運行 (On-Time)  
    * **遅延要因**: なし (現在のところ順調に推移しています)  
    * **注意事項**: 現時点では当初の計画スケジュール通りに各港へ寄港する見込みです。
    """)

# Layout columns for metadata and metrics (More compact)
col1, col2, col3, col4 = st.columns(4)

with col1:
    st.metric(
        label="追跡中船舶",
        value=vessel["name"],
        delta=f"IMO: {vessel["imo"]}",
        delta_color="off"
    )

with col2:
    status_label = vessel["status"]
    status_ja = {
        "Underway using Engine": "機関航行中",
        "At Anchor": "錨泊中 (錨をおろして停泊)",
        "Moored": "係留中 (接岸中)",
        "Berthing": "荷役・接岸作業中"
    }.get(status_label, status_label)
    
    st.metric(
        label="運航ステータス",
        value=status_ja,
        delta=f"速力: {vessel["speed_knots"]} ノット",
        delta_color="normal"
    )

with col3:
    st.metric(
        label="現在の遅延時間",
        value=f"{delay_hours} 時間" if delay_hours > 0 else "なし (定時)",
        delta="遅延波及あり" if delay_hours > 0 else "順調",
        delta_color="inverse" if delay_hours > 0 else "normal"
    )

with col4:
    st.metric(
        label="次の目的地 (AIS)",
        value=vessel["destination"],
        delta=f"データ元: {vessel["source"]}",
        delta_color="off"
    )

st.markdown("---")

# ==================== PRIORITY 1: SCHEDULE DETAIL TABLE ====================
st.subheader("📅 日本寄港・中国積出 運行スケジュール詳細")
st.markdown("中国での出発地（POL）から、日本の各寄港予定地（POD）における当初計画スケジュールと、現在の遅延を反映した最新予想スケジュール一覧です。")

# Format schedule into a beautiful pandas table
formatted_sched = []
for s in schedule:
    port_str = s["port"]
    port_type = "積出港 (POL)" if "POL" in s["type"] else "揚地港 (POD)"
    
    port_delay = s["delay_hours"]
    delay_display = f"{port_delay}時間遅れ" if port_delay > 0 else "定時 (On-Time)"
    
    status_map = {
        "Departed": "✅ 出発済み (Departed)",
        "Berthing": "⚓️ 接岸中 (Berthing)",
        "Estimated": "⏳ 到着予定 (Estimated)"
    }
    status_display = status_map.get(s["status"], s["status"])
    
    formatted_sched.append({
        "港名 (Port)": port_str,
        "役割 (Type)": port_type,
        "当初計画 ETA (到着)": s["planned_eta"].strftime("%Y/%m/%d %H:%M") if "POD" in s["type"] else "--",
        "当初計画 ETD (出発)": s["planned_etd"].strftime("%Y/%m/%d %H:%M"),
        "最新見込み ETA (到着)": s["estimated_eta"].strftime("%Y/%m/%d %H:%M") if "POD" in s["type"] else "--",
        "最新見込み ETD (出発)": s["estimated_etd"].strftime("%Y/%m/%d %H:%M"),
        "遅延時間": delay_display,
        "ステータス": status_display
    })

df_sched = pd.DataFrame(formatted_sched)
st.dataframe(df_sched, width="stretch", hide_index=True)

st.markdown("---")

# ==================== PRIORITY 2: MAP & SPECS ====================
map_col, spec_col = st.columns([2, 1])

with spec_col:
    st.subheader("📋 船舶基本情報 Specs")
    specs_df = pd.DataFrame({
        "項目": [
            "船舶会社 (Operator)", 
            "船籍 (Flag)", 
            "船種 (Type)", 
            "竣工年 (Built)", 
            "総トン数 (GT)", 
            "載貨重量トン (DWT)", 
            "全長 / 全幅 (Length/Beam)",
            "配属航路 (Service Route)"
        ],
        "仕様・値": [
            vessel["company"],
            vessel["flag"],
            vessel["type"],
            f"{vessel["built"]} 年",
            f"{vessel["gt"]:,} トン",
            f"{vessel["dwt"]:,} トン",
            f"{vessel["length"]}m / {vessel["width"]}m",
            vessel["route_name"]
        ]
    })
    st.dataframe(specs_df, width="stretch", hide_index=True)
    
    if vessel["is_realtime"]:
        st.success("🟢 VesselFinder からライブAIS位置情報を取得中")
    else:
        st.info("ℹ️ 現在は船舶スケジュールから位置を補間シミュレーションしています（耐障害モード稼働中）")

with map_col:
    st.subheader("🗺️ リアルタイム現在位置 & 航路マップ")
    
    # Initialize Folium Map centered on the ship or mid point
    m = folium.Map(location=[vessel["lat"], vessel["lon"]], zoom_start=5, control_scale=True)
    
    # Add Vessel Marker
    tooltip_html = f"""
    <b>{vessel["name"]}</b><br>
    会社: {vessel["company"]}<br>
    状態: {status_ja}<br>
    目的地: {vessel["destination"]}<br>
    遅延: {vessel["delay_hours"]}時間
    """
    
    folium.Marker(
        [vessel["lat"], vessel["lon"]],
        popup=folium.Popup(tooltip_html, max_width=300),
        tooltip=vessel["name"],
        icon=folium.Icon(color="red" if vessel["delay_hours"] > 0 else "blue", icon="ship", prefix="fa")
    ).add_to(m)
    
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
    
    # Draw port markers and routes
    route_points = []
    for s in schedule:
        port_name = s["port"]
        if port_name in PORT_COORDS:
            coords = PORT_COORDS[port_name]
            route_points.append(coords)
            
            is_pol = "China" in port_name or "POL" in s["type"]
            icon_color = "green" if is_pol else "orange"
            
            popup_text = f"""
            <b>{port_name}</b> ({s["type"]})<br>
            計画ETD: {s["planned_etd"].strftime("%Y-%m-%d %H:%M")}<br>
            最新見込ETD: {s["estimated_etd"].strftime("%Y-%m-%d %H:%M")}<br>
            ステータス: {s["status"]}
            """
            
            folium.Marker(
                coords,
                popup=folium.Popup(popup_text, max_width=250),
                tooltip=port_name,
                icon=folium.Icon(color=icon_color, icon="anchor", prefix="fa")
            ).add_to(m)
            
    # Draw path line if we have at least 2 points
    if len(route_points) >= 2:
        folium.PolyLine(
            route_points,
            color="darkblue",
            weight=3,
            opacity=0.6,
            tooltip="予定航路 (Planned Service Route)"
        ).add_to(m)
        
    st_folium(m, width=900, height=450, returned_objects=[])

# Section 3: Shortcuts to Cargo Tracking
st.markdown("---")
st.subheader("📦 各船社コンテナ・B/L追跡への直接リンク一覧")
st.markdown("""
個別の詳細なコンテナ追跡（通関状況、デマレージ等）を行いたい場合は、各社への公式リンクもご利用いただけます。
""")

col_lnk1, col_lnk2, col_lnk3, col_lnk4 = st.columns(4)

with col_lnk1:
    st.markdown("""
    **ONE (Ocean Network Express)**
    * [ONE Cargo Tracking 🔗](https://ecomm.one-line.com/one-ecom/manage-shipment/cargo-tracking)
    """, unsafe_allow_html=True)

with col_lnk2:
    st.markdown("""
    **COSCO SHIPPING**
    * [COSCO Container Tracking 🔗](https://lines.coscoshipping.com/ebusiness/cargoTracking)
    """, unsafe_allow_html=True)

with col_lnk3:
    st.markdown("""
    **OOCL**
    * [OOCL Cargo Tracking 🔗](https://www.oocl.com/eng/ourservices/container-tracking/Pages/default.aspx)
    """, unsafe_allow_html=True)

with col_lnk4:
    st.markdown("""
    **SITC Japan**
    * [SITC Container Tracking 🔗](https://webtracking.sitc.com/WebTracking/search.do)
    """, unsafe_allow_html=True)

# Footer
st.markdown("---")
st.caption(f"© 2026 日中コンテナ船追跡アプリ | 最終更新: {current_sim_datetime.strftime('%Y-%m-%d %H:%M')}")
