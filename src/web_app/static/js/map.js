let map = L.map('map').setView([30.285955, -97.739320], 500)
L.tileLayer('https://tile.openstreetmap.org/{z}/{x}/{y}.png', {
    maxNativeZoom: 19, maxZoom: 22, attribution: '&copy; <a href="http://www.openstreetmap.org/copyright">OpenStreetMap</a>'
}).addTo(map)
map.setZoom(18)

// var drawnItems = new L.FeatureGroup();
//  map.addLayer(drawnItems);
//  var drawControl = new L.Control.Draw({
//      edit: {
//          featureGroup: drawnItems
//      }
//  });
//  map.addControl(drawControl);