let map = L.map('map').setView([30.285955, -97.739320], 500)
L.tileLayer('https://tile.openstreetmap.org/{z}/{x}/{y}.png', {
    maxNativeZoom: 19, maxZoom: 22, attribution: '&copy; <a href="http://www.openstreetmap.org/copyright">OpenStreetMap</a>'
}).addTo(map)
map.setZoom(18)

let drawnItems = new L.FeatureGroup()
map.addLayer(drawnItems)
let drawControl = new L.Control.Draw({
    draw: {
        polyline: false,
        circle: false,
        marker: false,
        rectangle: false,

        polygon: {
            allowIntersection: false,
            drawError: {
                color: "#f8c137",
                message: "<strong>Lines of a polygon cannot overlap!</strong>"
            }
        }
    },
    edit: {
        featureGroup: drawnItems,
        edit: false,
        remove: false
    }
})
map.addControl(drawControl)
map.on('draw:created', (e) => {
    drawnItems.clearLayers()
    drawnItems.addLayer(e.layer)
    const inputs = document.getElementsByClassName("inputs");
    let payload = {}
    let points = Array()
    Array.from(inputs).forEach((input) => { payload[input.id] = input.value })
    e.layer.getLatLngs().filter((element, index) => {return index % 2 === 0})[0].forEach((point) => {points.push([point.lat, point.lng])})
    payload.polygon = points

    let xhr = new XMLHttpRequest()
    xhr.open('POST', 'http://localhost:5000/jobs')
    xhr.setRequestHeader('Content-Type', 'application/json; charset=UTF-8')
    xhr.send(JSON.stringify(payload))
})
