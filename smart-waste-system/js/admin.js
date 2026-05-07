document.addEventListener('DOMContentLoaded', function() {
    if (!localStorage.getItem('isLoggedIn')) {
        window.location.href = 'index.html';
        return;
    }
    
    const role = localStorage.getItem('userRole');
    if (role !== 'admin') {
        window.location.href = 'index.html';
        return;
    }
    
    const email = localStorage.getItem('userEmail');
    if (email) {
        const name = email.split('@')[0].replace(/\./g, ' ');
        const initials = name.split(' ').map(n => n[0]).join('').toUpperCase();
        document.querySelectorAll('.user-avatar').forEach(el => el.textContent = initials);
        document.querySelectorAll('.top-bar-actions .user-dropdown div:first-child').forEach(el => {
            el.innerHTML = `<div style="font-weight: 600; font-size: 0.9rem;">Admin</div><div style="font-size: 0.8rem; color: var(--gray);">Administrator</div>`;
        });
    }
    
    loadAdminData();
    startRealTimeUpdates();
});

function loadAdminData() {
    updateDashboardStats();
}

function updateDashboardStats() {
    const bins = [
        { id: '#001', location: 'Main St & 1st Ave', fill: 45, weight: '12kg/25kg', battery: 85, status: 'success', statusText: 'Operational', lastUpdate: '2 min ago' },
        { id: '#003', location: 'Oak Road 123', fill: 95, weight: '24kg/25kg', battery: 92, status: 'danger', statusText: 'Critical', lastUpdate: '1 min ago' },
        { id: '#007', location: 'Park Ave 456', fill: 72, weight: '18kg/25kg', battery: 45, status: 'warning', statusText: 'Warning', lastUpdate: '5 min ago' },
        { id: '#012', location: '789 Main St', fill: 45, weight: '11kg/25kg', battery: 78, status: 'success', statusText: 'Operational', lastUpdate: '3 min ago' },
        { id: '#015', location: '321 Elm Street', fill: 80, weight: '20kg/25kg', battery: 65, status: 'warning', statusText: 'Warning', lastUpdate: '7 min ago' },
        { id: '#045', location: 'Oak Road 456', fill: 30, weight: '8kg/25kg', battery: 15, status: 'warning', statusText: 'Low Battery', lastUpdate: '15 min ago' }
    ];
    
    localStorage.setItem('bins', JSON.stringify(bins));
}

function startRealTimeUpdates() {
    setInterval(() => {
        const bins = JSON.parse(localStorage.getItem('bins') || '[]');
        
        bins.forEach(bin => {
            const change = (Math.random() - 0.5) * 2;
            bin.fill = Math.max(0, Math.min(100, bin.fill + change));
            
            if (bin.fill > 90) {
                bin.status = 'danger';
                bin.statusText = 'Critical';
            } else if (bin.fill > 70) {
                bin.status = 'warning';
                bin.statusText = 'Warning';
            } else {
                bin.status = 'success';
                bin.statusText = 'Operational';
            }
            
            const weightValue = (bin.fill / 100) * 25;
            bin.weight = `${weightValue.toFixed(0)}kg/25kg`;
            
            bin.battery = Math.max(0, bin.battery - 0.1);
        });
        
        localStorage.setItem('bins', JSON.stringify(bins));
        
        const badges = document.querySelectorAll('.notification-badge');
        badges.forEach(badge => {
            const current = parseInt(badge.textContent);
            if (Math.random() > 0.8) {
                badge.textContent = current + 1;
            }
        });
    }, 5000);
}

function generateReport(type) {
    alert(`Generating ${type} report...\n\nThe report will include:\n- Collection statistics\n- Recycling rates\n- Fleet performance\n- Cost analysis\n- Environmental impact\n\nReport will be ready for download shortly.`);
}

document.querySelectorAll('.btn-danger')?.forEach(btn => {
    if (btn.textContent.includes('Disable')) {
        btn.addEventListener('click', function() {
            if (confirm('Are you sure you want to disable this user?')) {
                this.closest('tr').style.opacity = '0.5';
                this.textContent = 'Disabled';
                this.disabled = true;
            }
        });
    }
});

document.querySelectorAll('.btn-primary')?.forEach(btn => {
    if (btn.textContent.includes('Dispatch')) {
        btn.addEventListener('click', function() {
            alert('Dispatch order sent! Driver has been notified.');
            this.closest('.alert-item').style.opacity = '0.5';
            this.disabled = true;
            this.textContent = 'Dispatched';
        });
    }
});

function addNewBin() {
    const binId = prompt('Enter Bin ID (e.g., #020):');
    const location = prompt('Enter Location:');
    
    if (binId && location) {
        alert(`New bin ${binId} added at ${location}\nIoT sensors will be activated shortly.`);
    }
}

console.log('SmartBin Admin Dashboard Loaded');
console.log('Real-time IoT monitoring active');
console.log('Connected bins: 156');
console.log('Active drivers: 24');
