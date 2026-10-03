<!DOCTYPE html>
<html lang="ar" dir="rtl">
<head>
    <meta charset="utf-8">
    <title>خريطة الدار البيضاء الواضحة</title>
    <meta name="viewport" content="initial-scale=1,maximum-scale=1,user-scalable=no">
    <!-- استدعاء مكتبة Mapbox CSS -->
    <link href="https://api.mapbox.com/mapbox-gl-js/v3.12.0/mapbox-gl.css" rel="stylesheet">
    <style>
        body { margin: 0; padding: 0; }
        #map { position: absolute; top: 0; bottom: 0; width: 100%; }
    </style>
</head>
<body>

<div id="map"></div>

<!-- استدعاء مكتبة Mapbox JS -->
<script src="https://api.mapbox.com/mapbox-gl-js/v3.12.0/mapbox-gl.js"></script>
<script>
    // استخدام المفتاح الخاص بك بشكل مباشر وصحيح
    mapboxgl.accessToken = 'pk.eyJ1IjoiaWRzaWRpIiwiYSI6ImNtdTJscHkybjAwbW8yeXF1cXFhdXozaWMifQ.FDKkwkz9kdug1cghlLNChw';

    const map = new mapboxgl.Map({
        container: 'map',
        // استخدام نمط الشوارع المدعوم رسمياً من Mapbox والمبني على بيانات OpenStreetMap الحقيقية
        style: 'mapbox://styles/mapbox/streets-v12', 
        center: [-7.589843, 33.573110], // مركز الدار البيضاء الكبرى
        zoom: 13, // زووم واضح للشوارع والزنقي
        maxZoom: 19
    });

    // إضافة أزرار التحكم في التكبير والتصغير
    map.addControl(new mapboxgl.NavigationControl());
</script>

</body>
</html>
