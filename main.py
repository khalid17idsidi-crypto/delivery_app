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
        100% { transform: scale(1); box-shadow: 0 0 0 0 rgba(16, 185, 129, 0); }
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
            <span class="drawer-user-role" id="drawerUserRole">قم بتسجيل الدخول</span>
          </div>
          <button class="drawer-close-btn" onclick="toggleDrawer()">✕</button>
        </div>
        <nav class="drawer-menu">
          <div class="lang-switcher-box">
            <span style="font-size: 11px; font-weight: bold; color: var(--text-muted);">🌐 اللغة / Langue:</span>
            <div style="display: flex; gap: 4px;">
              <button class="lang-btn active" id="langBtnAr" onclick="setAppLanguage('ar')">عربي</button>
              <button class="lang-btn" id="langBtnFr" onclick="setAppLanguage('fr')">Français</button>
            </div>
          </div>
          <button class="drawer-item active" onclick="safeExecute(() => switchMainView('homeView'))"><span>🏠</span> <span>الرئيسية</span></button>
          <button class="drawer-item visitor-only-item" onclick="safeExecute(() => switchMainView('authView'))"><span>🔑</span> <span>تسجيل الدخول</span></button>
          <button class="drawer-item role-customer-item" onclick="safeExecute(() => switchMainView('clientView'))"><span>📦</span> <span>إنشاء طلب جديد بالخريطة</span></button>
          <button class="drawer-item role-customer-item" onclick="safeExecute(() => switchMainView('clientOrdersView'))"><span>🚚</span> <span>تتبع طلباتي النشطة</span></button>
          <button class="drawer-item role-driver-item" onclick="safeExecute(() => switchMainView('driverVerificationView'))"><span>🛡</span> <span id="verificationMenuLabel">توثيق ورفع الوثائق</span></button>
          <button class="drawer-item role-driver-item" onclick="safeExecute(() => switchMainView('ordersView'))"><span>📡</span> <span>الطلبيات الفورية (الرادار)</span></button>
          <button class="drawer-item role-driver-item" onclick="safeExecute(() => switchMainView('performanceView'))"><span>📊</span> <span>لوحة الأداء ومستواي</span></button>
          <button class="drawer-item role-driver-item" onclick="safeExecute(() => switchMainView('earningsView'))"><span>💰</span> <span>الأرباح والسجل</span></button>
          <button class="drawer-item role-driver-item" onclick="safeExecute(() => switchMainView('walletView'))"><span>💼</span> <span>المحفظة والشحن (CIH)</span></button>
          <button class="drawer-item" onclick="safeExecute(() => switchMainView('supportView'))"><span>💬</span> <span>الدعم الفني</span></button>
          <button class="drawer-item logout" id="drawer-logout" style="display: none" onclick="safeExecute(logoutUser)"><span>🚪</span> <span>تسجيل الخروج</span></button>
        </nav>
      </aside>

      <div class="content-area">
        <div id="homeView" class="view-panel active">
          <div class="promo-banner d-none-driver">
            <h3>🏆 مسابقة الشهر لزبناء "نتسخر ليك"!</h3>
            <p>جمع <strong>20 طلب توصيل ناجح خلال الشهر</strong> واربح قسيمة بقيمة <strong>200 درهم</strong>.</p>
            <button class="btn-submit" onclick="safeExecute(() => selectServiceCategory('طرود ووثائق 📦'))" style="padding: 8px; font-size: 11px">إبدأ طلبياتك الآن 🚀</button>
          </div>
          <div class="service-card hero-service-card">
            <div class="image-wrapper"><img src="https://cauujrnxtqswjzqhphyq.supabase.co/storage/v1/object/public/assets/1789090107575.png" alt="نتسخر ليك...كازا" class="service-icon" /></div>
            <div class="service-info">
              <h3 style="color: var(--primary); font-size: 16px; font-weight: 900; margin-bottom: 4px;">نتسخر ليك...كازا</h3>
              <div class="promo-video-container d-none-driver">
                <video autoplay muted loop playsinline preload="auto"><source src="https://cauujrnxtqswjzqhphyq.supabase.co/storage/v1/object/public/assets/mp4.mp4" type="video/mp4" /></video>
              </div>
              <p style="color: var(--text-muted); font-size: 11px; margin-bottom: 10px;">خدمة التوصيل السريعة والمقاضي في الدار البيضاء</p>
              <button class="btn-order" onclick="safeExecute(() => selectServiceCategory('طرود ووثائق 📦'))" style="padding: 10px 20px">إطلب الآن 🚀</button>
            </div>
          </div>
          <div class="section-header">⚡ اختر الخدمة المطلوبة:</div>
          <div class="services-grid">
            <div class="service-card" onclick="safeExecute(() => selectServiceCategory('طرود ووثائق 📦'))"><div class="emoji-badge">📦</div><h4>طرود ووثائق</h4></div>
            <div class="service-card" onclick="safeExecute(() => selectServiceCategory('وجبات طعام 🍔'))"><div class="emoji-badge">🍔</div><h4>وجبات طعام</h4></div>
            <div class="service-card" onclick="safeExecute(() => selectServiceCategory('صيدلية 💊'))"><div class="emoji-badge">💊</div><h4>صيدلية</h4></div>
            <div class="service-card" onclick="safeExecute(() => selectServiceCategory('المتاجر والتسوق 🛒'))"><div class="emoji-badge">🛒</div><h4>المتاجر والتسوق</h4></div>
          </div>
        </div>

        <div id="authView" class="view-panel">
          <div style="display: flex; background: rgba(255, 255, 255, 0.05); padding: 4px; border-radius: 14px; margin-bottom: 15px;">
            <button type="button" id="tabLoginBtn" class="btn-submit" style="background:var(--primary);" onclick="switchAuthMode('login')">تسجيل الدخول 🔑</button>
            <button type="button" id="tabSignupBtn" class="btn-submit" style="background:transparent;" onclick="switchAuthMode('signup')">حساب جديد 🚀</button>
          </div>
          <h3 style="font-size: 14px; margin-bottom: 12px; color: var(--primary)" id="authFormTitle">🔑 تسجيل الدخول لحسابك</h3>
          <div class="field-group" id="groupFullName" style="display: none;"><label>الاسم الكامل <span class="required">*</span>:</label><input type="text" id="authFullName" placeholder="الاسم الكامل" /></div>
          <div class="field-group"><label>البريد الإلكتروني <span class="required">*</span>:</label><input type="email" id="authEmail" placeholder="name@example.com" /></div>
          <div class="field-group" id="groupPhone" style="display: none;"><label>رقم الهاتف الأساسي <span class="required">*</span>:</label><input type="tel" id="authPhone" placeholder="0600000000" /></div>
          <div class="field-group"><label>كلمة المرور <span class="required">*</span>:</label><input type="password" id="authPassword" placeholder="********" /></div>
          <div class="field-group" id="groupRole" style="display: none;">
            <label>الصفة (Role) <span class="required">*</span>:</label>
            <select id="authRole"><option value="customer">زبون (customer - إرسال طلبات توصيل)</option><option value="driver">موصل (driver - تقديم خدمة التوصيل مع رصيد ترحيبي 20 درهم)</option></select>
          </div>
          <button class="btn-submit" id="authSubmitBtn" onclick="safeExecute(handleAuthAction)">🚀 تسجيل الدخول</button>
        </div>

        <div id="driverVerificationView" class="view-panel">
          <h3 style="color: var(--primary); margin-bottom: 8px;">🛡 توثيق حساب الموصل</h3>
          <p style="font-size: 11px; color: var(--text-muted); margin-bottom: 12px;">يرجى رفع الوثائق المطلوبة (البطاقة الوطنية، الصورة الشخصية، وشهادة ملكية الدراجة).</p>
          <div class="field-group"><label>صورة البطاقة الوطنية (CIN) <span class="required">*</span>:</label><input type="file" id="cinFile" accept="image/*" style="background:var(--bg-dark); padding:8px; width:100%; color:white; border:1px dashed var(--primary); border-radius:8px;" /></div>
          <div class="field-group"><label>الصورة الشخصية (Avatar) <span class="required">*</span>:</label><input type="file" id="driverAvatarFile" accept="image/*" capture="user" style="background:var(--bg-dark); padding:8px; width:100%; color:white; border:1px dashed var(--primary); border-radius:8px;" /></div>
          <div class="field-group"><label>شهادة ملكية الدراجة النارية (Carte Grise) <span class="required">*</span>:</label><input type="file" id="vehicleDocFile" accept="image/*,application/pdf" style="background:var(--bg-dark); padding:8px; width:100%; color:white; border:1px dashed var(--primary); border-radius:8px;" /></div>
          <button class="btn-submit" onclick="safeExecute(submitDriverDocuments)">📤 إرسال الوثائق للإدارة للمراجعة</button>
        </div>

        <div id="clientView" class="view-panel">
          <h3 style="font-size: 14px; margin-bottom: 6px; color: var(--primary)">🗺 تحديد موقع الاستلام والتسليم بدقة</h3>
          <div class="pin-instruction-box">📍 <b>تم تحديد موقع الاستلام الحالي (Pickup) تلقائياً عبر GPS.</b> يمكنك تحريك الدبوس الأزرق الداكن لتحديد نقطة الاستلام بدقة إذا لزم الأمر.</div>
          <div id="geocoder-container" style="margin-bottom: 8px;"></div>
          <div class="map-wrapper">
            <div id="map" style="width: 100%; height: 380px; border-radius: 14px; border: 2px solid var(--primary);"></div>
            <button type="button" class="gps-btn" onclick="safeExecute(goToCurrentLocation)">📍 موقعي الحالي (GPS)</button>
          </div>
          <div class="field-group"><label>الفئة المختارة:</label><input type="text" id="orderCategory" readonly value="طرود ووثائق 📦" /></div>
          <div class="field-group"><label>الإحداثيات الدقيقة لموقع الاستلام (Pickup):</label><input type="text" id="deliveryCoordsDisplay" readonly style="color: var(--accent-green); font-weight: bold; text-align: center;" value="جاري تحديد موقعك عبر GPS..." /></div>
          
          <div class="field-group">
            <label>رقم هاتف المستلم الأول (إلزامي) <span class="required">*</span>:</label>
            <input type="tel" id="recipientPhone" placeholder="0600000000" required />
          </div>

          <div class="field-group">
            <label>رقم هاتف المستلم الإضافي / الثاني (إلزامي للتسليم) <span class="required">*</span>:</label>
            <input type="tel" id="recipientPhoneSecondary" placeholder="0700000000" required />
          </div>

          <div class="field-group"><label>وصف الطرد أو محتوى الشحنة تفصيلياً <span class="required">*</span>:</label><textarea id="parcelDescription" rows="3" placeholder="اكتب وصفاً واضحاً ومفصلاً للطرد..."></textarea></div>

          <div class="security-box-warning">
            <h4>🚨 إشعار أمني وقانوني صارم</h4>
            <p>
              يمنع منعاً كلياً استغلال منصة التوصيل لنقل أو حيازة أي مواد ممنوعة قانوناً أو مخدرات أو مؤثرات عقلية.
              <strong>يمنح التطبيق للأجهزة الأمنية والشرطة القضائية الصلاحية الفورية لمراجعة وتسليم كافة البيانات الرقمية، أرقام الهواتف، تسجيلات GPS ومسارات النقل عند أي اشتباه.</strong>
            </p>
            <label class="security-checkbox-label">
              <input type="checkbox" id="securityAcceptedCheckbox" required />
              <span>أوافق صراحة على الشروط الأمنية وأتحمل كامل المسؤولية القانونية والجنائية عن محتوى الطرد.</span>
            </label>
          </div>

          <button class="btn-submit" onclick="safeExecute(createNewOrder)">🚀 إرسال الطلب وحساب السعر المضبوط</button>
        </div>

        <div id="clientOrdersView" class="view-panel">
          <h3 style="font-size: 14px; margin-bottom: 10px; color: var(--primary)">🛵 التتبع الحي المباشر لموقع الموصل (مثل inDrive)</h3>
          <div id="clientTrackingMap" style="width: 100%; height: 400px; border-radius: 14px; border: 1px solid var(--border); margin-top: 10px;"></div>
          <div id="clientOrdersListContainer" style="margin-top: 10px;"><p style="font-size: 11px; color: var(--text-muted)">جاري جلب تفاصيل التتبع الحي من قاعدة البيانات...</p></div>
        </div>

        <div id="ordersView" class="view-panel">
          <h3 style="font-size: 14px; margin-bottom: 10px; color: var(--primary)">📡 رادار الطلبات والخرائط التوجيهية</h3>
          <div id="driverActiveOrderContainer" style="display: none;">
            <div class="map-wrapper">
              <div id="driverActiveMap" style="width: 100%; height: 350px; border-radius: 14px; border: 1px solid var(--border); margin-bottom: 10px;"></div>
              <button type="button" class="compass-btn" onclick="openNavSelectionModal()" title="فتح في Waze / Google Maps">🧭</button>
            </div>
            <div id="driverActiveOrderDetails"></div>
          </div>
          <div id="ordersListContainer"><p style="font-size: 11px; color: var(--text-muted)">جاري تحميل الطلبات المتاحة في الرادار...</p></div>
        </div>

        <div id="performanceView" class="view-panel">
          <h3 style="color: var(--primary); font-size: 15px; margin-bottom: 14px;">📊 لوحة الأداء والمستويات الاحترافية</h3>
          <div class="perf-circles-grid">
            <div class="perf-circle-card">
              <div class="progress-ring-container">
                <svg class="progress-ring-svg" viewBox="0 0 36 36">
                  <path class="progress-ring-bg" d="M18 2.0845 a 15.9155 15.9155 0 0 1 0 31.831 a 15.9155 15.9155 0 0 1 0 -31.831" />
                  <path id="circleOrdersFill" class="progress-ring-fill" stroke="#10b981" stroke-dasharray="0, 100" d="M18 2.0845 a 15.9155 15.9155 0 0 1 0 31.831 a 15.9155 15.9155 0 0 1 0 -31.831" />
                </svg>
                <div class="progress-ring-value-box"><span class="progress-ring-icon">📦</span><span class="progress-ring-value" id="valOrdersCount">0</span></div>
              </div>
              <span class="perf-circle-title">طلبات اليوم</span>
            </div>
            <div class="perf-circle-card">
              <div class="progress-ring-container">
                <svg class="progress-ring-svg" viewBox="0 0 36 36">
                  <path class="progress-ring-bg" d="M18 2.0845 a 15.9155 15.9155 0 0 1 0 31.831 a 15.9155 15.9155 0 0 1 0 -31.831" />
                  <path id="circleEvalFill" class="progress-ring-fill" stroke="#10b981" stroke-dasharray="96, 100" d="M18 2.0845 a 15.9155 15.9155 0 0 1 0 31.831 a 15.9155 15.9155 0 0 1 0 -31.831" />
                </svg>
                <div class="progress-ring-value-box"><span class="progress-ring-icon">⭐</span><span class="progress-ring-value" id="valEvalScore">4.8</span></div>
              </div>
              <span class="perf-circle-title">التقييم العام</span>
            </div>
            <div class="perf-circle-card">
              <div class="progress-ring-container">
                <svg class="progress-ring-svg" viewBox="0 0 36 36">
                  <path class="progress-ring-bg" d="M18 2.0845 a 15.9155 15.9155 0 0 1 0 31.831 a 15.9155 15.9155 0 0 1 0 -31.831" />
                  <path id="circleCancelFill" class="progress-ring-fill" stroke="#10b981" stroke-dasharray="0, 100" d="M18 2.0845 a 15.9155 15.9155 0 0 1 0 31.831 a 15.9155 15.9155 0 0 1 0 -31.831" />
                </svg>
                <div class="progress-ring-value-box"><span class="progress-ring-icon">⚠</span><span class="progress-ring-value" id="valCancelRate">0%</span></div>
              </div>
              <span class="perf-circle-title">نسبة الإلغاء</span>
            </div>
          </div>
          <div class="indrive-order-card" style="margin-top: 10px;">
            <h4 style="color: var(--primary); font-size: 13px; margin-bottom: 6px;">💡 إرشادات الموصل الاحترافي:</h4>
            <p style="font-size: 11px; color: var(--text-muted); line-height: 1.6;">التزم بقبول الطلبات وسرعة إيصالها لرفع تقييمك للأفضل وتفادي أي إلغاءات غير مبررة.</p>
          </div>
        </div>

        <div id="earningsView" class="view-panel">
          <h3 style="color: var(--primary); font-size: 15px; margin-bottom: 12px;">💰 الأرباح والسجل المالي</h3>
          <div class="earnings-filter-tabs">
            <button class="earnings-tab-btn active" onclick="switchEarningsPeriod('day', this)">اليوم</button>
            <button class="earnings-tab-btn" onclick="switchEarningsPeriod('week', this)">الأسبوع</button>
            <button class="earnings-tab-btn" onclick="switchEarningsPeriod('month', this)">الشهر</button>
          </div>
          <div class="indrive-order-card" style="text-align: center; padding: 18px; background: linear-gradient(135deg, rgba(16,185,129,0.15), var(--card-bg));">
            <span style="font-size: 12px; color: var(--text-muted);" id="earningsPeriodLabel">إجمالي دخل اليوم</span>
            <div style="font-size: 26px; font-weight: 900; color: var(--primary); margin: 6px 0;" id="earningsTotalAmount">0.00 MAD</div>
            <div style="display: flex; justify-content: space-around; margin-top: 12px; border-top: 1px solid var(--border); padding-top: 10px; font-size: 11px;">
              <div>📦 عدد الطلبات: <strong id="earningsOrdersCount">0</strong></div>
              <div>🛣 المسافة: <strong id="earningsTotalKm">0 كم</strong></div>
              <div>⚡ الثمن/كم: <strong id="earningsPricePerKm">0 MAD</strong></div>
            </div>
            <div style="margin-top: 8px; font-size: 11px; color: var(--warning);">📉 اقتطاع التطبيق (10%): <strong id="earningsAppFee">0.00 MAD</strong></div>
          </div>
          <button class="btn-submit" style="background: rgba(255,255,255,0.08); border: 1px solid var(--primary); margin: 10px 0; font-size: 12px;" onclick="safeExecute(toggleEarningsHistoryDisplay)">📜 عرض سجل الطلبات الكامل</button>
          <div id="earningsOrdersListContainer" style="display: none; margin-top: 10px;"><p style="font-size: 11px; color: var(--text-muted); text-align: center; padding: 10px;">جاري تحميل سجلك الحقيقي للطلبات...</p></div>
        </div>

        <div id="walletView" class="view-panel">
          <div class="wallet-box" style="background: var(--card-bg); border: 1px solid var(--border); padding: 14px; border-radius: 12px; margin-bottom: 12px; display: flex; justify-content: space-between; align-items: center;">
            <span style="font-size: 13px; font-weight: bold">💳 رصيد المحفظة الحالي:</span>
            <span id="driverWalletBalance" style="font-size: 18px; font-weight: 900; color: var(--primary)">0.00 MAD</span>
          </div>
          <div class="bonus-badge" style="background: rgba(245, 158, 11, 0.1); border: 1px dashed var(--warning); padding: 10px; border-radius: 10px; font-size: 11px; margin-bottom: 12px;">🎁 <b>عروض الشحن (CIH):</b> الحد الأدنى للشحن هو 30 درهم. اختر عروض البونيس أدناه لتفعيلها تلقائياً:</div>
          
          <div class="bonus-circles-container">
            <div class="bonus-circle" onclick="selectBonusOffer(50, this)">
              <span class="b-val">50 MAD</span>
              <span class="b-desc">🎁 +4 د بونيس</span>
            </div>
            <div class="bonus-circle" onclick="selectBonusOffer(100, this)">
              <span class="b-val">100 MAD</span>
              <span class="b-desc">⭐ +10 د بونيس</span>
            </div>
          </div>

          <div class="field-group" style="margin-top: 10px;"><label>مبلغ الشحن المرغوب (الحد الأدنى 30 درهم) <span class="required">*</span>:</label><input type="number" id="walletRechargeAmount" placeholder="مثال: 50 أو 100" /></div>
          <div class="field-group"><label>مرجع التحويل البنكي CIH (إن وجد):</label><input type="text" id="receiptTextRef" placeholder="أدخل رقم أو مرجع التحويل" /></div>
          
          <div class="field-group">
            <label>📸 التقاط صورة وصل التحويل بالكاميرا (إلزامي) <span class="required">*</span>:</label>
            <input type="file" id="receiptImageFile" accept="image/*" capture="environment" style="background:var(--bg-dark); padding:10px; width:100%; color:white; border:2px dashed var(--primary); border-radius:10px;" />
          </div>

          <button class="btn-submit" onclick="safeExecute(submitRealWalletTopupRequest)">📷 التقاط وإرسال صورة الوصل للاعتماد</button>
        </div>

        <div id="supportView" class="view-panel">
          <h3 style="font-size: 14px; margin-bottom: 12px; color: var(--primary)">💬 الدعم الفني والخدمة</h3>
          <div class="field-group"><textarea id="supportMessage" rows="4" placeholder="اكتب تفاصيل مشكلتك..."></textarea></div>
          <button class="btn-submit" onclick="safeExecute(() => showAppToast('تم الإرسال', 'تم إرسال شكواك للادارة بنجاح!'))">📨 إرسال للادارة</button>
        </div>
      </div>

      <nav class="driver-bottom-nav" id="driverBottomNav" style="display: none; position: fixed; bottom: 0; left: 0; right: 0; background: var(--card-bg); border-top: 1px solid var(--border); padding: 8px; justify-content: space-around; z-index: 1000;">
        <button class="nav-item active" onclick="safeExecute(() => switchMainView('ordersView'))" style="background: transparent; border: none; color: var(--text-main); display: flex; flex-direction: column; align-items: center; font-size: 10px; cursor: pointer;"><span style="font-size: 18px;">📡</span><span>الرادار</span></button>
        <button class="nav-item" onclick="safeExecute(() => switchMainView('performanceView'))" style="background: transparent; border: none; color: var(--text-main); display: flex; flex-direction: column; align-items: center; font-size: 10px; cursor: pointer;"><span style="font-size: 18px;">📊</span><span>الأداء</span></button>
        <button class="nav-item" onclick="safeExecute(() => switchMainView('earningsView'))" style="background: transparent; border: none; color: var(--text-main); display: flex; flex-direction: column; align-items: center; font-size: 10px; cursor: pointer;"><span style="font-size: 18px;">💰</span><span>الأرباح</span></button>
        <button class="nav-item" onclick="safeExecute(() => switchMainView('walletView'))" style="background: transparent; border: none; color: var(--text-main); display: flex; flex-direction: column; align-items: center; font-size: 10px; cursor: pointer;"><span style="font-size: 18px;">💼</span><span>المحفظة</span></button>
      </nav>
    </div>

    <script>
      function safeExecute(fn) { try { if (typeof fn === 'function') fn(); } catch (error) { console.error("Execution Error:", error); } }

      const SUPABASE_URL = "https://cauujrnxtqswjzqhphyq.supabase.co";
      const SUPABASE_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6ImNhdXVqcm54dHFzd2p6cWhwaHlxIiwicm9sZSI6InNlcnZpY2Vfcm9sZSIsImlhdCI6MTc4ODM0MTA0MywiZXhwIjoyMTAzOTE3MDQzfQ.17AG1uMHj14ZNVuzp56-9_Z2KYeG50Oo3k__kDbhUok";
      const supabaseClient = supabase.createClient(SUPABASE_URL, SUPABASE_KEY);

      mapboxgl.accessToken = 'pk.eyJ1IjoiaWRzaWRpIiwiYSI6ImNtdTJscHkybjAwbW8yeXF1cXFhdXozaWMifQ.FDKkwkz9kdug1cghlLNChw';

      if (mapboxgl.setRTLTextPlugin) {
        mapboxgl.setRTLTextPlugin(
          'https://api.mapbox.com/mapbox-gl-js/plugins/mapbox-gl-rtl-text/v0.2.3/mapbox-gl-rtl-text.js',
          null,
          true
        );
      }

      let currentUserId = localStorage.getItem("app_user_id") || null;
      let currentUserName = localStorage.getItem("app_user_name") || "";
      let currentRole = localStorage.getItem("app_user_role") || "";
      let currentUserPhone = localStorage.getItem("app_user_phone") || "";

      let userCurrentLat = 33.5731, userCurrentLng = -7.5898;
      let deliveryLat = null, deliveryLng = null;
      let mapboxInstance = null, deliveryMarker = null, trackingMapInstance = null, trackingDriverMarker = null;
      let driverActiveMapInstance = null, driverActiveMarker = null, currentActiveOrder = null;
      let currentAuthMode = 'login', wakeLockInstance = null;
      let radarOrdersCache = [], radarInterval = null, clientTrackingInterval = null, driverLocationUpdateInterval = null;

      function selectBonusOffer(amount, el) {
        document.getElementById('walletRechargeAmount').value = amount;
        document.querySelectorAll('.bonus-circle').forEach(c => c.classList.remove('active'));
        if (el) el.classList.add('active');
      }

      function formatShortAddress(fullAddress) {
        if (!fullAddress) return 'العنوان غير متوفر';
        const parts = fullAddress.split(',');
        return parts.length > 1 ? `${parts[0].trim()},${parts[1].trim()}` : fullAddress;
      }

      function calculateDistanceMeters(lat1, lon1, lat2, lon2) {
        const R = 6371e3;
        const φ1 = lat1 * Math.PI/180;
        const φ2 = lat2 * Math.PI/180;
        const Δφ = (lat2-lat1) * Math.PI/180;
        const Δλ = (lon2-lon1) * Math.PI/180;
        const a = Math.sin(Δφ/2) * Math.sin(Δφ/2) + Math.cos(φ1) * Math.cos(φ2) * Math.sin(Δλ/2) * Math.sin(Δλ/2);
        const c = 2 * Math.atan2(Math.sqrt(a), Math.sqrt(1-a));
        return R * c;
      }

      async function drawMapboxRoute(mapObj, startLng, startLat, endLng, endLat, layerId = 'route-layer', lineColor = '#1e3a8a') {
        if (!mapObj || !startLng || !startLat || !endLng || !endLat) return;
        try {
          const response = await fetch('/api/get-live-route', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ start_lng: startLng, start_lat: startLat, end_lng: endLng, end_lat: endLat })
          });
          const result = await response.json();
          if (result.status === 'success') {
            const geojson = { type: 'Feature', properties: {}, geometry: result.route_geometry };
            if (mapObj.getSource(layerId)) {
              mapObj.getSource(layerId).setData(geojson);
            } else {
              if (!mapObj.isStyleLoaded()) {
                mapObj.on('load', () => drawMapboxRoute(mapObj, startLng, startLat, endLng, endLat, layerId, lineColor));
                return;
              }
              mapObj.addSource(layerId, { type: 'geojson', data: geojson });
              mapObj.addLayer({
                id: layerId, type: 'line', source: layerId,
                layout: { 'line-join': 'round', 'line-cap': 'round' },
                paint: { 'line-color': lineColor, 'line-width': 6, 'line-opacity': 0.9 }
              });
            }
          }
        } catch (e) { console.error("Mapbox Route Error:", e); }
      }

      async function requestScreenWakeLock() {
        if ('wakeLock' in navigator) {
          try { wakeLockInstance = await navigator.wakeLock.request('screen'); } catch (err) {}
        }
      }
      function releaseScreenWakeLock() { if (wakeLockInstance) { wakeLockInstance.release(); wakeLockInstance = null; } }

      function setAppLanguage(lang) {
        localStorage.setItem("app_lang", lang);
        document.getElementById("htmlRoot").setAttribute("lang", lang);
        document.getElementById("htmlRoot").setAttribute("dir", lang === 'ar' ? 'rtl' : 'ltr');
      }

      function requestUserLocationPermission() {
        const overlay = document.getElementById("locationOverlay");
        if (!navigator.geolocation) {
          if (overlay) overlay.style.display = "none";
          showAppToast("تنبيه", "ميزة تحديد الموقع غير مدعومة في متصفحك.");
          return;
        }
        navigator.geolocation.getCurrentPosition(pos => {
          userCurrentLat = pos.coords.latitude;
          userCurrentLng = pos.coords.longitude;
          if (overlay) overlay.style.display = "none";
          if (mapboxInstance) {
            mapboxInstance.resize();
            mapboxInstance.setCenter([userCurrentLng, userCurrentLat]);
          }
          showAppToast("تم بنجاح 📍", "تم تحديد موقعك الجغرافي بنجاح.");
        }, (err) => {
          if (overlay) overlay.style.display = "none";
          showAppToast("تنبيه موقع GPS", "يرجى السماح بالوصول للموقع من إعدادات المتصفح.");
        }, { enableHighAccuracy: true });
      }

      function toggleDrawer() {
        document.getElementById("sideDrawer").classList.toggle("active");
        document.getElementById("drawerOverlay").classList.toggle("active");
      }

      function switchMainView(viewId) {
        document.querySelectorAll(".view-panel").forEach(p => p.classList.remove("active"));
        const targetView = document.getElementById(viewId);
        if (targetView) targetView.classList.add("active");
        const drawer = document.getElementById("sideDrawer");
        const overlay = document.getElementById("drawerOverlay");
        if (drawer && drawer.classList.contains("active")) { drawer.classList.remove("active"); overlay.classList.remove("active"); }
        window.scrollTo({ top: 0, behavior: 'smooth' });

        if (viewId === 'ordersView' && currentRole === 'driver') {
          checkDriverActiveOrder();
          if (!radarInterval) radarInterval = setInterval(() => { if (currentRole === 'driver' && document.getElementById('ordersView').classList.contains('active')) checkDriverActiveOrder(); }, 5000);
          startDriverLiveLocationTracking();
        } else {
          if (radarInterval) { clearInterval(radarInterval); radarInterval = null; }
          if (driverLocationUpdateInterval) { clearInterval(driverLocationUpdateInterval); driverLocationUpdateInterval = null; }
        }

        if (viewId === 'clientOrdersView' && currentRole === 'customer') {
          setTimeout(() => initMapboxClientTracking(), 300);
          if (!clientTrackingInterval) clientTrackingInterval = setInterval(() => { if (currentRole === 'customer' && document.getElementById('clientOrdersView').classList.contains('active')) updateMapboxClientLiveTracking(); }, 4000);
        } else {
          if (clientTrackingInterval) { clearInterval(clientTrackingInterval); clientTrackingInterval = null; }
        }

        if (viewId === 'clientView') setTimeout(() => initMapboxClientMap(), 300);
        if (viewId === 'performanceView') loadDriverPerformanceRealData();
        if (viewId === 'earningsView') loadDriverEarningsRealData('day');
        if (viewId === 'walletView') fetchDriverWalletBalance();
      }

      async function loadDriverPerformanceRealData() {
        if (!currentUserId || currentRole !== 'driver') return;
        try {
          const { data: orders } = await supabaseClient.from('orders').select('*').eq('driver_id', currentUserId);
          const allOrders = orders || [];
          const todayStr = new Date().toISOString().split('T')[0];
          const countToday = allOrders.filter(o => o.status === 'completed' && o.updated_at && o.updated_at.startsWith(todayStr)).length;
          document.getElementById('valOrdersCount').innerText = countToday;
          document.getElementById('circleOrdersFill').style.strokeDasharray = `${Math.min((countToday / 15) * 100, 100)}, 100`;
          document.getElementById('valEvalScore').innerText = allOrders.length > 0 ? '4.9' : '4.8';
          const cancelledCount = allOrders.filter(o => o.status === 'cancelled').length;
          const cancelRate = allOrders.length > 0 ? Math.round((cancelledCount / allOrders.length) * 100) : 0;
          document.getElementById('valCancelRate').innerText = cancelRate + '%';
        } catch (e) {}
      }

      async function loadDriverEarningsRealData(period) {
        if (!currentUserId || currentRole !== 'driver') return;
        try {
          const { data: orders } = await supabaseClient.from('orders').select('*').eq('driver_id', currentUserId).eq('status', 'completed');
          const allCompleted = orders || [];
          const now = new Date();
          const filteredOrders = allCompleted.filter(o => {
            if (!o.created_at) return false;
            const d = new Date(o.created_at);
            if (period === 'day') return d.toDateString() === now.toDateString();
            if (period === 'week') return Math.abs(now - d) / (1000 * 60 * 60 * 24) <= 7;
            return d.getMonth() === now.getMonth();
          });
          let totalEarnings = 0, totalKm = 0;
          filteredOrders.forEach(o => { totalEarnings += parseFloat(o.price_mad || 25); totalKm += parseFloat(o.distance_km || 3.2); });
          document.getElementById('earningsTotalAmount').innerText = `${totalEarnings.toFixed(2)} MAD`;
          document.getElementById('earningsOrdersCount').innerText = filteredOrders.length;
          document.getElementById('earningsTotalKm').innerText = `${totalKm.toFixed(1)} كم`;
          document.getElementById('earningsAppFee').innerText = `${(totalEarnings * 0.10).toFixed(2)} MAD`;
        } catch (e) {}
      }

      function switchEarningsPeriod(period, btnEl) {
        document.querySelectorAll('.earnings-tab-btn').forEach(b => b.classList.remove('active'));
        if (btnEl) btnEl.classList.add('active');
        loadDriverEarningsRealData(period);
      }

      function toggleEarningsHistoryDisplay() {
        const c = document.getElementById('earningsOrdersListContainer');
        c.style.display = (c.style.display === 'none' || !c.style.display) ? 'block' : 'none';
      }

      function startDriverLiveLocationTracking() {
        if (!navigator.geolocation) return;
        if (driverLocationUpdateInterval) clearInterval(driverLocationUpdateInterval);
        driverLocationUpdateInterval = setInterval(() => {
          navigator.geolocation.getCurrentPosition(async pos => {
            userCurrentLat = pos.coords.latitude; 
            userCurrentLng = pos.coords.longitude;
            if (currentUserId && currentRole === 'driver') {
              try {
                if (currentActiveOrder && currentActiveOrder.id) {
                  await supabaseClient.from('orders').update({
                    driver_lat: userCurrentLat,
                    driver_lng: userCurrentLng
                  }).eq('id', currentActiveOrder.id);
                  
                  const targetNavLat = (currentActiveOrder.status === 'assigned') ? currentActiveOrder.pickup_lat : currentActiveOrder.dropoff_lat;
                  const targetNavLng = (currentActiveOrder.status === 'assigned') ? currentActiveOrder.pickup_lng : currentActiveOrder.dropoff_lng;
                  if (driverActiveMapInstance && targetNavLat && targetNavLng) {
                    driverActiveMapInstance.setCenter([userCurrentLng, userCurrentLat]);
                    if (driverActiveMarker) driverActiveMarker.setLngLat([userCurrentLng, userCurrentLat]);
                    drawMapboxRoute(driverActiveMapInstance, userCurrentLng, userCurrentLat, targetNavLng, targetNavLat, 'driver-route', '#1e3a8a');
                  }
                }
                await supabaseClient.rpc('update_driver_status', { p_driver_id: currentUserId, p_lat: userCurrentLat, p_lng: userCurrentLng, p_online: true });
              } catch (e) { console.error("Driver location update error:", e); }
            }
          }, () => {}, { enableHighAccuracy: true });
        }, 4000);
      }

      function selectServiceCategory(categoryName) {
        document.getElementById("orderCategory").value = categoryName;
        if (currentUserId) {
          if (currentRole === 'driver') { showAppToast("تنبيه", "أنت مسجل بحساب موصل."); switchMainView('ordersView'); }
          else { switchMainView('clientView'); }
        } else { switchMainView('authView'); }
      }

      async function toggleDriverOnlineStatus() {
        if (!currentUserId || currentRole !== 'driver') return;
        const toggleBtn = document.getElementById("driverStatusToggle");
        const newStatus = !toggleBtn.classList.contains("online");
        try {
          await supabaseClient.rpc('update_driver_status', { p_driver_id: currentUserId, p_lat: userCurrentLat, p_lng: userCurrentLng, p_online: newStatus });
          if (newStatus) {
            toggleBtn.classList.remove("online"); toggleBtn.classList.add("online");
            document.getElementById("driverStatusText").innerText = "متصل الآن 🟢";
            await requestScreenWakeLock(); checkDriverActiveOrder();
          } else {
            toggleBtn.classList.remove("online"); toggleBtn.classList.add("offline");
            document.getElementById("driverStatusText").innerText = "غير متصل 🔴";
            releaseScreenWakeLock();
          }
        } catch (err) { showAppToast("خطأ", err.message); }
      }

      async function checkDriverActiveOrder() {
        if (currentRole !== 'driver') return;
        try {
          const { data: orders } = await supabaseClient.from('orders').select('*').eq('driver_id', currentUserId).in('status', ['assigned', 'picked_up']);
          const container = document.getElementById("ordersListContainer");
          const activeContainer = document.getElementById("driverActiveOrderContainer");
          if (orders && orders.length > 0) {
            currentActiveOrder = orders[0];
            activeContainer.style.display = "block"; container.style.display = "none";
            renderDriverActiveOrderView(currentActiveOrder);
          } else {
            currentActiveOrder = null;
            activeContainer.style.display = "none"; container.style.display = "block";
            fetchRadarOrders();
          }
        } catch (e) { fetchRadarOrders(); }
      }

      async function fetchRadarOrders() {
        if (currentRole !== 'driver' || currentActiveOrder) return;
        try {
          const { data: orders } = await supabaseClient.from('orders').select('*').or('status.eq.pending,driver_id.is.null');
          radarOrdersCache = (orders || []).map(o => ({ ...o, calculatedDist: 1.5 }));
          renderDriverRadarOrders(radarOrdersCache);
        } catch (e) { renderDriverRadarOrders([]); }
      }

      function renderDriverActiveOrderView(order) {
        const detailsContainer = document.getElementById("driverActiveOrderDetails");
        const pLat = order.pickup_lat || userCurrentLat, pLng = order.pickup_lng || userCurrentLng;
        const dLat = order.dropoff_lat || userCurrentLat, dLng = order.dropoff_lng || userCurrentLng;
        
        const targetNavLat = (order.status === 'assigned') ? pLat : dLat;
        const targetNavLng = (order.status === 'assigned') ? pLng : dLng;

        let statusTextAr = order.status === 'assigned' ? '📦 في الطريق لاستلام الطرد' : '🚀 جاري التوصيل لنقطة التسليم للزبون';

        let btnHtml = (order.status === 'assigned') ? 
          `<button class="btn-indrive-action" onclick="updateOrderStatus('${order.id}', 'picked_up')">📍 تأكيد الوصول والاستلام</button>` :
          `<button class="btn-indrive-action" style="background:var(--warning);" onclick="updateOrderStatus('${order.id}', 'completed')">🏁 إتمام الطلب وتسليم الشحنة</button>`;

        detailsContainer.innerHTML = `
          <div class="indrive-order-card" style="margin-bottom:0;">
            <div class="card-top-info"><span class="price-badge-indrive">${order.price_mad || 20} MAD</span><span class="distance-tag">${statusTextAr}</span></div>
            <div class="location-row"><span class="dot-point pickup"></span><span><b>الاستلام:</b> ${formatShortAddress(order.pickup_address)}</span></div>
            <div class="location-row"><span class="dot-point delivery"></span><span><b>التسليم:</b> ${formatShortAddress(order.dropoff_address)}</span></div>${btnHtml}
          </div>
        `;
        document.getElementById("driverActiveOrderContainer").style.display = "block";
        document.getElementById("ordersListContainer").style.display = "none";
        setTimeout(() => {
          initMapboxDriverActiveMap(targetNavLng, targetNavLat);
          drawMapboxRoute(driverActiveMapInstance, userCurrentLng, userCurrentLat, targetNavLng, targetNavLat, 'driver-route', '#1e3a8a');
        }, 200);
      }

      function initMapboxDriverActiveMap(lng, lat) {
        if (!driverActiveMapInstance) {
          driverActiveMapInstance = new mapboxgl.Map({
            container: 'driverActiveMap',
            style: 'mapbox://styles/mapbox/streets-v12',
            center: [lng || userCurrentLng, lat || userCurrentLat],
            zoom: 15
          });
          if (typeof MapboxLanguage !== 'undefined') {
            driverActiveMapInstance.addControl(new MapboxLanguage({ defaultLanguage: 'ar' }));
          }
          const el = document.createElement('div');
          el.innerHTML = '<div style="background:#1e3a8a; color:white; padding:6px 10px; border-radius:50px; font-size:16px; box-shadow:0 0 12px rgba(30,58,138,0.6); display:flex; align-items:center; gap:4px; font-weight:bold;">🛵</div>';
          driverActiveMarker = new mapboxgl.Marker(el).setLngLat([userCurrentLng, userCurrentLat]).addTo(driverActiveMapInstance);
        } else {
          driverActiveMapInstance.resize();
          driverActiveMapInstance.setCenter([lng, lat]);
        }
      }

      function openNavSelectionModal() { document.getElementById("navModalOverlay").style.display = "flex"; }
      function closeNavModal(e) { if (!e || e.target.id === 'navModalOverlay' || e.target.tagName === 'BUTTON') document.getElementById("navModalOverlay").style.display = "none"; }
      
      function openNavigatorApp(type, destinationType) {
        closeNavModal();
        if (!currentActiveOrder) { 
          showAppToast("تنبيه", "لا يوجد طلب نشط حالياً."); 
          return; 
        }
        
        let destLat = destinationType === 'pickup' ? currentActiveOrder.pickup_lat : currentActiveOrder.dropoff_lat;
        let destLng = destinationType === 'pickup' ? currentActiveOrder.pickup_lng : currentActiveOrder.dropoff_lng;
        
        if (!destLat || !destLng) { 
          showAppToast("تنبيه GPS", "إحداثيات الوجهة غير متوفرة في هذا الطلب."); 
          return; 
        }
        
        let url = type === 'waze' ? 
          `https://waze.com/ul?ll=${destLat},${destLng}&navigate=yes` : 
          `https://www.google.com/maps/dir/?api=1&destination=${destLat},${destLng}&travelmode=driving`;
        
        window.open(url, '_blank');
      }

      async function updateOrderStatus(orderId, newStatus) {
        try {
          if (currentActiveOrder) {
            const targetLat = (newStatus === 'picked_up') ? currentActiveOrder.pickup_lat : currentActiveOrder.dropoff_lat;
            const targetLng = (newStatus === 'picked_up') ? currentActiveOrder.pickup_lng : currentActiveOrder.dropoff_lng;
            if (targetLat && targetLng) {
              const distanceMeters = calculateDistanceMeters(userCurrentLat, userCurrentLng, targetLat, targetLng);
              if (distanceMeters > 250) {
                showAppToast("تنبيه GPS 🚫", `لا يمكنك تأكيد العملية! أنت تبعد عن النقطة بـ ${Math.round(distanceMeters)} متر.`);
                return;
              }
            }
          }
          await supabaseClient.from('orders').update({ status: newStatus, driver_id: (newStatus==='completed'? currentUserId : undefined) }).eq('id', orderId);
          showAppToast("تم بنجاح ✅", "تم تحديث حالة الطلب ومسار التوجيه.");
          checkDriverActiveOrder();
        } catch (e) { showAppToast("خطأ", e.message); }
      }

      async function initMapboxClientTracking() {
        if (!trackingMapInstance) {
          trackingMapInstance = new mapboxgl.Map({
            container: 'clientTrackingMap',
            style: 'mapbox://styles/mapbox/streets-v12',
            center: [userCurrentLng, userCurrentLat],
            zoom: 15
          });
          if (typeof MapboxLanguage !== 'undefined') {
            trackingMapInstance.addControl(new MapboxLanguage({ defaultLanguage: 'ar' }));
          }
        } else {
          trackingMapInstance.resize();
        }
        await updateMapboxClientLiveTracking();
      }

      async function updateMapboxClientLiveTracking() {
        const container = document.getElementById("clientOrdersListContainer");
        if (currentRole !== 'customer' || !trackingMapInstance) return;
        try {
          const { data: orders } = await supabaseClient.from('orders').select('*').eq('customer_id', currentUserId).order('created_at', { ascending: false });
          if (!orders || orders.length === 0) { 
            container.innerHTML = `<p style="font-size: 11px; color: var(--text-muted); text-align: center;">لا توجد طلبات نشطة حالياً.</p>`; 
            return; 
          }
          const activeOrder = orders[0];
          let pLat = activeOrder.pickup_lat || userCurrentLat, pLng = activeOrder.pickup_lng || userCurrentLng;
          let dLat = activeOrder.dropoff_lat || userCurrentLat, dLng = activeOrder.dropoff_lng || userCurrentLng;
          let driverLat = activeOrder.driver_lat || pLat;
          let driverLng = activeOrder.driver_lng || pLng;

          drawMapboxRoute(trackingMapInstance, driverLng, driverLat, dLng, dLat, 'tracking-route', '#1e3a8a');

          if (!window.mapboxPickupMarker) {
            window.mapboxPickupMarker = new mapboxgl.Marker({ color: '#1e3a8a' }).setLngLat([pLng, pLat]).addTo(trackingMapInstance);
            window.mapboxDropoffMarker = new mapboxgl.Marker({ color: '#ef4444' }).setLngLat([dLng, dLat]).addTo(trackingMapInstance);
          }

          if (!trackingDriverMarker) {
            const el = document.createElement('div');
            el.innerHTML = '<div style="background:#1e3a8a; color:white; padding:6px 10px; border-radius:50px; font-size:16px; box-shadow:0 0 12px rgba(30,58,138,0.6); display:flex; align-items:center; gap:4px; font-weight:bold;">🛵</div>';
            trackingDriverMarker = new mapboxgl.Marker(el).setLngLat([driverLng, driverLat]).addTo(trackingMapInstance);
          } else {
            trackingDriverMarker.setLngLat([driverLng, driverLat]);
          }

          container.innerHTML = `
            <div class="indrive-order-card">
              <div class="card-top-info"><span class="price-badge-indrive">${activeOrder.price_mad} MAD</span><span class="distance-tag">الحالة: ${activeOrder.status}</span></div>
              <div class="location-row"><span class="dot-point pickup"></span><span><b>الاستلام:</b> ${formatShortAddress(activeOrder.pickup_address)}</span></div>
              <div class="location-row"><span class="dot-point delivery"></span><span><b>التسليم:</b> ${formatShortAddress(activeOrder.dropoff_address)}</span></div>
            </div>
          `;
        } catch (e) { console.error("Client tracking fetch error:", e); }
      }

      function renderDriverRadarOrders(orders) {
        const container = document.getElementById("ordersListContainer");
        if (!container) return;
        if (!orders || orders.length === 0) { container.innerHTML = `<p style="font-size: 11px; color: var(--text-muted); text-align: center; padding: 10px;">لا توجد طلبيات في الرادار.</p>`; return; }
        let html = '';
        orders.forEach(o => {
          html += `
            <div class="indrive-order-card">
              <div class="card-top-info"><span class="price-badge-indrive">${o.price_mad || 20} MAD</span><span class="distance-tag">📍 المسافة: ${o.calculatedDist} كلم</span></div>
              <div class="location-row"><span class="dot-point pickup"></span><span><b>الاستلام:</b> ${formatShortAddress(o.pickup_address)}</span></div>
              <div class="location-row"><span class="dot-point delivery"></span><span><b>التسليم:</b> ${formatShortAddress(o.dropoff_address)}</span></div>
              <button class="btn-indrive-action" onclick="acceptOrder('${o.id}')">🛵 قبول الطلب الآن</button>
            </div>
          `;
        });
        container.innerHTML = html;
      }

      async function acceptOrder(orderId) {
        try {
          const res = await fetch('/accept-order', {
            method: 'POST', headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ order_id: orderId, driver_id: currentUserId })
          });
          if (!res.ok) throw new Error("فشل قبول الطلب");
          showAppToast("تم بنجاح", "تم قبول الطلب بنجاح.");
          checkDriverActiveOrder();
        } catch (e) { showAppToast("خطأ", e.message); }
      }

      function showAppToast(title, message) {
        document.getElementById("toastTitle").innerText = title;
        document.getElementById("toastMessage").innerText = message;
        document.getElementById("customToastOverlay").style.display = "flex";
      }
      function closeCustomToast() { document.getElementById("customToastOverlay").style.display = "none"; }

      function switchAuthMode(mode) {
        currentAuthMode = mode;
        document.getElementById("groupFullName").style.display = mode === 'signup' ? "block" : "none";
        document.getElementById("groupPhone").style.display = mode === 'signup' ? "block" : "none";
        document.getElementById("groupRole").style.display = mode === 'signup' ? "block" : "none";
        document.getElementById("authFormTitle").innerText = mode === 'signup' ? "🚀 إنشاء حساب جديد مع رصيد ترحيبي 20 درهم" : "🔑 تسجيل الدخول لحسابك";
      }

      async function handleAuthAction() {
        const email = document.getElementById("authEmail").value.trim();
        const password = document.getElementById("authPassword").value.trim();
        if (currentAuthMode === 'signup') {
          const name = document.getElementById("authFullName").value.trim();
          const phone = document.getElementById("authPhone").value.trim();
          const role = document.getElementById("authRole").value;
          
          const initialBalance = (role === 'driver') ? 20.0 : 0.0;

          const { data, error } = await supabaseClient.auth.signUp({ 
            email, password, 
            options: { data: { full_name: name, phone_number: phone, role, wallet_balance: initialBalance } } 
          });
          if (error) { showAppToast("خطأ", error.message); return; }
          
          if (data.user) {
            await supabaseClient.from('profiles').upsert({
              id: data.user.id,
              full_name: name,
              phone_number: phone,
              role: role,
              wallet_balance: initialBalance
            });
          }

          localStorage.setItem("app_user_id", data.user.id);
          localStorage.setItem("app_user_name", name);
          localStorage.setItem("app_user_role", role);
          localStorage.setItem("app_user_phone", phone);
          showAppToast("مرحباً بك! 🎉", "تم منحك رصيداً ترحيبياً بقيمة 20 درهم في محفظتك.");
          setTimeout(() => location.reload(), 1500);
        } else {
          const { data, error } = await supabaseClient.auth.signInWithPassword({ email, password });
          if (error) { showAppToast("خطأ", error.message); return; }
          const { data: profile } = await supabaseClient.from("profiles").select("*").eq("id", data.user.id).single();
          localStorage.setItem("app_user_id", data.user.id);
          localStorage.setItem("app_user_name", profile.full_name);
          localStorage.setItem("app_user_role", profile.role);
          localStorage.setItem("app_user_phone", profile.phone_number || "");
          location.reload();
        }
      }

      async function submitDriverDocuments() { showAppToast("جاري المعالجة", "تم رفع المستندات بنجاح."); }

      async function submitRealWalletTopupRequest() {
        const amount = parseFloat(document.getElementById("walletRechargeAmount").value.trim() || 0);
        const fileInput = document.getElementById("receiptImageFile");
        
        if (amount < 30) {
          showAppToast("تنبيه ⚠️", "الحد الأدنى للشحن عبر التحويل البنكي CIH هو 30 درهم.");
          return;
        }

        if (!fileInput.files || fileInput.files.length === 0) {
          showAppToast("تنبيه ⚠️", "يرجى التقاط صورة لوصل التحويل البنكي بالكاميرا للمطابقة.");
          return;
        }

        try {
          showAppToast("جاري الرفع...", "يتم رفع صورة الوصل وإرسال طلب الشحن...");
          
          const file = fileInput.files[0];
          const fileExt = file.name.split('.').pop() || 'jpg';
          const fileName = `receipt_${currentUserId}_${Date.now()}.${fileExt}`;
          const filePath = `receipts/${fileName}`;

          const { data: uploadData, error: uploadError } = await supabaseClient.storage
            .from('assets')
            .upload(filePath, file);

          if (uploadError) throw uploadError;

          const { data: publicUrlData } = supabaseClient.storage
            .from('assets')
            .getPublicUrl(filePath);

          const receiptUrl = publicUrlData.publicUrl;

          const res = await fetch('/api/wallet/topup', { 
            method: 'POST', 
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ 
              user_id: currentUserId, 
              amount: amount, 
              receipt_url: receiptUrl 
            })
          });
          
          const result = await res.json();
          if (!res.ok) throw new Error(result.detail || "فشل إرسال الطلب");
          
          showAppToast("تم بنجاح 📨", "تم إرسال طلب الشحن وصورة الوصل بنجاح للإدارة للمراجعة وإضافة الرصيد مع البونيس تلقائياً.");
          
          document.getElementById("walletRechargeAmount").value = "";
          document.getElementById("receiptTextRef").value = "";
          fileInput.value = "";
          document.querySelectorAll('.bonus-circle').forEach(c => c.classList.remove('active'));
          
          fetchDriverWalletBalance();
        } catch (e) {
          showAppToast("خطأ ❌", e.message);
        }
      }

      async function createNewOrder() {
        const recipientPhone = document.getElementById("recipientPhone").value.trim();
        const recipientPhoneSec = document.getElementById("recipientPhoneSecondary").value.trim();
        const parcelDesc = document.getElementById("parcelDescription").value.trim();
        const securityAccepted = document.getElementById("securityAcceptedCheckbox").checked;

        if (!recipientPhone || !recipientPhoneSec) {
          showAppToast("تنبيه ⚠️", "رقم هاتف المستلم الأول ورقم الهاتف الإضافي (الثاني) إلزاميان معاً.");
          return;
        }

        if (!securityAccepted) {
          showAppToast("تنبيه أمني 🚨", "يجب الموافقة الإلزامية على الشروط الأمنية ومنع نقل الممنوعات لمتابعة الطلب.");
          return;
        }

        if (!parcelDesc) {
          showAppToast("تنبيه", "يرجى كتابة وصف واضح لمحتوى الشحنة.");
          return;
        }

        try {
          const res = await fetch('/create-order', {
            method: 'POST', 
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
              pickup_lat: userCurrentLat,
              pickup_lng: userCurrentLng,
              dropoff_lat: deliveryLat,
              dropoff_lng: deliveryLng,
              user_id: currentUserId,
              customer_name: currentUserName,
              customer_phone: currentUserPhone,
              recipient_phone: recipientPhone,
              recipient_phone_secondary: recipientPhoneSec,
              notes: parcelDesc,
              security_accepted: securityAccepted
            })
          });
          const result = await res.json();
          if (!res.ok) throw new Error(result.detail || result.message);
          showAppToast("تم بنجاح 🚀", `تم إنشاء الطلب بالسعر: ${result.data.price_mad} MAD`);
          switchMainView('clientOrdersView');
        } catch (e) { showAppToast("خطأ", e.message); }
      }

      async function fetchDriverWalletBalance() {
        if (!currentUserId) return;
        try {
          const { data } = await supabaseClient.from('profiles').select('wallet_balance').eq('id', currentUserId).single();
          if (data) document.getElementById("driverWalletBalance").innerText = `${parseFloat(data.wallet_balance || 0).toFixed(2)} MAD`;
        } catch (e) {}
      }

      function initMapboxClientMap() {
        if (!navigator.geolocation) {
          initMapboxMapInstance(userCurrentLat, userCurrentLng);
          return;
        }

        navigator.geolocation.getCurrentPosition(pos => {
          userCurrentLat = pos.coords.latitude;
          userCurrentLng = pos.coords.longitude;
          initMapboxMapInstance(userCurrentLat, userCurrentLng);
        }, () => {
          initMapboxMapInstance(userCurrentLat, userCurrentLng);
        }, { enableHighAccuracy: true });
      }

      function initMapboxMapInstance(lat, lng) {
        if (mapboxInstance) {
          mapboxInstance.resize();
          mapboxInstance.setCenter([lng, lat]);
          if (deliveryMarker) deliveryMarker.setLngLat([lng, lat]);
          updateCoordsDisplay(lat, lng);
          return;
        }

        mapboxInstance = new mapboxgl.Map({
          container: 'map',
          style: 'mapbox://styles/mapbox/streets-v12',
          center: [lng, lat],
          zoom: 15
        });

        if (typeof MapboxLanguage !== 'undefined') {
          mapboxInstance.addControl(new MapboxLanguage({ defaultLanguage: 'ar' }));
        }

        deliveryLat = lat; deliveryLng = lng;
        deliveryMarker = new mapboxgl.Marker({ color: '#1e3a8a', draggable: true })
          .setLngLat([deliveryLng, deliveryLat])
          .addTo(mapboxInstance);

        updateCoordsDisplay(deliveryLat, deliveryLng);

        deliveryMarker.on('dragend', () => {
          const lngLat = deliveryMarker.getLngLat();
          updateCoordsDisplay(lngLat.lat, lngLat.lng);
        });

        mapboxInstance.on('click', (e) => {
          deliveryMarker.setLngLat(e.lngLat);
          updateCoordsDisplay(e.lngLat.lat, e.lngLat.lng);
        });

        const geocoder = new MapboxGeocoder({
          accessToken: mapboxgl.accessToken,
          mapboxgl: mapboxgl,
          marker: false,
          placeholder: 'ابحث عن أي حي أو شارع في الدار البيضاء...',
          bbox: [-7.85, 33.35, -7.35, 33.75],
          proximity: { longitude: lng, latitude: lat }
        });

        const geocoderContainer = document.getElementById('geocoder-container');
        if (geocoderContainer && !geocoderContainer.hasChildNodes()) {
          geocoderContainer.appendChild(geocoder.onAdd(mapboxInstance));
        }

        geocoder.on('result', (e) => {
          const coords = e.result.center;
          deliveryMarker.setLngLat(coords);
          updateCoordsDisplay(coords[1], coords[0]);
        });
      }

      function updateCoordsDisplay(lat, lng) {
        deliveryLat = lat; deliveryLng = lng;
        document.getElementById("deliveryCoordsDisplay").value = `📍 إحداثيات الاستلام: (${deliveryLat.toFixed(4)},${deliveryLng.toFixed(4)})`;
      }

      function goToCurrentLocation() {
        if (!navigator.geolocation) return;
        navigator.geolocation.getCurrentPosition(p => {
          userCurrentLat = p.coords.latitude;
          userCurrentLng = p.coords.longitude;
          if (mapboxInstance) {
            mapboxInstance.resize();
            mapboxInstance.setCenter([userCurrentLng, userCurrentLat]);
            deliveryMarker.setLngLat([userCurrentLng, userCurrentLat]);
            updateCoordsDisplay(userCurrentLat, userCurrentLng);
          }
          showAppToast("تم التحديث 📍", "تم ضبط موقع الاستلام على موقعك الحالي عبر GPS.");
        }, () => { showAppToast("تنبيه", "تعذر تحديد موقعك الحالي."); }, { enableHighAccuracy: true });
      }

      function logoutUser() { releaseScreenWakeLock(); localStorage.clear(); location.reload(); }

      document.addEventListener("DOMContentLoaded", async () => {
        if (navigator.geolocation) {
          navigator.geolocation.getCurrentPosition(p => {
            userCurrentLat = p.coords.latitude; userCurrentLng = p.coords.longitude;
            document.getElementById("locationOverlay").style.display = "none";
          }, () => { document.getElementById("locationOverlay").style.display = "flex"; }, { enableHighAccuracy: true });
        }

        if (currentUserId && currentUserPhone) {
          document.querySelectorAll('.visitor-only-item').forEach(el => el.style.display = "none");
          document.getElementById("drawer-logout").style.display = "flex";
          if (currentRole === 'driver') {
            document.getElementById("driverStatusToggle").style.display = "flex";
            document.getElementById("driverBottomNav").style.display = "flex";
            document.querySelectorAll(".role-driver-item").forEach(el => el.style.display = "flex");
            switchMainView("ordersView");
          } else {
            document.querySelectorAll(".role-customer-item").forEach(el => el.style.display = "flex");
            switchMainView("clientView");
          }
        } else {
          document.querySelectorAll('.visitor-only-item').forEach(el => el.style.display = "flex");
          switchMainView("homeView");
        }
      });
    </script>
  </body>
