let map = L.map('map').setView([30.285955, -97.739320], 500)
L.tileLayer('https://tile.openstreetmap.org/{z}/{x}/{y}.png', {
    maxNativeZoom: 19, maxZoom: 22, attribution: '&copy; <a href="http://www.openstreetmap.org/copyright">OpenStreetMap</a>'
}).addTo(map)
map.setZoom(18)

let end_date_elem = document.getElementById('end_date')
end_date_elem.addEventListener('change', (e) => {
    if ((new Date(e.target.value)).getTime() < (new Date(document.getElementById('start_date').value)).getTime()) {
        map._handlers.forEach(function(handler) { handler.disable() })
        document.getElementById('dates').innerText = 'Error: End date is earlier than start date. Please fix before progressing to the map.'
    } else {
        map._handlers.forEach(function(handler) { handler.enable() })
        document.getElementById('dates').innerText = ''
    }
})

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
    const inputs = document.getElementsByClassName('inputs');
    let payload = {}
    let points = Array()
    let warning_types = ['SEVERE THUNDERSTORM', 'TORNADO', 'FLASH FLOOD', 'SPECIAL MARINE']
    Array.from(inputs).forEach((input) => {
        if (!warning_types.includes(input.id) || input.checked) { payload[input.id] = input.value }
    })
    e.layer.getLatLngs().filter((element, index) => {return index % 2 === 0})[0].forEach((point) => {points.push([point.lat, point.lng])})
    payload.polygon = points

    let xhr = new XMLHttpRequest()
    xhr.open('POST', 'http://localhost:5000/jobs')
    xhr.setRequestHeader('Content-Type', 'application/json; charset=UTF-8')
    xhr.send(JSON.stringify(payload))
})
