let map = L.map('map').setView([30.285955, -97.739320], 500)
L.tileLayer('https://tile.openstreetmap.org/{z}/{x}/{y}.png', {
    maxNativeZoom: 19, maxZoom: 22, attribution: '&copy; <a href="http://www.openstreetmap.org/copyright">OpenStreetMap</a>'
}).addTo(map)
map.setZoom(15)

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

async function get_results(jid) {
    let status
    do {
        await new Promise(resolve => setTimeout(resolve, 500));
        const res = await fetch(`http://${flask_ip}/jobs/${jid}`)
        const data = await res.json()
        status = data.status
    } while (status !== 'Complete')
    const res = await fetch(`http://${flask_ip}/results/${jid}`)
    const pic = await res.text()
    document.getElementById('plot').src = `data:image/png;base64,${pic}`
}

map.on('draw:created', (e) => {
    let payload = {'warning_types': []}
    let warning_types = ['SEVERE THUNDERSTORM', 'TORNADO', 'FLASH FLOOD', 'SPECIAL MARINE']
    let warning_flag = false

    const inputs = document.getElementsByClassName('inputs');
    Array.from(inputs).forEach((input) => {
        if (warning_types.includes(input.id) && input.checked) {
            payload.warning_types.push(input.id)
            warning_flag = true
        } else if (!warning_types.includes(input.id)) {
            payload[input.id] = input.value
        }
    })

    if (!warning_flag) {
        document.getElementById('warning_types').innerText = 'No warning types selected. Please check at least one warning type and then redraw your polygon.'
    } else {
        document.getElementById('warning_types').innerText = ''
        drawnItems.clearLayers()
        drawnItems.addLayer(e.layer)
        let points = Array()

        e.layer.getLatLngs().filter((element, index) => {
            return index % 2 === 0
        })[0].forEach((point) => {
            points.push([point.lng, point.lat])
        })
        payload.polygon = points

        let xhr = new XMLHttpRequest()
        xhr.open('POST', `http://${flask_ip}/jobs`)
        xhr.setRequestHeader('Content-Type', 'application/json; charset=UTF-8')
        xhr.responseType = 'json'
        xhr.onreadystatechange = async () => {
            if (xhr.readyState === XMLHttpRequest.DONE) {
                await get_results(xhr.response.id)
            }
        }
        xhr.send(JSON.stringify(payload))
    }
})