</html>"""
    return HTMLResponse(content=html_content)

# ==========================================
# 2. لوحة التحكم الإدارية ( /admin )
# ==========================================
@app.get("/admin", response_class=HTMLResponse)
def serve_admin_dashboard():
    admin_html_content = """<!DOCTYPE html>
<html lang="ar" dir="rtl">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>لوحة التحكم الإدارية الاحترافية - نتسخر ليك في كازا</title>
    
    <link href="https://fonts.googleapis.com/css2?family=Tajawal:wght@400;600;700;800;900&display=swap" rel="stylesheet">
    <link rel="stylesheet" href="https://unpkg.com/leaflet@1.9.4/dist/leaflet.css" />
    <script src="https://cdn.jsdelivr.net/npm/@supabase/supabase-js@2.39.8/dist/umd/supabase.min.js"></script>
    <script src="https://unpkg.com/leaflet@1.9.4/dist/leaflet.js"></script>

    <style>
        :root {
            --primary: #10b981;
            --bg-dark: #0f172a;
            --card-bg: #1e293b;
            --text-main: #f8fafc;
            --text-muted: #94a3b8;
            --border: rgba(255, 255, 255, 0.1);
            --danger: #ef4444;
            --warning: #f59e0b;
        }

        * { box-sizing: border-box; margin: 0; padding: 0; font-family: 'Tajawal', sans-serif; }
        html { scroll-behavior: smooth; }
        body { background: var(--bg-dark); color: var(--text-main); display: flex; min-height: 100vh; overflow-x: hidden; }

        .admin-sidebar { width: 260px; background: var(--card-bg); border-left: 1px solid var(--border); display: flex; flex-direction: column; position: fixed; top: 0; bottom: 0; right: 0; z-index: 1000; padding: 20px; overflow-y: auto; }
        .sidebar-brand { font-size: 16px; font-weight: 900; color: var(--primary); margin-bottom: 30px; text-align: center; border-bottom: 1px solid var(--border); padding-bottom: 15px; }
        .sidebar-menu { display: flex; flex-direction: column; gap: 8px; list-style: none; }
        .sidebar-item button { width: 100%; display: flex; align-items: center; gap: 10px; padding: 12px 14px; color: var(--text-muted); text-decoration: none; border-radius: 8px; font-size: 13px; font-weight: 700; transition: all 0.2s; background: transparent; border: none; cursor: pointer; text-align: right; }
        .sidebar-item button:hover, .sidebar-item button.active { background: rgba(16, 185, 129, 0.15); color: var(--primary); }

        .admin-main { flex: 1; margin-right: 260px; padding: 30px; max-width: calc(100% - 260px); }
        header { display: flex; justify-content: space-between; align-items: center; border-bottom: 1px solid var(--border); padding-bottom: 15px; margin-bottom: 30px; }
        h1 { color: var(--primary); font-size: 20px; }

        .stats-grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); gap: 15px; margin-bottom: 35px; }
        .stat-card { background: var(--card-bg); border: 1px solid var(--border); border-radius: 12px; padding: 20px; text-align: center; }
        .stat-card h3 { font-size: 12px; color: var(--text-muted); margin-bottom: 5px; }
        .stat-card p { font-size: 22px; font-weight: 900; color: var(--primary); }

        .admin-section { display: none; background: var(--card-bg); border: 1px solid var(--border); border-radius: 12px; padding: 20px; margin-bottom: 35px; animation: fadeIn 0.3s ease-in-out; }
        .admin-section.active { display: block; }
        @keyframes fadeIn { from { opacity: 0; transform: translateY(5px); } to { opacity: 1; transform: translateY(0); } }

        .admin-section h2 { font-size: 15px; color: var(--primary); margin-bottom: 15px; border-bottom: 1px solid var(--border); padding-bottom: 8px; display: flex; justify-content: space-between; align-items: center; }

        #adminLiveMap { width: 100%; height: 400px; border-radius: 12px; border: 1px solid var(--border); margin-bottom: 10px; }

        table { width: 100%; border-collapse: collapse; font-size: 12px; text-align: right; }
        th, td { padding: 12px 10px; border-bottom: 1px solid var(--border); }
        th { color: var(--text-muted); }

        .btn-action { padding: 6px 12px; border: none; border-radius: 6px; font-weight: bold; cursor: pointer; font-size: 11px; margin-left: 4px; text-decoration: none; display: inline-block; }
        .btn-approve { background: var(--primary); color: white; }
        .btn-reject { background: var(--danger); color: white; }
        .btn-block { background: var(--warning); color: black; }
        .btn-edit { background: #38bdf8; color: black; }

        .alert-row { background: rgba(239, 68, 68, 0.08); }
        .signal-badge {
            display: inline-flex; align-items: center; gap: 5px;
            background: rgba(239, 68, 68, 0.2); color: #fca5a5;
            padding: 4px 8px; border-radius: 6px; font-size: 10px; font-weight: bold;
            border: 1px solid var(--danger); animation: blinkSignal 1.2s infinite;
        }
        @keyframes blinkSignal { 0% { opacity: 1; } 50% { opacity: 0.3; } 100% { opacity: 1; } }

        .doc-img { width: 50px; height: 50px; object-fit: cover; border-radius: 6px; cursor: pointer; border: 1px solid var(--border); }
        .field-inline { display: flex; gap: 10px; align-items: center; margin-bottom: 10px; flex-wrap: wrap; }
        .field-inline input, .field-inline textarea { padding: 8px; border-radius: 6px; border: 1px solid var(--border); background: var(--bg-dark); color: white; }

        .winner-card {
            background: rgba(245, 158, 11, 0.05); border: 1px dashed var(--warning);
            border-radius: 12px; padding: 14px; margin-bottom: 10px; display: flex; justify-content: space-between; align-items: center;
        }
        .winner-info h4 { color: var(--warning); font-size: 13px; margin-bottom: 4px; }
        .winner-info p { font-size: 11px; color: var(--text-muted); margin-bottom: 2px; }
        .badge-prize { background: rgba(245, 158, 11, 0.2); color: var(--warning); padding: 3px 8px; border-radius: 6px; font-size: 10px; font-weight: bold; display: inline-block; margin-top: 4px; }
        .indrive-order-card { background: var(--card-bg); border: 1px solid var(--border); border-radius: 12px; padding: 14px; margin-bottom: 12px; }
    </style>
</head>
<body>

    <aside class="admin-sidebar">
        <div class="sidebar-brand">🛡️ لوحة الإدارة العليا</div>
        <ul class="sidebar-menu">
            <li class="sidebar-item"><button onclick="switchAdminTab('statsSection', this)" class="active">📊 نظرة عامة والإحصائيات</button></li>
            <li class="sidebar-item"><button onclick="switchAdminTab('walletAdminSection', this)">💳 طلبات الشحن والتحويلات</button></li>
            <li class="sidebar-item"><button onclick="switchAdminTab('promoAdminSection', this)">📢 إدارة لوحة الإعلانات</button></li>
            <li class="sidebar-item"><button onclick="switchAdminTab('complaintSection', this)">🔍 شبكة الأمان والشكاوى</button></li>
            <li class="sidebar-item"><button onclick="switchAdminTab('winnersSection', this)">🏆 الفائزون بمسابقة الشهر</button></li>
            <li class="sidebar-item"><button onclick="switchAdminTab('ordersSection', this)">🔴 مراقبة الطلبات المعلقة</button></li>
            <li class="sidebar-item"><button onclick="switchAdminTab('mapSection', this)">🗺 خريطة تتبع الموصلين</button></li>
            <li class="sidebar-item"><button onclick="switchAdminTab('settingsSection', this)">💰 التسعير والعمولات</button></li>
            <li class="sidebar-item"><button onclick="switchAdminTab('driversSection', this)">📝 وثائق الموصلين</button></li>
            <li class="sidebar-item"><button onclick="switchAdminTab('usersSection', this)">👥 إدارة وحظر الحسابات</button></li>
        </ul>
    </aside>

    <main class="admin-main">
        <header>
            <h1>⚙️ لوحة التحكم والإدارة الرئيسية الاحترافية</h1>
            <button class="btn-action btn-reject" onclick="location.reload()">🔄 تحديث البيانات</button>
        </header>

        <div class="admin-section active" id="statsSection">
            <h2>📊 نظرة عامة والإحصائيات النظام</h2>
            <div class="stats-grid">
                <div class="stat-card"><h3>إجمالي المستخدمين</h3><p id="statTotalUsers">0</p></div>
                <div class="stat-card"><h3>الموصلين النشطين (Online)</h3><p id="statOnlineDrivers" style="color:var(--primary);">0</p></div>
                <div class="stat-card"><h3>الموصلين المعلقين</h3><p id="statPendingDrivers" style="color:var(--warning);">0</p></div>
                <div class="stat-card"><h3>إجمالي الطلبات</h3><p id="statTotalOrders">0</p></div>
                <div class="stat-card"><h3>👥 الزائرون اليوم</h3><p id="statDailyVisitors" style="color:#38bdf8;">0</p></div>
            </div>
        </div>

        <div class="admin-section" id="walletAdminSection">
            <h2>💳 اعتماد وشحن المحافظ (في انتظار مراجعة الوصل والـ SMS)</h2>
            <p style="font-size: 11px; color: var(--text-muted); margin-bottom: 14px;">هذه الطلبات تطابقت مع البيانات البنكية أو تم رفعها، يرجى مراجعة وصل التحويل والتأكد ثم الضغط على تفعيل لإضافتها لرصيد الموصل تلقائياً:</p>
            <div id="adminTopupsContainer">
                <p style="font-size: 11px; color: var(--text-muted);">جاري تحميل طلبات الشحن المعلقة...</p>
            </div>
        </div>

        <div class="admin-section" id="promoAdminSection">
            <h2>📢 إدارة لوحة الإعلانات الترويجية (الرئيسية)</h2>
            <div class="field-inline" style="flex-direction: column; align-items: stretch;">
                <label style="font-size:12px; color:var(--primary); font-weight:bold;">عنوان الإعلان / المسابقة:</label>
                <input type="text" id="adminPromoTitle" placeholder="مثال: 🏆 مسابقة الشهر لزبناء تسخر ليك!" style="margin-bottom: 8px;">
                <label style="font-size:12px; color:var(--primary); font-weight:bold;">نص الإعلان والرسالة الترويجية:</label>
                <textarea id="adminPromoText" rows="3" placeholder="اكتب تفاصيل الإعلان هنا..." style="padding: 10px; border-radius: 6px; border: 1px solid var(--border); background: var(--bg-dark); color: white; margin-bottom: 10px;"></textarea>
                <button class="btn-action btn-approve" onclick="savePromoAnnouncement()" style="padding: 12px; font-weight: bold;">💾 نشر وتحديث الإعلان في الرئيسية فوراً</button>
            </div>
        </div>

        <div class="admin-section" id="complaintSection">
            <h2>🔍 شبكة الأمان والتحقيق في شكاوى الزبناء (Audit Trail)</h2>
            <div class="field-inline">
                <input type="text" id="complaintSearchInput" placeholder="أدخل رقم هاتف المستلم أو ID الطلب..." style="flex:1;">
                <button class="btn-action btn-approve" onclick="adminInvestigateComplaint()">بحث وتحقيق فوري</button>
            </div>
            <div id="complaintResultContainer" style="margin-top: 15px;"><p style="font-size: 11px; color: var(--text-muted);">أدخل المعيار بالأعلى للبدء بالبحث في السجلات...</p></div>
        </div>

        <div class="admin-section" id="winnersSection">
            <h2>🏆 فائزون مسابقة الشهر (أتموا 20 طلبة ناجحة) - جائزة 200 درهم</h2>
            <div id="winnersListContainer"><p style="color: var(--text-muted); font-size: 12px;">جاري فحص وجلب الزبائن المؤهلين للفوز هذا الشهر...</p></div>
        </div>

        <div class="admin-section" id="ordersSection">
            <h2>
                <span>🔴 مراقبة الطلبات المعلقة أو غير المكتملة</span>
                <button class="btn-action btn-reject" onclick="adminDeleteAllOrders()" style="font-size: 12px; padding: 8px 14px;">🗑️ إزالة جميع الطلبيات</button>
            </h2>
            <table>
                <thead>
                    <tr><th>رقم الطلب</th><th>الزبون</th><th>الموصل المقبول</th><th>الحالة / السنيال</th><th>الإجراءات اليدوية</th></tr>
                </thead>
                <tbody id="adminOrdersTable"><tr><td colspan="5">جاري التحقق من الطلبات المعلقة...</td></tr></tbody>
            </table>
        </div>

        <div class="admin-section" id="mapSection">
            <h2>🗺️ خريطة تتبع الموصلين والطلبات المباشرة في كازا</h2>
            <div id="adminLiveMap"></div>
        </div>

        <div class="admin-section" id="settingsSection">
            <h2>💰 إعدادات التسعير والعمولات</h2>
            <div class="field-inline" style="flex-direction: column; align-items: stretch; gap: 10px;">
                <div><label style="font-size: 11px; color: var(--text-muted);">أدنى سعر للتوصيل (MAD):</label><input type="number" id="settingMinPrice" style="width: 100%; margin-top: 4px;"></div>
                <div><label style="font-size: 11px; color: var(--text-muted);">سعر الكيلومتر الإضافي (MAD):</label><input type="number" id="settingPricePerKm" step="0.25" style="width: 100%; margin-top: 4px;"></div>
                <div><label style="font-size: 11px; color: var(--text-muted);">معامل تعديل الوقود:</label><input type="number" id="settingFuelMultiplier" step="0.1" style="width: 100%; margin-top: 4px;"></div>
                <button class="btn-action btn-approve" onclick="saveSettings()" style="padding: 10px; font-weight: bold; margin-top: 5px;">💾 حفظ وتحديث إعدادات التسعير</button>
            </div>
        </div>

        <div class="admin-section" id="driversSection">
            <h2>📝 طلبات الموصلين والوثائق المرفوعة (قيد المراجعة)</h2>
            <table>
                <thead>
                    <tr><th>الاسم</th><th>الهاتف</th><th>البطاقة (CIN)</th><th>الورقة الرمادية</th><th>صورة الوجه</th><th>الإجراءات</th></tr>
                </thead>
                <tbody id="pendingDriversTable"><tr><td colspan="6">جاري تحميل الطلبات...</td></tr></tbody>
            </table>
        </div>

        <div class="admin-section" id="usersSection">
            <h2>👥 إدارة الحسابات (تفعيل / حظر)</h2>
            <table>
                <thead>
                    <tr><th>الاسم</th><th>الهاتف</th><th>النوع</th><th>الحالة</th><th>الإجراء</th></tr>
                </thead>
                <tbody id="allUsersTable"><tr><td colspan="5">جاري تحميل المستخدمين...</td></tr></tbody>
            </table>
        </div>
    </main>

    <script>
        const SUPABASE_URL = "https://cauujrnxtqswjzqhphyq.supabase.co";
        const SUPABASE_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6ImNhdXVqcm54dHFzd2p6cWhwaHlxIiwicm9sZSI6ImFub24iLCJpYXQiOjE3ODgzNDEwNDMsImV4cCI6MjEwMzkxNzA0M30.xIwYyOcOaH-3VEkfuf2T73tHMRn3oAL2_RjNNPueQKU";
        const supabaseClient = supabase.createClient(SUPABASE_URL, SUPABASE_KEY);

        let adminMap = null;
        let driverMarkers = {};

        document.addEventListener("DOMContentLoaded", () => {
            trackDailyVisitor();
            initAdminMap();
            loadDashboardStats();
            loadAdminWalletQueue();
            loadQualifiedWinners();
            loadAdminOrdersMonitor();
            loadPendingDrivers();
            loadAllUsers();
            loadDynamicPricingSettings();
            listenRealtimeUpdates();
        });

        async function trackDailyVisitor() {
            try {
                const todayStr = new Date().toISOString().split('T')[0];
                const visitorKey = `admin_visitor_tracked_${todayStr}`;
                if (!localStorage.getItem(visitorKey)) {
                    localStorage.setItem(visitorKey, 'true');
                    let { data } = await supabaseClient.from('app_settings').select('setting_value').eq('setting_key', `daily_visitors_${todayStr}`).single();
                    let currentCount = data ? parseInt(data.setting_value || 0) : 0;
                    currentCount++;
                    await supabaseClient.from('app_settings').upsert({ setting_key: `daily_visitors_${todayStr}`, setting_value: currentCount.toString() });
                }
            } catch (e) {}
        }

        function switchAdminTab(sectionId, btnElement) {
            document.querySelectorAll('.admin-section').forEach(sec => sec.classList.remove('active'));
            document.querySelectorAll('.sidebar-menu button').forEach(btn => btn.classList.remove('active'));

            document.getElementById(sectionId).classList.add('active');
            btnElement.classList.add('active');

            if (sectionId === 'mapSection' && adminMap) {
                setTimeout(() => { adminMap.invalidateSize(); }, 200);
            }
            if (sectionId === 'walletAdminSection') {
                loadAdminWalletQueue();
            }
        }

        async function loadAdminWalletQueue() {
            const container = document.getElementById("adminTopupsContainer");
            if (!container) return;
            try {
                const { data: topups, error } = await supabaseClient
                    .from('wallet_topups')
                    .select(`id, amount, total_credited, receipt_url, status, created_at, profiles:driver_id ( full_name, phone_number )`)
                    .eq('status', 'pending');

                if (error) throw error;

                if (!topups || topups.length === 0) {
                    container.innerHTML = `<p style="font-size: 11px; color: var(--text-muted); text-align: center; padding: 15px;">لا توجد طلبات شحن معلقة حالياً.</p>`;
                    return;
                }

                let html = '';
                topups.forEach(item => {
                    const driverName = item.profiles ? item.profiles.full_name : 'موصل مجهول';
                    const driverPhone = item.profiles ? item.profiles.phone_number : '';

                    html += `
                        <div class="indrive-order-card" style="border: 1px solid var(--warning);">
                            <div class="card-top-info" style="display:flex; justify-content:space-between; margin-bottom:8px;">
                                <span style="background:rgba(16,185,129,0.15); color:var(--primary); font-weight:900; padding:4px 10px; border-radius:8px;">المجموع: ${item.total_credited} MAD</span>
                                <span style="color:var(--warning); font-size:11px;">المبلغ الأساسي: ${item.amount} درهم</span>
                            </div>
                            <div style="font-size:12px; margin-bottom:8px;">👤 <b>الموصل:</b> ${driverName} (${driverPhone})</div>
                            <div style="font-size:12px; margin-bottom:8px;">
                                📸 <b>صورة وصل التحويل:</b><br>
                                <a href="${item.receipt_url || '#'}" target="_blank">
                                    <img src="${item.receipt_url || 'https://via.placeholder.com/150'}" style="width:100%; max-height:180px; object-fit:cover; border-radius:8px; margin-top:6px; border:1px solid var(--border);" />
                                </a>
                            </div>
                            <button class="btn-action btn-approve" style="width:100%; padding:10px; font-weight:bold;" onclick="adminApproveTopup('${item.id}', '${item.driver_id}', ${item.total_credited})">✅ تفعيل وإضافة الرصيد للموصل</button>
                        </div>
                    `;
                });
                container.innerHTML = html;
            } catch (e) {
                container.innerHTML = `<p style="font-size: 11px; color: var(--danger);">خطأ في جلب طلبات الشحن.</p>`;
            }
        }

        async function adminApproveTopup(topupId, driverId, totalCredited) {
            try {
                const { data: profile } = await supabaseClient.from('profiles').select('wallet_balance').eq('id', driverId).single();
                const currentBalance = profile ? parseFloat(profile.wallet_balance || 0) : 0;
                const newBalance = currentBalance + parseFloat(totalCredited);

                const { error: updateErr } = await supabaseClient.from('profiles').update({ wallet_balance: newBalance }).eq('id', driverId);
                if (updateErr) throw updateErr;

                const { error: topupErr } = await supabaseClient.from('wallet_topups').update({ status: 'approved' }).eq('id', topupId);
                if (topupErr) throw topupErr;

                alert("✅ تم تفعيل الشحن وإضافة الرصيد لمحفظة الموصل بنجاح.");
                loadAdminWalletQueue();
            } catch (e) {
                alert("خطأ: " + e.message);
            }
        }

        async function savePromoAnnouncement() {
            const title = document.getElementById('adminPromoTitle').value.trim();
            const text = document.getElementById('adminPromoText').value.trim();
            if (!title || !text) { alert("يرجى ملء عنوان ونص الإعلان."); return; }

            try {
                const { error } = await supabaseClient.from('app_settings').upsert([
                    { setting_key: 'promo_title', setting_value: title },
                    { setting_key: 'promo_text', setting_value: text }
                ]);
                if (error) throw error;
                alert("🚀 تم تحديث الإعلان ونشره بنجاح في الصفحة الرئيسية للزبناء والزوار!");
            } catch (err) { alert("خطأ في النشر: " + err.message); }
        }

        async function adminInvestigateComplaint() {
            const queryText = document.getElementById('complaintSearchInput').value.trim();
            const resultContainer = document.getElementById('complaintResultContainer');
            if (!queryText) { alert("يرجى إدخال رقم الهاتف أو رقم الطلب للبحث."); return; }

            resultContainer.innerHTML = '<p style="color:var(--text-muted); font-size:12px;">جاري فحص أرشيف السجلات والتحقيق...</p>';
            try {
                const { data: disputedOrders, error } = await supabaseClient
                    .from('orders')
                    .select('*, customer:customer_id(full_name, phone_number), driver:driver_id(full_name, phone_number)')
                    .or(`recipient_phone.ilike.%${queryText}%,id.ilike.%${queryText}%`)
                    .order('created_at', { ascending: false });

                if (error) throw error;
                if (!disputedOrders || disputedOrders.length === 0) {
                    resultContainer.innerHTML = '<p style="color:var(--warning); font-size:12px;">لم يتم العثور على أي طلب مسجل بهذا المعيار في الأرشيف.</p>';
                    return;
                }

                resultContainer.innerHTML = disputedOrders.map(ord => `
                    <div class="winner-card" style="border-color: var(--primary); background: rgba(16, 185, 129, 0.05);">
                        <div class="winner-info" style="width: 100%;">
                            <h4>📦 تفاصيل الطلب: #${ord.id}</h4>
                            <p>📌 الحالة الحالية: <strong style="color:var(--primary);">${ord.status}</strong></p>
                            <p>🙋‍♂️ الزبون صاحب الطلب: ${ord.customer ? ord.customer.full_name : 'غير معروف'} (هاتف: ${ord.customer ? ord.customer.phone_number : '-'})</p>
                            <p>🛵 الموصل المسؤول: ${ord.driver ? ord.driver.full_name : 'لم يتم إسناده'} (هاتف: ${ord.driver ? ord.driver.phone_number : '-'})</p>
                            <p>📍 التسليم: ${ord.dropoff_address || 'غير محدد'} | هاتف المستلم: <strong>${ord.recipient_phone}</strong></p>
                        </div>
                    </div>
                `).join('');
            } catch (err) { resultContainer.innerHTML = `<p style="color:var(--danger); font-size:12px;">خطأ في عملية التحقيق: ${err.message}</p>`; }
        }

        function initAdminMap() {
            adminMap = L.map('adminLiveMap').setView([33.5731, -7.5898], 12);
            L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png').addTo(adminMap);
            loadActiveDriversOnMap();
        }

        async function loadActiveDriversOnMap() {
            const { data: drivers } = await supabaseClient.from('profiles').select('*').eq('role', 'driver');
            if (drivers) {
                document.getElementById('statOnlineDrivers').innerText = drivers.length;
                drivers.forEach(d => updateDriverMarker(d));
            }
        }

        function updateDriverMarker(driver) {
            if (!driver.driver_lat || !driver.driver_lng) return;
            const lat = driver.driver_lat;
            const lng = driver.driver_lng;
            if (driverMarkers[driver.id]) {
                driverMarkers[driver.id].setLatLng([lat, lng]);
            } else {
                driverMarkers[driver.id] = L.marker([lat, lng]).addTo(adminMap).bindPopup(`🛵 <b>${driver.full_name}</b><br>📞 ${driver.phone_number}`);
            }
        }

        async function loadQualifiedWinners() {
            const container = document.getElementById('winnersListContainer');
            try {
                const startOfMonth = new Date(new Date().getFullYear(), new Date().getMonth(), 1).toISOString();
                const { data: customers } = await supabaseClient.from('profiles').select('*').eq('role', 'customer');
                if (!customers || customers.length === 0) { container.innerHTML = '<p style="color:var(--text-muted); font-size:12px;">لا يوجد زبائن مسجلين حالياً.</p>'; return; }

                let winnersHTML = '';
                let foundAny = false;
                for (let cust of customers) {
                    const { count, error } = await supabaseClient.from('orders').select('*', { count: 'exact', head: true }).eq('customer_id', cust.id).gte('created_at', startOfMonth);
                    if (!error && count >= 20) {
                        foundAny = true;
                        winnersHTML += `
                            <div class="winner-card">
                                <div class="winner-info">
                                    <h4>👤 ${cust.full_name || 'بدون اسم'}</h4>
                                    <p>📞 رقم الهاتف: <strong>${cust.phone_number}</strong></p>
                                    <p>📊 الطلبات الناجحة هذا الشهر: <strong style="color:var(--primary);">${count} طلبات</strong></p>
                                    <span class="badge-prize">🎁 مؤهل لجائزة قسيمة 200 درهم</span>
                                </div>
                                <div><a href="tel:${cust.phone_number}" class="btn-action btn-approve">📞 اتصال بالزبون</a></div>
                            </div>
                        `;
                    }
                }
                container.innerHTML = foundAny ? winnersHTML : '<p style="color:var(--text-muted); font-size:12px;">لم يصل أي زبون إلى 20 طلبة حتى الآن هذا الشهر.</p>';
            } catch (e) { container.innerHTML = `<p style="color:var(--danger); font-size:12px;">خطأ: ${e.message}</p>`; }
        }

        async function loadAdminOrdersMonitor() {
            const { data: orders } = await supabaseClient.from('orders').select('*, customer:customer_id(full_name), driver:driver_id(full_name)').order('id', { ascending: false });
            const tbody = document.getElementById('adminOrdersTable');
            if (!orders || orders.length === 0) { tbody.innerHTML = '<tr><td colspan="5">لا توجد طلبات مسجلة حالياً.</td></tr>'; return; }

            tbody.innerHTML = orders.map(ord => {
                let isPendingUnfinished = (ord.status === 'pending' || ord.status === 'assigned');
                return `
                    <tr class="${isPendingUnfinished ? 'alert-row' : ''}">
                        <td>#${ord.id.substring(0, 6)}</td>
                        <td>${ord.customer_name || 'زبون'}</td>
                        <td>${ord.driver_id ? 'موصل مسند' : 'في انتظار الموصل'}</td>
                        <td>${isPendingUnfinished ? `<span class="signal-badge">🔴 طلبية معلقة</span>` : `<span>${ord.status}</span>`}</td>
                        <td>
                            <button class="btn-action btn-reject" onclick="adminDeleteOrder('${ord.id}')">🗑 إزالة نهائية</button>
                        </td>
                    </tr>
                `;
            }).join('');
        }

        async function adminDeleteOrder(orderId) {
            if (!confirm("هل أنت متأكد من رغبتك في إزالة وإلغاء هذه الطلبية نهائياً؟")) return;
            try {
                await supabaseClient.from('orders').delete().eq('id', orderId);
                alert("🗑 تم إزالة الطلبية بنجاح.");
                loadAdminOrdersMonitor();
                loadDashboardStats();
            } catch (err) { alert("خطأ: " + err.message); }
        }

        async function adminDeleteAllOrders() {
            if (!confirm("⚠️ تحذير: هل أنت متأكد من حذف جميع الطلبيات؟")) return;
            try {
                await supabaseClient.from('orders').delete().neq('id', '00000000-0000-0000-0000-000000000000');
                alert("🗑️ تم حذف جميع الطلبات بنجاح.");
                loadAdminOrdersMonitor();
                loadDashboardStats();
            } catch (err) { alert("خطأ: " + err.message); }
        }

        async function loadDynamicPricingSettings() {
            try {
                const { data } = await supabaseClient.from('app_settings').select('setting_key, setting_value');
                if (data) {
                    data.forEach(item => {
                        if (item.setting_key === 'min_fare') document.getElementById('settingMinPrice').value = item.setting_value;
                        if (item.setting_key === 'price_per_km') document.getElementById('settingPricePerKm').value = item.setting_value;
                        if (item.setting_key === 'fuel_multiplier') document.getElementById('settingFuelMultiplier').value = item.setting_value;
                    });
                }
            } catch (err) {}
        }

        async function saveSettings() {
            const minFare = document.getElementById('settingMinPrice').value;
            const pricePerKm = document.getElementById('settingPricePerKm').value;
            const fuelMultiplier = document.getElementById('settingFuelMultiplier').value;

            try {
                await supabaseClient.from('app_settings').upsert([
                    { setting_key: 'min_fare', setting_value: minFare },
                    { setting_key: 'price_per_km', setting_value: pricePerKm },
                    { setting_key: 'fuel_multiplier', setting_value: fuelMultiplier }
                ]);
                alert("💰 تم حفظ إعدادات التسعير بنجاح!");
            } catch (err) { alert("خطأ: " + err.message); }
        }

        function listenRealtimeUpdates() {
            supabaseClient.channel('admin_realtime_all')
                .on('postgres_changes', { event: '*', schema: 'public', table: 'profiles' }, () => { loadDashboardStats(); loadPendingDrivers(); loadAllUsers(); })
                .on('postgres_changes', { event: '*', schema: 'public', table: 'orders' }, () => { loadDashboardStats(); loadAdminOrdersMonitor(); })
                .on('postgres_changes', { event: '*', schema: 'public', table: 'wallet_topups' }, () => { loadAdminWalletQueue(); })
                .subscribe();
        }

        async function loadDashboardStats() {
            const { count: usersCount } = await supabaseClient.from('profiles').select('*', { count: 'exact', head: true });
            const { count: pendingCount } = await supabaseClient.from('profiles').select('*', { count: 'exact', head: true }).eq('role', 'driver').eq('verification_status', 'pending_review');
            const { count: ordersCount } = await supabaseClient.from('orders').select('*', { count: 'exact', head: true });
            
            const todayStr = new Date().toISOString().split('T')[0];
            const { data: visitorData } = await supabaseClient.from('app_settings').select('setting_value').eq('setting_key', `daily_visitors_${todayStr}`).single();
            const dailyVisitorsCount = visitorData ? visitorData.setting_value : '1';

            document.getElementById('statTotalUsers').innerText = usersCount || 0;
            document.getElementById('statPendingDrivers').innerText = pendingCount || 0;
            document.getElementById('statTotalOrders').innerText = ordersCount || 0;
            document.getElementById('statDailyVisitors').innerText = dailyVisitorsCount;
        }

        async function loadPendingDrivers() {
            const { data: drivers } = await supabaseClient.from('profiles').select('*').eq('role', 'driver');
            const tbody = document.getElementById('pendingDriversTable');
            if (!drivers || drivers.length === 0) { tbody.innerHTML = '<tr><td colspan="6">لا توجد طلبات توثيق معلقة.</td></tr>'; return; }

            tbody.innerHTML = drivers.map(d => `
                <tr>
                    <td>${d.full_name || 'بدون اسم'}</td>
                    <td>${d.phone_number || '-'}</td>
                    <td><img src="${d.cin_front_url || ''}" class="doc-img" onclick="window.open(this.src)" onerror="this.src='https://via.placeholder.com/50'"></td>
                    <td><img src="${d.registration_card_url || ''}" class="doc-img" onclick="window.open(this.src)" onerror="this.src='https://via.placeholder.com/50'"></td>
                    <td><img src="${d.avatar_url || ''}" class="doc-img" onclick="window.open(this.src)" onerror="this.src='https://via.placeholder.com/50'"></td>
                    <td><button class="btn-action btn-approve" onclick="updateDriverStatus('${d.id}', 'verified')">قبول وتفعيل</button></td>
                </tr>
            `).join('');
        }

        async function updateDriverStatus(userId, status) {
            await supabaseClient.from('profiles').update({ verification_status: status }).eq('id', userId);
            alert("تم تحديث حالة الموصل!");
            loadPendingDrivers();
        }

        async function loadAllUsers() {
            const { data: users } = await supabaseClient.from('profiles').select('*');
            const tbody = document.getElementById('allUsersTable');
            if (!users || users.length === 0) { tbody.innerHTML = '<tr><td colspan="5">لا توجد حسابات مسجلة.</td></tr>'; return; }
            
            tbody.innerHTML = users.map(u => `
                <tr>
                    <td>${u.full_name || 'بدون اسم'}</td>
                    <td>${u.phone_number || '-'}</td>
                    <td>${u.role === 'driver' ? 'موصل 🛵' : 'زبون 🙋‍♂️'}</td>
                    <td>${u.verification_status || 'نشط'}</td>
                    <td><button class="btn-action btn-block" onclick="toggleUserBlock('${u.id}', '${u.verification_status}')">تبديل الحالة</button></td>
                </tr>
            `).join('');
        }

        async function toggleUserBlock(userId, currentStatus) {
            const newStatus = (currentStatus === 'blocked') ? 'verified' : 'blocked';
            await supabaseClient.from('profiles').update({ verification_status: newStatus }).eq('id', userId);
            loadAllUsers();
        }
    </script>
</body>
</html>"""
    return HTMLResponse(content=admin_html_content)

if __name__ == "__main__":
    import uvicorn
    port = int(os.environ.get("PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=port)
