let maps = {};
let charts = {};

function toggleSidebar() {
    const sidebar = document.getElementById('sidebar');
    sidebar.classList.toggle('collapsed');
    const icon = sidebar.querySelector('.sidebar-toggle i');
    if (sidebar.classList.contains('collapsed')) {
        icon.className = 'fas fa-chevron-right';
    } else {
        icon.className = 'fas fa-chevron-left';
    }
}

function showPage(pageId) {
    const pages = document.querySelectorAll('.page-content');
    pages.forEach(page => page.classList.remove('active'));
    
    const targetPage = document.getElementById('page-' + pageId);
    if (targetPage) {
        targetPage.classList.add('active');
    }
    
    const menuItems = document.querySelectorAll('.menu-item[data-page]');
    menuItems.forEach(item => item.classList.remove('active'));
    
    const activeMenuItem = document.querySelector(`.menu-item[data-page="${pageId}"]`);
    if (activeMenuItem) {
        activeMenuItem.classList.add('active');
    }
    
    const pageTitles = {
        'dashboard': { title: 'Dashboard', subtitle: 'Welcome back!' },
        'pickup': { title: 'Pickup Request', subtitle: 'Schedule a waste collection' },
        'pickups': { title: 'Assigned Pickups', subtitle: 'Manage your collection tasks' },
        'bins': { title: 'Smart Bins', subtitle: 'Monitor bin fill levels' },
        'route': { title: 'Route Optimization', subtitle: 'AI-powered collection routes' },
        'navigation': { title: 'GPS Navigation', subtitle: 'Turn-by-turn directions' },
        'vehicle': { title: 'Vehicle Status', subtitle: 'Monitor your vehicle' },
        'confirm': { title: 'Confirm Collection', subtitle: 'Verify waste collection' },
        'complaint': { title: 'Report Issue', subtitle: 'Report waste management issues' },
        'history': { title: 'Pickup History', subtitle: 'View past collections' },
        'payment': { title: 'Payments', subtitle: 'Manage your payments' },
        'recycling': { title: 'Recycling Tips', subtitle: 'Learn about proper recycling' },
        'notifications': { title: 'Notifications', subtitle: 'Stay updated' },
        'fleet': { title: 'Fleet Monitor', subtitle: 'Track all vehicles' },
        'analytics': { title: 'Analytics', subtitle: 'Waste management insights' },
        'complaints': { title: 'Complaint Management', subtitle: 'Handle user complaints' },
        'routes': { title: 'Route Optimizer', subtitle: 'Optimize collection routes' },
        'alerts': { title: 'Smart Alerts', subtitle: 'Real-time system alerts' },
        'reports': { title: 'Report Generation', subtitle: 'Generate detailed reports' },
        'users': { title: 'User Management', subtitle: 'Manage system users' },
        'profile': { title: 'My Profile', subtitle: 'Update your information' }
    };
    
    if (pageTitles[pageId]) {
        document.getElementById('pageTitle').textContent = pageTitles[pageId].title;
        document.getElementById('pageSubtitle').textContent = pageTitles[pageId].subtitle;
    }
    
    setTimeout(() => {
        if (pageId === 'bins' && document.getElementById('citizenMap') && !maps.citizenMap) {
            initCitizenMap();
        }
        if (pageId === 'dashboard' && document.getElementById('wasteChart') && !charts.wasteChart) {
            initWasteChart();
        }
        if (pageId === 'route' && document.getElementById('driverRouteMap') && !maps.driverRouteMap) {
            initDriverRouteMap();
        }
        if (pageId === 'navigation' && document.getElementById('navMap') && !maps.navMap) {
            initNavMap();
        }
        if (pageId === 'vehicle' && document.getElementById('vehicleMap') && !maps.vehicleMap) {
            initVehicleMap();
        }
        if (pageId === 'dashboard' && document.getElementById('adminCityMap') && !maps.adminCityMap) {
            initAdminCityMap();
        }
        if (pageId === 'analytics' && document.getElementById('adminAnalyticsChart') && !charts.adminAnalyticsChart) {
            initAdminAnalyticsChart();
        }
        if (pageId === 'fleet' && document.getElementById('fleetMap') && !maps.fleetMap) {
            initFleetMap();
        }
        if (pageId === 'routes' && document.getElementById('adminRouteMap') && !maps.adminRouteMap) {
            initAdminRouteMap();
        }
    }, 100);
}

