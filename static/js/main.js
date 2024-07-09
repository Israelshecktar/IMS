document.getElementById('showRegisterForm').addEventListener('click', function(event) {
    event.preventDefault();
    document.getElementById('loginSection').style.display = 'none';
    document.getElementById('registerSection').style.display = 'block';
});

document.getElementById('showLoginForm').addEventListener('click', function(event) {
    event.preventDefault();
    document.getElementById('registerSection').style.display = 'none';
    document.getElementById('loginSection').style.display = 'block';
});

document.getElementById('loginForm').addEventListener('submit', async function(event) {
    event.preventDefault();
    const username = document.getElementById('username').value;
    const password = document.getElementById('password').value;

    const response = await fetch('/auth/login', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify({ username, password })
    });

    const data = await response.json();
    if (response.ok) {
        localStorage.setItem('jwtToken', data.access_token);
        alert('Login successful!');
        window.location.href = '/dashboard';
    } else {
        alert('Login failed: ' + data.message);
    }
});

document.getElementById('registerForm').addEventListener('submit', async function(event) {
    event.preventDefault();
    const username = document.getElementById('reg_username').value;
    const email = document.getElementById('reg_email').value;
    const password = document.getElementById('reg_password').value;
    const role = document.getElementById('reg_role').value;

    const response = await fetch('/auth/register', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify({ username, email, password, role })
    });

    const data = await response.json();
    if (response.ok) {
        alert('Registration successful!');
        document.getElementById('registerForm').reset();
        document.getElementById('registerSection').style.display = 'none';
        document.getElementById('loginSection').style.display = 'block';
    } else {
        alert('Registration failed: ' + data.message);
    }
});

document.getElementById('fetchInventory').addEventListener('click', async function() {
    const token = localStorage.getItem('jwtToken');
    const response = await fetch('/inventory', {
        headers: {
            'Authorization': `Bearer ${token}`
        }
    });

    const data = await response.json();
    if (response.ok) {
        const inventoryData = document.getElementById('inventoryData');
        inventoryData.innerHTML = '<pre>' + JSON.stringify(data, null, 2) + '</pre>';
    } else {
        alert('Failed to fetch inventory: ' + data.message);
    }
});
