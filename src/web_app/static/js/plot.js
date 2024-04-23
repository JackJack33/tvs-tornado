async function main() {
    const host_ip = 'localhost'
    const job_data = await create_job(host_ip)
    await get_results(host_ip, job_data.id, job_data.status)
}


async function create_job(host_ip) {
    const response = await fetch(`http://${host_ip}:5000/jobs`, {
        method: 'POST'
    })
    return await response.json()
}

async function get_results(host_ip, jid, status) {
    while (status !== 'Complete') {
        await new Promise(resolve => setTimeout(resolve, 300));
        const res = await fetch(`http://${host_ip}:5000/jobs/${jid}`)
        const data = await res.json()
        status = data.status
    }
    const res = await fetch(`http://${host_ip}:5000/results/${jid}`)
    const pic = await res.text()
    document.getElementById('plot').src = `data:image/png;base64,${pic}`
}

main()