function showNotifications() {
    showPage('notifications');
}

function markAllRead() {
    const unreadItems = document.querySelectorAll('.notification-item.unread');
    unreadItems.forEach(item => item.classList.remove('unread'));
    const badges = document.querySelectorAll('.notification-badge');
    badges.forEach(badge => badge.textContent = '0');
    alert('All notifications marked as read!');
}

document.addEventListener('DOMContentLoaded', function() {
    const menuItems = document.querySelectorAll('.menu-item[data-page]');
    menuItems.forEach(item => {
        item.addEventListener('click', function(e) {
            e.preventDefault();
            const pageId = this.dataset.page;
            showPage(pageId);
        });
    });
    
    if (window.innerWidth <= 768) {
        const sidebar = document.getElementById('sidebar');
        if (sidebar) {
            sidebar.classList.add('collapsed');
        }
    }
});

// Map initialization functions
function initCitizenMap() {
    const mapEl = document.getElementById('citizenMap');
    if (!mapEl || maps.citizenMap) return;
    
    maps.citizenMap = L.map('citizenMap').setView([40.7128, -74.0060], 13);
    L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
        attribution: '© OpenStreetMap contributors'
    }).addTo(maps.citizenMap);
    
    const bins = [
        { lat: 40.7128, lng: -74.0060, fill: 45, id: '#001', status: 'success' },
        { lat: 40.7150, lng: -74.0080, fill: 72, id: '#002', status: 'warning' },
        { lat: 40.7180, lng: -74.0100, fill: 95, id: '#003', status: 'danger' }
    ];
    
    bins.forEach(bin => {
        const color = bin.status === 'success' ? 'green' : bin.status === 'warning' ? 'orange' : 'red';
        L.marker([bin.lat, bin.lng], {
            icon: L.divIcon({
                html: `<div style="background: ${color}; width: 30px; height: 30px; border-radius: 50%; display: flex; align-items: center; justify-content: center; color: white; font-weight: bold; border: 3px solid white; box-shadow: 0 2px 5px rgba(0,0,0,0.3);">${bin.fill}%</div>`,
                iconSize: [30, 30],
                className: ''
            })
        }).addTo(maps.citizenMap)
        .bindPopup(`<b>Bin ${bin.id}</b><br>Fill Level: ${bin.fill}%<br>Status: ${bin.status}`);
    });
}

function initWasteChart() {
    const ctx = document.getElementById('wasteChart');
    if (!ctx || charts.wasteChart) return;
    
    charts.wasteChart = new Chart(ctx, {
        type: 'bar',
        data: {
            labels: ['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun'],
            datasets: [{
                label: 'General Waste (kg)',
                data: [8.5, 7.2, 9.1, 6.8, 8.9, 5.5, 4.2],
                backgroundColor: 'rgba(46, 204, 113, 0.7)',
                borderColor: 'rgba(46, 204, 113, 1)',
                borderWidth: 1
            }, {
                label: 'Recyclables (kg)',
                data: [5.2, 4.8, 6.1, 5.5, 4.9, 3.8, 3.2],
                backgroundColor: 'rgba(52, 152, 219, 0.7)',
                borderColor: 'rgba(52, 152, 219, 1)',
                borderWidth: 1
            }, {
                label: 'Organic (kg)',
                data: [3.8, 3.2, 4.1, 3.5, 3.9, 2.8, 2.5],
                backgroundColor: 'rgba(243, 156, 18, 0.7)',
                borderColor: 'rgba(243, 156, 18, 1)',
                borderWidth: 1
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                legend: { position: 'top' }
            },
            scales: {
                y: { beginAtZero: true, title: { display: true, text: 'Weight (kg)' } }
            }
        }
    });
}

function initDriverRouteMap() {
    const mapEl = document.getElementById('driverRouteMap');
    if (!mapEl || maps.driverRouteMap) return;
    
    maps.driverRouteMap = L.map('driverRouteMap').setView([40.7128, -74.0060], 13);
    L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
        attribution: '© OpenStreetMap contributors'
    }).addTo(maps.driverRouteMap);
    
    const stops = [
        { lat: 40.7128, lng: -74.0060, label: 'Bin #003 - 95%' },
        { lat: 40.7150, lng: -74.0080, label: 'Bin #007 - 72%' },
        { lat: 40.7180, lng: -74.0100, label: 'Bin #012 - 45%' }
    ];
    
    const points = [];
    stops.forEach((stop, idx) => {
        L.marker([stop.lat, stop.lng]).addTo(maps.driverRouteMap).bindPopup(stop.label);
        points.push([stop.lat, stop.lng]);
    });
    
    L.polyline(points, { color: 'var(--primary)', weight: 3, opacity: 0.7 }).addTo(maps.driverRouteMap);
}

