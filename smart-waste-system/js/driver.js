document.addEventListener('DOMContentLoaded', function() {
    if (!localStorage.getItem('isLoggedIn')) {
        window.location.href = 'index.html';
        return;
    }
    
    const role = localStorage.getItem('userRole');
    if (role !== 'driver') {
        window.location.href = 'index.html';
        return;
    }
    
    const email = localStorage.getItem('userEmail');
    if (email) {
        const name = email.split('@')[0].replace(/\./g, ' ');
        const initials = name.split(' ').map(n => n[0]).join('').toUpperCase();
        document.querySelectorAll('.user-avatar').forEach(el => el.textContent = initials);
        document.querySelectorAll('.top-bar-actions .user-dropdown div:first-child').forEach(el => {
            el.innerHTML = `<div style="font-weight: 600; font-size: 0.9rem;">${name}</div><div style="font-size: 0.8rem; color: var(--gray);">Driver</div>`;
        });
    }
    
    loadDriverData();
    startSimulation();
});

function loadDriverData() {
    const today = new Date();
    const dateStr = today.toISOString().split('T')[0];
    document.getElementById('todayDate')?.setTextContent(dateStr);
}

function startNavigation(address) {
    showPage('navigation');
    const destElement = document.getElementById('currentDestination');
    if (destElement) {
        destElement.textContent = address;
    }
    
    simulateNavigation();
}

function simulateNavigation() {
    const distanceEl = document.querySelector('#page-navigation .nav-detail:nth-child(1) span');
    const etaEl = document.querySelector('#page-navigation .nav-detail:nth-child(2) span');
    
    if (distanceEl && etaEl) {
        let distance = 2.3;
        let eta = 8;
        
        const interval = setInterval(() => {
            if (!document.getElementById('page-navigation').classList.contains('active')) {
                clearInterval(interval);
                return;
            }
            
            distance -= 0.1;
            eta -= 1;
            
            if (distance <= 0) {
                distance = 0;
                eta = 0;
                clearInterval(interval);
                alert('You have arrived at your destination!');
            }
            
            distanceEl.textContent = `Distance: ${distance.toFixed(1)} km`;
            etaEl.textContent = `ETA: ${eta} minutes`;
        }, 3000);
    }
}

function stopNavigation() {
    if (confirm('Are you sure you want to end navigation?')) {
        showPage('dashboard');
    }
}

function confirmCollection(event) {
    event.preventDefault();
    
    const binId = document.getElementById('confirmBinId').value;
    const location = document.getElementById('confirmLocation').value;
    const wasteType = document.getElementById('confirmWasteType').value;
    const weight = document.getElementById('confirmWeight').value;
    const condition = document.getElementById('binCondition').value;
    
    if (!weight) {
        alert('Please enter the weight collected');
        return;
    }
    
    const collectionData = {
        id: 'COL-' + Date.now(),
        binId,
        location,
        wasteType,
        weight,
        condition,
        driver: localStorage.getItem('userEmail'),
        timestamp: new Date().toISOString()
    };
    
    let collections = JSON.parse(localStorage.getItem('collections') || '[]');
    collections.push(collectionData);
    localStorage.setItem('collections', JSON.stringify(collections));
    
    alert(`Collection confirmed!\nCollection ID: ${collectionData.id}\nWeight: ${weight}kg`);
    event.target.reset();
    
    const stats = document.getElementById('completedToday');
    if (stats) {
        const current = parseInt(stats.textContent);
        stats.textContent = current + 1;
    }
}

document.getElementById('driverProfileForm')?.addEventListener('submit', function(e) {
    e.preventDefault();
    const firstName = document.getElementById('driverFirstName').value;
    const lastName = document.getElementById('driverLastName').value;
    
    const initials = (firstName[0] + lastName[0]).toUpperCase();
    document.querySelectorAll('.user-avatar').forEach(el => el.textContent = initials);
    
    alert('Profile updated successfully!');
});

function startSimulation() {
    setInterval(() => {
        const badges = document.querySelectorAll('.notification-badge');
        badges.forEach(badge => {
            const current = parseInt(badge.textContent);
            if (Math.random() > 0.7) {
                badge.textContent = current + 1;
            }
        });
    }, 10000);
}
