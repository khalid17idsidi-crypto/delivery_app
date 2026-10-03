<!DOCTYPE html>
<html lang="ar" dir="rtl">
<head>
    <meta charset="utf-8">
    <title>خريطة الدار البيضاء الواضحة</title>
    <meta name="viewport" content="initial-scale=1,maximum-scale=1,user-scalable=no">
    <!-- استدعاء مكتبة Mapbox CSS المحدثة -->
    <link href="https://api.mapbox.com/mapbox-gl-js/v3.12.0/mapbox-gl.css" rel="stylesheet">
    <style>
        body { margin: 0; padding: 0; }
        #map { position: absolute; top: 0; bottom: 0; width: 100%; }
    </style>
</head>
<body>

<div id="map"></div>

<!-- استدعاء مكتبة Mapbox JS المحدثة -->
<script src="https://api.mapbox.com/mapbox-gl-js/v3.12.0/mapbox-gl.js"></script>
<script>
    // ⚠️ استبدل هذا الرمز بالـ Access Token الخاص بك من موقع Mapbox
    mapboxgl.accessToken = 'pk.eyJ1IjoieW91ci11c2VybmFtZSIsImEiOiJjbH...';

    const map = new mapboxgl.Map({
        container: 'map',
        style: 'mapbox://styles/mapbox/streets-v12', // النمط المستقر والواضحة جداً للشبكة والشوارع
        center: [-7.589843, 33.573110], // مركز الدار البيضاء
        zoom: 13 // مستوى التقريب لعرض الأحياء والشوارع
    });

    // إضافة أزرار التكبير والتصغير
    map.addControl(new mapboxgl.NavigationControl());
</script>

</body>
</html>