function initNavMap() {
    const mapEl = document.getElementById('navMap');
    if (!mapEl || maps.navMap) return;
    
    maps.navMap = L.map('navMap').setView([40.7128, -74.0060], 15);
    L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
        attribution: '© OpenStreetMap contributors'
    }).addTo(maps.navMap);
    
    L.marker([40.7180, -74.0100]).addTo(maps.navMap).bindPopup('Bin #003 - Destination');
    L.marker([40.7128, -74.0060]).addTo(maps.navMap).bindPopup('Your Location');
}

function initVehicleMap() {
    const mapEl = document.getElementById('vehicleMap');
    if (!mapEl || maps.vehicleMap) return;
    
    maps.vehicleMap = L.map('vehicleMap').setView([40.7128, -74.0060], 14);
    L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
        attribution: '© OpenStreetMap contributors'
    }).addTo(maps.vehicleMap);
    
    L.marker([40.7128, -74.0060], {
        icon: L.divIcon({
            html: '<div style="background: var(--secondary); width: 40px; height: 40px; border-radius: 50%; display: flex; align-items: center; justify-content: center; color: white; font-size: 1.2rem; border: 3px solid white; box-shadow: 0 2px 5px rgba(0,0,0,0.3);"><i class="fas fa-truck"></i></div>',
            iconSize: [40, 40],
            className: ''
        })
    }).addTo(maps.vehicleMap).bindPopup('Vehicle V-001 - Mike Wilson');
}

function initAdminCityMap() {
    const mapEl = document.getElementById('adminCityMap');
    if (!mapEl || maps.adminCityMap) return;
    
    maps.adminCityMap = L.map('adminCityMap').setView([40.7128, -74.0060], 13);
    L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
        attribution: '© OpenStreetMap contributors'
    }).addTo(maps.adminCityMap);
    
    const allBins = [
        { lat: 40.7128, lng: -74.0060, fill: 45, id: '#001' },
        { lat: 40.7150, lng: -74.0080, fill: 72, id: '#007' },
        { lat: 40.7180, lng: -74.0100, fill: 95, id: '#003' },
        { lat: 40.7200, lng: -74.0120, fill: 30, id: '#012' },
        { lat: 40.7220, lng: -74.0140, fill: 80, id: '#015' }
    ];
    
    allBins.forEach(bin => {
        const color = bin.fill >= 85 ? 'red' : bin.fill >= 60 ? 'orange' : 'green';
        L.circleMarker([bin.lat, bin.lng], {
            radius: 12,
            fillColor: color,
            color: 'white',
            weight: 2,
            fillOpacity: 0.8
        }).addTo(maps.adminCityMap)
        .bindPopup(`<b>Bin ${bin.id}</b><br>Fill: ${bin.fill}%`);
    });
}

