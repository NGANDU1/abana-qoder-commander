document.addEventListener('DOMContentLoaded', function() {
    if (!localStorage.getItem('isLoggedIn')) {
        window.location.href = 'index.html';
        return;
    }
    
    const role = localStorage.getItem('userRole');
    if (role !== 'citizen') {
        window.location.href = 'index.html';
        return;
    }
    
    const email = localStorage.getItem('userEmail');
    if (email) {
        const name = email.split('@')[0].replace(/\./g, ' ');
        const initials = name.split(' ').map(n => n[0]).join('').toUpperCase();
        document.querySelectorAll('.user-avatar').forEach(el => el.textContent = initials);
        document.querySelectorAll('.top-bar-actions .user-dropdown div:first-child').forEach(el => {
            el.innerHTML = `<div style="font-weight: 600; font-size: 0.9rem;">${name}</div><div style="font-size: 0.8rem; color: var(--gray);">Citizen</div>`;
        });
    }
    
    loadDashboardData();
    
    setTimeout(() => {
        if (document.getElementById('wasteChart') && !charts.wasteChart) {
            initWasteChart();
        }
    }, 500);
});

function loadDashboardData() {
    const today = new Date();
    const tomorrow = new Date(today);
    tomorrow.setDate(tomorrow.getDate() + 2);
    const dateInput = document.getElementById('pickupDate');
    if (dateInput) {
        dateInput.min = today.toISOString().split('T')[0];
        dateInput.value = tomorrow.toISOString().split('T')[0];
    }
}

function submitPickup(event) {
    event.preventDefault();
    
    const wasteType = document.getElementById('wasteType').value;
    const weight = document.getElementById('wasteWeight').value;
    const address = document.getElementById('pickupAddress').value;
    const date = document.getElementById('pickupDate').value;
    const time = document.getElementById('pickupTime').value;
    
    if (!wasteType || !weight || !address || !date || !time) {
        alert('Please fill in all required fields');
        return;
    }
    
    const pickupData = {
        id: 'PK-' + Date.now(),
        wasteType,
        weight,
        address,
        date,
        time,
        status: 'pending',
        createdAt: new Date().toISOString()
    };
    
    let pickups = JSON.parse(localStorage.getItem('pickupRequests') || '[]');
    pickups.push(pickupData);
    localStorage.setItem('pickupRequests', JSON.stringify(pickups));
    
    alert(`Pickup request submitted successfully!\nRequest ID: ${pickupData.id}\nYou will receive a confirmation notification.`);
    event.target.reset();
    
    const tomorrow = new Date();
    tomorrow.setDate(tomorrow.getDate() + 2);
    document.getElementById('pickupDate').value = tomorrow.toISOString().split('T')[0];
}

function submitComplaint(event) {
    event.preventDefault();
    
    const issueType = document.getElementById('issueType').value;
    const location = document.getElementById('issueLocation').value;
    const description = document.getElementById('issueDescription').value;
    const priority = document.getElementById('issuePriority').value;
    
    if (!issueType || !location || !description) {
        alert('Please fill in all required fields');
        return;
    }
    
    const complaintData = {
        id: 'C-' + Date.now(),
        issueType,
        location,
        description,
        priority,
        status: 'open',
        createdAt: new Date().toISOString(),
        photo: document.getElementById('photoUpload').files[0]?.name || null
    };
    
    let complaints = JSON.parse(localStorage.getItem('complaints') || '[]');
    complaints.push(complaintData);
    localStorage.setItem('complaints', JSON.stringify(complaints));
    
    alert(`Complaint submitted successfully!\nComplaint ID: ${complaintData.id}\nOur team will review it shortly.`);
    event.target.reset();
    document.getElementById('photoPreview').innerHTML = '';
}

function processPayment(event) {
    event.preventDefault();
    
    const method = document.getElementById('paymentMethod').value;
    const amount = document.getElementById('paymentAmount').value;
    
    if (!method || !amount) {
        alert('Please fill in all required fields');
        return;
    }
    
    const paymentData = {
        id: 'TXN-' + Date.now(),
        method,
        amount,
        status: 'completed',
        date: new Date().toISOString()
    };
    
    let payments = JSON.parse(localStorage.getItem('payments') || '[]');
    payments.push(paymentData);
    localStorage.setItem('payments', JSON.stringify(payments));
    
    alert(`Payment processed successfully!\nTransaction ID: ${paymentData.id}\nAmount: $${amount}`);
    event.target.reset();
}

function previewPhoto(event) {
    const file = event.target.files[0];
    if (file) {
        if (file.size > 5 * 1024 * 1024) {
            alert('File size exceeds 5MB limit!');
            event.target.value = '';
            return;
        }
        
        const reader = new FileReader();
        reader.onload = function(e) {
            const preview = document.getElementById('photoPreview');
            if (preview) {
                preview.innerHTML = `
                    <div style="position: relative; display: inline-block;">
                        <img src="${e.target.result}" style="max-width: 200px; border-radius: 8px; margin-top: 10px;">
                        <button onclick="removePhoto()" style="position: absolute; top: 5px; right: 5px; background: var(--danger); color: white; border: none; border-radius: 50%; width: 25px; height: 25px; cursor: pointer;">×</button>
                    </div>
                `;
            }
        };
        reader.readAsDataURL(file);
    }
}

function removePhoto() {
    document.getElementById('photoUpload').value = '';
    document.getElementById('photoPreview').innerHTML = '';
}

document.getElementById('profileForm')?.addEventListener('submit', function(e) {
    e.preventDefault();
    const firstName = document.getElementById('profileFirstName').value;
    const lastName = document.getElementById('profileLastName').value;
    const email = document.getElementById('profileEmail').value;
    
    localStorage.setItem('userEmail', email);
    
    const initials = (firstName[0] + lastName[0]).toUpperCase();
    document.querySelectorAll('.user-avatar').forEach(el => el.textContent = initials);
    
    alert('Profile updated successfully!');
});
