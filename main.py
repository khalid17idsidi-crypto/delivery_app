import os
import sys

# ضمان قراءة مسار المجلد الحالي مباشرة
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)

from fastapi import FastAPI
from fastapi.responses import HTMLResponse
from fastapi.middleware.cors import CORSMiddleware
from routes import router as api_router

app = FastAPI(title="Delivery Tracking & Routing API - FastAPI Backend")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# تضمين كافة مسارات الـ API المقسمة
app.include_router(api_router)

# ==========================================
# 1. واجهة تطبيق التوصيل الأساسية ( / )
# ==========================================
@app.get("/", response_class=HTMLResponse)
def serve_frontend():
    html_content = """<!DOCTYPE html>
<html lang="ar" dir="rtl" id="htmlRoot">
  <head>
    <meta charset="UTF-8" />
    <meta name="viewport" content="width=device-width, initial-scale=1.0, maximum-scale=1.0, user-scalable=no" />
    <title id="appMetaTitle">نتسخر ليك...كازا - خدمة التوصيل الذكية</title>

    <meta name="theme-color" content="#10b981" />
    <meta name="mobile-web-app-capable" content="yes" />
    <meta name="apple-mobile-web-app-status-bar-style" content="black-translucent" />
    
    <link href="https://fonts.googleapis.com/css2?family=Tajawal:wght@400;600;700;800;900&display=swap" rel="stylesheet" />

    <script src="https://api.mapbox.com/mapbox-gl-js/v2.15.0/mapbox-gl.js"></script>
    <link href="https://api.mapbox.com/mapbox-gl-js/v2.15.0/mapbox-gl.css" rel="stylesheet" />

    <script src="https://api.mapbox.com/mapbox-gl-js/plugins/mapbox-gl-geocoder/v5.0.0/mapbox-gl-geocoder.min.js"></script>
    <link rel="stylesheet" href="https://api.mapbox.com/mapbox-gl-js/plugins/mapbox-gl-geocoder/v5.0.0/mapbox-gl-geocoder.css" type="text/css" />

    <script src="https://unpkg.com/@mapbox/mapbox-gl-language@1.0.1/index.js"></script>
    <script src="https://cdn.jsdelivr.net/npm/@supabase/supabase-js@2.39.8/dist/umd/supabase.min.js"></script>

    <style>
      :root {
        --primary: #10b981; --primary-dark: #059669; --bg-dark: #0f172a; --card-bg: #1e293b;
        --text-main: #f8fafc; --text-muted: #94a3b8; --border: rgba(255, 255, 255, 0.1);
        --danger: #ef4444; --warning: #f59e0b; --accent-green: #a3e635;
      }
      * { box-sizing: border-box; margin: 0; padding: 0; font-family: "Tajawal", sans-serif; text-rendering: optimizeLegibility; }
      body {
        background: var(--bg-dark); color: var(--text-main); display: flex;
        justify-content: center; min-height: 100vh; overflow-y: auto; -webkit-tap-highlight-color: transparent;
        direction: rtl; text-align: right;
      }
      .app-container {
        width: 100%; max-width: 480px; min-height: 100vh; background: var(--bg-dark);
        position: relative; display: flex; flex-direction: column; padding-bottom: 70px;
      }
      .offline-banner { display: none; background: var(--danger); color: white; text-align: center; font-size: 11px; font-weight: bold; padding: 6px; z-index: 1002; }
      .location-overlay {
        position: fixed; top: 0; left: 0; right: 0; bottom: 0; background: var(--bg-dark);
        z-index: 99999; display: flex; flex-direction: column; justify-content: center; align-items: center; padding: 30px; text-align: center;
      }
      .location-icon-box {
        width: 100px; height: 100px; background: rgba(16, 185, 129, 0.1); border: 2px solid var(--primary);
        border-radius: 50%; display: flex; align-items: center; justify-content: center; font-size: 45px;
        margin-bottom: 20px; box-shadow: 0 0 25px rgba(16, 185, 129, 0.3); animation: pulse 2s infinite;
      }
      @keyframes pulse {
        0% { transform: scale(1); box-shadow: 0 0 0 0 rgba(16, 185, 129, 0.4); }
        70% { transform: scale(1.05); box-shadow: 0 0 0 15px rgba(16, 185, 129, 0); }
        100% { transform: scale(1); box-shadow: 0 0 0 0 rgba(16, 185, 129, 0.4); }
      }
      .location-overlay h2 { font-size: 18px; font-weight: 800; color: var(--primary); margin-bottom: 10px; }
      .location-overlay p { font-size: 12px; color: var(--text-muted); line-height: 1.6; margin-bottom: 25px; }
      .app-header {
        background: var(--card-bg); padding: 12px 16px; display: flex;
        justify-content: space-between; align-items: center; border-bottom: 1px solid var(--border); z-index: 1001; position: sticky; top: 0;
      }
      .app-title { font-size: 16px; font-weight: 900; color: var(--primary); display: flex; align-items: center; gap: 8px; cursor: pointer; }
      .hamburger-btn { background: transparent; border: none; color: var(--text-main); font-size: 24px; cursor: pointer; padding: 2px 8px; border-radius: 8px; }
      .driver-status-toggle {
        display: none; align-items: center; background: rgba(255, 255, 255, 0.1);
        border-radius: 20px; padding: 3px 10px; cursor: pointer; font-size: 11px; font-weight: bold;
      }
      .driver-status-toggle.online { background: var(--primary); color: white; }
      .driver-status-toggle.offline { background: var(--danger); color: white; }
      .drawer-overlay {
        position: fixed; top: 0; left: 0; right: 0; bottom: 0; background: rgba(0, 0, 0, 0.6);
        backdrop-filter: blur(4px); z-index: 2000; opacity: 0; visibility: hidden; transition: all 0.3s ease;
      }
      .drawer-overlay.active { opacity: 1; visibility: visible; }
      .side-drawer {
        position: fixed; top: 0; bottom: 0; right: 0; width: 280px; max-width: 80%;
        background: var(--card-bg); z-index: 2001; box-shadow: 0 0 20px rgba(0, 0, 0, 0.5);
        display: flex; flex-direction: column; transform: translateX(100%); transition: transform 0.3s ease-in-out;
      }
      .side-drawer.active { transform: translateX(0); }
      .drawer-header { padding: 20px 16px; background: rgba(16, 185, 129, 0.1); border-bottom: 1px solid var(--border); display: flex; align-items: center; gap: 12px; }
      .drawer-avatar { width: 50px; height: 50px; border-radius: 50%; border: 2px solid var(--primary); object-fit: cover; background: var(--bg-dark); }
      .drawer-user-info { display: flex; flex-direction: column; gap: 2px; }
      .drawer-user-name { font-size: 14px; font-weight: 800; color: var(--primary); }
      .drawer-user-role { font-size: 10px; color: var(--text-muted); }
      .drawer-close-btn { background: transparent; border: none; color: var(--text-muted); font-size: 20px; cursor: pointer; margin-right: auto; }
      .drawer-menu { padding: 12px; display: flex; flex-direction: column; gap: 6px; flex: 1; overflow-y: auto; }
      .drawer-item {
        display: flex; align-items: center; gap: 12px; padding: 12px 14px; border-radius: 12px;
        color: var(--text-main); font-size: 13px; font-weight: 700; cursor: pointer; border: none; background: transparent; width: 100%; text-align: right;
      }
      .drawer-item:hover, .drawer-item.active { background: rgba(16, 185, 129, 0.15); color: var(--primary); }
      .drawer-item.logout { color: var(--danger); margin-top: auto; border-top: 1px solid var(--border); }
      .lang-switcher-box { display: flex; gap: 6px; padding: 8px 12px; background: rgba(255,255,255,0.03); border-radius: 10px; border: 1px solid var(--border); margin-bottom: 8px; align-items: center; justify-content: space-between; }
      .lang-btn { background: transparent; border: 1px solid var(--border); color: var(--text-muted); padding: 4px 10px; border-radius: 6px; font-size: 11px; font-weight: bold; cursor: pointer; }
      .lang-btn.active { background: var(--primary); color: white; border-color: var(--primary); }
      .content-area { flex: 1; position: relative; width: 100%; padding: 16px; }
      .view-panel { display: none; flex-direction: column; width: 100%; }
      .view-panel.active { display: flex; }
      .section-header { font-size: 14px; font-weight: 800; color: var(--primary); margin: 10px 0 8px; text-align: right; }
      .services-grid { display: grid; grid-template-columns: repeat(2, 1fr); gap: 10px; margin-bottom: 14px; }
      .service-card {
        background: rgba(255, 255, 255, 0.04); border: 1px solid var(--border); border-radius: 16px;
        padding: 12px 8px; text-align: center; cursor: pointer; display: flex; flex-direction: column; align-items: center;
      }
      .service-card:hover { background: rgba(16, 185, 129, 0.1); border-color: var(--primary); }
      .service-card .emoji-badge { font-size: 28px; margin-bottom: 4px; }
      .service-card h4 { font-size: 12px; font-weight: 800; color: var(--text-main); }
      .hero-service-card {
        background: linear-gradient(160deg, rgba(16, 185, 129, 0.25), rgba(15, 23, 42, 0.95));
        border: 2px solid var(--primary); border-radius: 20px; padding: 14px 12px;
        display: flex; flex-direction: column; align-items: center; text-align: center; gap: 10px; margin-bottom: 12px;
      }
      .image-wrapper { width: 70px; height: 70px; border-radius: 14px; overflow: hidden; border: 2px solid var(--primary); display: flex; justify-content: center; align-items: center; background: var(--bg-dark); }
      .service-icon { width: 100%; height: 100%; object-fit: cover; }
      .promo-video-container { width: 100%; border-radius: 14px; overflow: hidden; border: 2px solid var(--primary); margin: 10px 0; background: #000; }
      .promo-video-container video { width: 100%; display: block; max-height: 220px; object-fit: cover; }
      .promo-banner {
        background: linear-gradient(135deg, rgba(245, 158, 11, 0.2), rgba(16, 185, 129, 0.2));
        border: 2px dashed var(--warning); border-radius: 16px; padding: 14px; margin-bottom: 15px; text-align: center;
      }
      .promo-banner h3 { color: var(--warning); font-size: 14px; font-weight: 900; margin-bottom: 6px; }
      .promo-banner p { font-size: 11px; color: var(--text-main); line-height: 1.5; margin-bottom: 10px; }
      .btn-order, .btn-submit {
        width: 100%; padding: 14px; background: var(--primary); color: white;
        border: none; border-radius: 14px; font-size: 13px; font-weight: 800; cursor: pointer; text-align: center;
      }
      .map-wrapper { position: relative; width: 100%; margin-bottom: 12px; }
      #map { width: 100%; height: 380px; border-radius: 14px; border: 2px solid var(--primary); cursor: pointer; }
      #clientTrackingMap { width: 100%; height: 400px; border-radius: 14px; border: 1px solid var(--border); margin-top: 10px; }
      #driverActiveMap { width: 100%; height: 350px; border-radius: 14px; border: 1px solid var(--border); margin-bottom: 10px; }
      .gps-btn {
        position: absolute; bottom: 12px; right: 12px; z-index: 1000; background: var(--card-bg);
        border: 1px solid var(--primary); color: var(--primary); padding: 6px 10px; border-radius: 8px; font-size: 11px; font-weight: bold; cursor: pointer;
      }
      .compass-btn {
        position: absolute; top: 12px; right: 12px; z-index: 1000; background: var(--card-bg);
        border: 2px solid var(--warning); color: var(--warning); width: 45px; height: 45px; border-radius: 50%;
        font-size: 20px; display: flex; align-items: center; justify-content: center; cursor: pointer;
      }
      .mapboxgl-ctrl-geocoder { max-width: 100% !important; width: 100% !important; background: var(--card-bg) !important; color: var(--text-main) !important; border-radius: 10px !important; border: 1px solid var(--primary) !important; box-shadow: none !important; font-family: "Tajawal", sans-serif !important; margin-bottom: 10px !important; direction: rtl !important; text-align: right !important; }
      .mapboxgl-ctrl-geocoder input { color: var(--text-main) !important; font-family: "Tajawal", sans-serif !important; padding: 10px 40px 10px 15px !important; direction: rtl !important; text-align: right !important; }
      .mapboxgl-ctrl-geocoder .mapboxgl-ctrl-geocoder--icon { right: 12px !important; left: auto !important; fill: var(--primary) !important; }
      .mapboxgl-ctrl-geocoder .mapboxgl-ctrl-geocoder--icon-search { top: 12px !important; }
      .mapboxgl-ctrl-geocoder .mapboxgl-ctrl-geocoder--pin-right { right: auto !important; left: 10px !important; }
      .mapboxgl-ctrl-geocoder .suggestions { background: var(--card-bg) !important; border: 1px solid var(--border) !important; direction: rtl !important; text-align: right !important; }
      .mapboxgl-ctrl-geocoder .suggestions > li > a { color: var(--text-main) !important; font-family: "Tajawal", sans-serif !important; direction: rtl !important; text-align: right !important; }
      .mapboxgl-ctrl-geocoder .suggestions > li > a:hover { background: rgba(16, 185, 129, 0.2) !important; color: var(--primary) !important; }

      .field-group { margin-bottom: 12px; text-align: right; position: relative; }
      .field-group label { display: block; font-size: 11px; color: var(--text-muted); margin-bottom: 6px; }
      .field-group label span.required { color: var(--danger); font-weight: bold; }
      .field-group input, .field-group select, .field-group textarea {
        width: 100%; padding: 12px; border-radius: 10px; border: 1px solid var(--border);
        background: var(--card-bg); color: var(--text-main); font-size: 12px; outline: none; text-align: right; direction: rtl; font-family: "Tajawal", sans-serif;
      }
      .pin-instruction-box { background: rgba(16, 185, 129, 0.12); border: 1px solid var(--primary); border-radius: 12px; padding: 12px; margin-bottom: 10px; font-size: 12px; color: var(--text-main); text-align: center; line-height: 1.5; }
      .custom-toast-overlay { display: none; position: fixed; top: 0; left: 0; right: 0; bottom: 0; background: rgba(0, 0, 0, 0.7); z-index: 999999; justify-content: center; align-items: center; padding: 20px; }
      .custom-toast-card { background: var(--card-bg); border: 1px solid var(--primary); border-radius: 16px; width: 100%; max-width: 320px; padding: 20px; text-align: center; }
      .indrive-order-card { background: var(--card-bg); border: 1px solid var(--border); border-radius: 16px; padding: 16px; margin-bottom: 14px; box-shadow: 0 4px 15px rgba(0,0,0,0.3); text-align: right; }
      .card-top-info { display: flex; justify-content: space-between; align-items: center; margin-bottom: 12px; padding-bottom: 10px; border-bottom: 1px solid var(--border); }
      .price-badge-indrive { background: rgba(16, 185, 129, 0.15); color: var(--primary); font-size: 15px; font-weight: 900; padding: 4px 12px; border-radius: 10px; }
      .distance-tag { font-size: 11px; font-weight: bold; color: var(--warning); background: rgba(245, 158, 11, 0.1); padding: 4px 10px; border-radius: 8px; }
      .location-row { display: flex; align-items: flex-start; gap: 10px; margin-bottom: 8px; font-size: 12px; line-height: 1.5; color: var(--text-main); text-align: right; }
      .dot-point { width: 10px; height: 10px; border-radius: 50%; margin-top: 5px; flex-shrink: 0; }
      .dot-point.pickup { background: #1e3a8a; box-shadow: 0 0 6px #1e3a8a; }
      .dot-point.delivery { background: var(--danger); box-shadow: 0 0 6px var(--danger); }
      .btn-indrive-action { width: 100%; margin-top: 12px; padding: 12px; background: var(--primary); color: white; border: none; border-radius: 12px; font-size: 13px; font-weight: 800; cursor: pointer; text-align: center; }
      .nav-modal-overlay { display: none; position: fixed; top: 0; left: 0; right: 0; bottom: 0; background: rgba(0,0,0,0.7); z-index: 999999; justify-content: center; align-items: center; padding: 20px; }
      .nav-modal-card { background: var(--card-bg); border: 2px solid var(--primary); border-radius: 18px; width: 100%; max-width: 320px; padding: 20px; text-align: center; }
      .perf-circles-grid { display: grid; grid-template-columns: repeat(3, 1fr); gap: 10px; margin-bottom: 16px; }
      .perf-circle-card { background: linear-gradient(145deg, var(--card-bg), rgba(15, 23, 42, 0.8)); border: 1px solid var(--border); border-radius: 18px; padding: 14px 6px; text-align: center; display: flex; flex-direction: column; align-items: center; justify-content: center; }
      .progress-ring-container { position: relative; width: 85px; height: 85px; display: flex; align-items: center; justify-content: center; margin-bottom: 10px; }
      .progress-ring-svg { width: 85px; height: 85px; transform: rotate(-90deg); }
      .progress-ring-bg { fill: none; stroke: rgba(255,255,255,0.1); stroke-width: 7; }
      .progress-ring-fill { fill: none; stroke-width: 7; stroke-linecap: round; transition: stroke-dashoffset 0.6s ease; }
      .progress-ring-value-box { position: absolute; display: flex; flex-direction: column; align-items: center; justify-content: center; gap: 2px; }
      .progress-ring-value { font-size: 14px; font-weight: 900; color: var(--text-main); }
      .progress-ring-icon { font-size: 14px; }
      .perf-circle-title { font-size: 11px; font-weight: 800; color: var(--text-muted); }
      .earnings-filter-tabs { display: flex; background: rgba(255,255,255,0.05); padding: 4px; border-radius: 12px; margin-bottom: 14px; gap: 4px; }
      .earnings-tab-btn { flex: 1; background: transparent; border: none; color: var(--text-muted); padding: 8px; font-size: 11px; font-weight: bold; border-radius: 8px; cursor: pointer; text-align: center; }
      .earnings-tab-btn.active { background: var(--primary); color: white; }
      .bonus-circles-container { display: flex; gap: 10px; justify-content: center; margin: 12px 0; }
      .bonus-circle {
        width: 85px; height: 85px; border-radius: 50%; border: 2px solid var(--warning);
        background: rgba(245, 158, 11, 0.1); display: flex; flex-direction: column; align-items: center; justify-content: center;
        text-align: center; cursor: pointer; transition: all 0.2s ease;
      }
      .bonus-circle.active, .bonus-circle:hover { background: var(--warning); color: #000; box-shadow: 0 0 15px rgba(245, 158, 11, 0.5); transform: scale(1.05); }
      .bonus-circle .b-val { font-size: 13px; font-weight: 900; }
      .bonus-circle .b-desc { font-size: 10px; font-weight: bold; }
      .role-customer-item, .role-driver-item, .role-admin-item, .visitor-only-item { display: none; }
      .d-none-driver { display: block; }

      .security-box-warning {
        background: rgba(239, 68, 68, 0.15);
        border: 2px solid var(--danger);
        border-radius: 14px;
        padding: 14px;
        margin: 14px 0;
        text-align: right;
      }
      .security-box-warning h4 {
        color: var(--danger);
        font-size: 13px;
        font-weight: 900;
        margin-bottom: 6px;
        display: flex;
        align-items: center;
        gap: 6px;
      }
      .security-box-warning p {
        font-size: 11px;
        line-height: 1.6;
        color: #fca5a5;
        margin-bottom: 10px;
      }
      .security-checkbox-label {
        display: flex;
        align-items: flex-start;
        gap: 8px;
        font-size: 11px;
        font-weight: bold;
        color: var(--warning);
        cursor: pointer;
      }
      .security-checkbox-label input {
        width: 18px;
        height: 18px;
        accent-color: var(--danger);
        margin-top: 2px;
      }
    </style>
  </head>
  <body>
    <div class="app-container">
      <div class="offline-banner" id="offlineBanner">⚠️ أنت تعمل الآن في وضع غير متصل (Offline). سيتم حفظ طلباتك ومزامنتها فور عودة الإنترنت.</div>

      <div class="custom-toast-overlay" id="customToastOverlay">
        <div class="custom-toast-card">
          <h4 id="toastTitle" style="color: var(--primary); margin-bottom: 8px">تنبيه النظام</h4>
          <p id="toastMessage" style="font-size: 12px; margin-bottom: 14px"></p>
          <button class="btn-submit" onclick="closeCustomToast()" id="btnToastOk">حسناً 👍</button>
        </div>
      </div>

      <div class="nav-modal-overlay" id="navModalOverlay" onclick="closeNavModal(event)">
        <div class="nav-modal-card">
          <h3 style="color: var(--primary); margin-bottom: 6px; font-size: 15px;" id="navModalTitle">🧭 توجيه الموصل الفعلي</h3>
          <p style="font-size: 11px; color: var(--text-muted); margin-bottom: 15px;" id="navModalSub">اختر الوجهة المباشرة بناءً على حالة الطلب الحقيقية:</p>
          <button class="btn-submit" style="margin-bottom: 8px; background: #1e3a8a;" onclick="openNavigatorApp('google', 'pickup')">📍 جوجل مابس: الذهاب للاستلام</button>
          <button class="btn-submit" style="margin-bottom: 12px; background: #ef4444;" onclick="openNavigatorApp('google', 'dropoff')">🎯 جوجل مابس: الذهاب للتسليم</button>
          <button class="btn-submit" style="margin-bottom: 8px; background: #0284c7;" onclick="openNavigatorApp('waze', 'pickup')">🚗 وايز: الذهاب للاستلام</button>
          <button class="btn-submit" style="margin-bottom: 12px; background: #f59e0b;" onclick="openNavigatorApp('waze', 'dropoff')">🏁 وايز: الذهاب للتسليم</button>
          <button class="btn-submit" style="background: transparent; color: var(--text-muted);" onclick="closeNavModal()">إلغاء</button>
        </div>
      </div>

      <div class="location-overlay" id="locationOverlay">
        <div class="location-icon-box">📍</div>
        <h2>تفعيل خدمة الموقع مطلوب</h2>
        <p>لتتمكن من استخدام التطبيق وخدمة التوصيل، يرجى السماح بتحديد موقعك الجغرافي الحالي بشكل دقيق.</p>
        <button class="btn-submit" onclick="requestUserLocationPermission()">📍 السماح وتفعيل الموقع الآن</button>
      </div>

      <header class="app-header">
        <div class="app-title" onclick="safeExecute(() => switchMainView('homeView'))">🚀 <span>نتسخر ليك...كازا</span></div>
        <div class="driver-status-toggle offline" id="driverStatusToggle" onclick="safeExecute(toggleDriverOnlineStatus)">
          <span id="driverStatusIcon">🔴</span>
          <span id="driverStatusText" style="margin-right: 4px">غير متصل</span>
        </div>
        <button class="hamburger-btn" onclick="toggleDrawer()">☰</button>
      </header>

      <div class="drawer-overlay" id="drawerOverlay" onclick="toggleDrawer()"></div>
      <aside class="side-drawer" id="sideDrawer">
        <div class="drawer-header">
          <img src="https://cauujrnxtqswjzqhphyq.supabase.co/storage/v1/object/public/assets/1789090107575.png" class="drawer-avatar" id="drawerUserAvatarImg" />
          <div class="drawer-user-info">
            <span class="drawer-user-name" id="drawerUserName">زائر</span>
            <span class="drawer-user-role