function initAdminAnalyticsChart() {
    const ctx = document.getElementById('adminAnalyticsChart');
    if (!ctx || charts.adminAnalyticsChart) return;
    
    charts.adminAnalyticsChart = new Chart(ctx, {
        type: 'line',
        data: {
            labels: ['Jan', 'Feb', 'Mar', 'Apr', 'May'],
            datasets: [{
                label: 'Total Waste (kg)',
                data: [15000, 16500, 15800, 18200, 17000],
                borderColor: 'rgba(46, 204, 113, 1)',
                backgroundColor: 'rgba(46, 204, 113, 0.1)',
                tension: 0.4,
                fill: true
            }, {
                label: 'Recycled (kg)',
                data: [10500, 11550, 11850, 13104, 12240],
                borderColor: 'rgba(52, 152, 219, 1)',
                backgroundColor: 'rgba(52, 152, 219, 0.1)',
                tension: 0.4,
                fill: true
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                legend: { position: 'top' }
            },
            scales: {
                y: { beginAtZero: true, title: { display: true, text: 'Weight (kg)' } }
            }
        }
    });
}

function initFleetMap() {
    const mapEl = document.getElementById('fleetMap');
    if (!mapEl || maps.fleetMap) return;
    
    maps.fleetMap = L.map('fleetMap').setView([40.7128, -74.0060], 13);
    L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
        attribution: '© OpenStreetMap contributors'
    }).addTo(maps.fleetMap);
    
    const vehicles = [
        { lat: 40.7128, lng: -74.0060, driver: 'Mike Wilson', id: 'V-001' },
        { lat: 40.7150, lng: -74.0080, driver: 'John Smith', id: 'V-005' }
    ];
    
    vehicles.forEach(v => {
        L.marker([v.lat, v.lng], {
            icon: L.divIcon({
                html: `<div style="background: var(--secondary); width: 35px; height: 35px; border-radius: 50%; display: flex; align-items: center; justify-content: center; color: white; border: 2px solid white; box-shadow: 0 2px 5px rgba(0,0,0,0.3);"><i class="fas fa-truck" style="font-size: 0.9rem;"></i></div>`,
                iconSize: [35, 35],
                className: ''
            })
        }).addTo(maps.fleetMap).bindPopup(`<b>${v.id}</b><br>Driver: ${v.driver}`);
    });
}

function initAdminRouteMap() {
    const mapEl = document.getElementById('adminRouteMap');
    if (!mapEl || maps.adminRouteMap) return;
    
    maps.adminRouteMap = L.map('adminRouteMap').setView([40.7128, -74.0060], 13);
    L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
        attribution: '© OpenStreetMap contributors'
    }).addTo(maps.adminRouteMap);
    
    const bins = [
        { lat: 40.7128, lng: -74.0060, fill: 45 },
        { lat: 40.7150, lng: -74.0080, fill: 72 },
        { lat: 40.7180, lng: -74.0100, fill: 95 }
    ];
    
    const points = [];
    bins.forEach(bin => {
        const color = bin.fill >= 85 ? 'red' : bin.fill >= 60 ? 'orange' : 'green';
        L.circleMarker([bin.lat, bin.lng], {
            radius: 10,
            fillColor: color,
            color: 'white',
            weight: 2,
            fillOpacity: 0.8
        }).addTo(maps.adminRouteMap);
        points.push([bin.lat, bin.lng]);
    });
    
    L.polyline(points, { color: 'var(--primary)', weight: 4, opacity: 0.7, dashArray: '10,10' }).addTo(maps.adminRouteMap);
}

function previewPhoto(event) {
    const file = event.target.files[0];
    if (file) {
        const reader = new FileReader();
        reader.onload = function(e) {
            const preview = document.getElementById('photoPreview');
            if (preview) {
                preview.innerHTML = `<img src="${e.target.result}" style="max-width: 200px; border-radius: 8px; margin-top: 10px;">`;
            }
        };
        reader.readAsDataURL(file);
    }
}

function submitPickup(event) {
    event.preventDefault();
    alert('Pickup request submitted successfully! You will receive a confirmation notification.');
    event.target.reset();
}

function submitComplaint(event) {
    event.preventDefault();
    alert('Complaint submitted successfully! Our team will review it shortly.');
    event.target.reset();
}

function confirmCollection(event) {
    event.preventDefault();
    alert('Collection confirmed! Thank you for your service.');
    event.target.reset();
}

function processPayment(event) {
    event.preventDefault();
    alert('Payment processed successfully! Thank you.');
    event.target.reset();
}

function startNavigation(address) {
    showPage('navigation');
    const destElement = document.getElementById('currentDestination');
    if (destElement) {
        destElement.textContent = address;
    }
}

function stopNavigation() {
    if (confirm('Are you sure you want to end navigation?')) {
        showPage('dashboard');
    }
}

function generateReport(type) {
    alert(`Generating ${type} report... The report will be ready for download shortly.`);
}
