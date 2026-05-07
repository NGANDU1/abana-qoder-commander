document.addEventListener('DOMContentLoaded', function() {
    const tabBtns = document.querySelectorAll('.tab-btn');
    const authForms = document.querySelectorAll('.auth-form');
    const loginForm = document.getElementById('loginForm');
    const registerForm = document.getElementById('registerForm');

    tabBtns.forEach(btn => {
        btn.addEventListener('click', function() {
            const tab = this.dataset.tab;
            
            tabBtns.forEach(b => b.classList.remove('active'));
            authForms.forEach(f => f.classList.remove('active'));
            
            this.classList.add('active');
            document.getElementById(tab + 'Form').classList.add('active');
        });
    });

    loginForm.addEventListener('submit', function(e) {
        e.preventDefault();
        const email = document.getElementById('loginEmail').value;
        const password = document.getElementById('loginPassword').value;
        const role = document.getElementById('loginRole').value;

        if (!role) {
            alert('Please select a role');
            return;
        }

        localStorage.setItem('userRole', role);
        localStorage.setItem('userEmail', email);
        localStorage.setItem('isLoggedIn', 'true');

        switch(role) {
            case 'citizen':
                window.location.href = 'citizen.html';
                break;
            case 'driver':
                window.location.href = 'driver.html';
                break;
            case 'admin':
                window.location.href = 'admin.html';
                break;
        }
    });

    registerForm.addEventListener('submit', function(e) {
        e.preventDefault();
        const firstName = document.getElementById('regFirstName').value;
        const lastName = document.getElementById('regLastName').value;
        const email = document.getElementById('regEmail').value;
        const phone = document.getElementById('regPhone').value;
        const role = document.getElementById('regRole').value;
        const address = document.getElementById('regAddress').value;
        const password = document.getElementById('regPassword').value;
        const confirmPassword = document.getElementById('regConfirmPassword').value;

        if (password !== confirmPassword) {
            alert('Passwords do not match!');
            return;
        }

        if (!document.getElementById('agreeTerms').checked) {
            alert('Please agree to the Terms & Conditions');
            return;
        }

        alert('Registration successful! Please login with your credentials.');
        
        document.querySelector('[data-tab="login"]').click();
        
        registerForm.reset();
    });
});
