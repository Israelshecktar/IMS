document.getElementById('showRegisterForm').addEventListener('click', function(event) {
    event.preventDefault();
    window.location.href = '/register';
});

document.getElementById('showLoginForm').addEventListener('click', function(event) {
    event.preventDefault();
    window.location.href = '/login';
});

document.getElementById('register-form').addEventListener('submit', async function(event) {
    event.preventDefault();
    const username = document.querySelector('input[name="username"]').value;
    const email = document.querySelector('input[name="email"]').value;
    const password = document.querySelector('input[name="password"]').value;
    const confirmPassword = document.querySelector('input[name="confirm_password"]').value;
    const role = document.querySelector('select[name="role"]').value;

    if (password !== confirmPassword) {
        showFlashMessage('Passwords do not match.', 'is-danger');
        return;
    }

    const response = await fetch('/register', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/x-www-form-urlencoded'
        },
        body: `username=${encodeURIComponent(username)}&email=${encodeURIComponent(email)}&password=${encodeURIComponent(password)}&role=${encodeURIComponent(role)}`
    });

    if (response.ok) {
        showFlashMessage('Registration successful!', 'is-success');
        document.getElementById('register-form').reset();
        window.location.href = '/login';
    } else {
        showFlashMessage('Registration failed: Please check the details and try again.', 'is-danger');
    }
});

function showFlashMessage(message, type) {
    const flashMessage = document.getElementById('flash-message');
    flashMessage.textContent = message;
    flashMessage.className = `notification ${type}`;
    flashMessage.classList.remove('is-hidden');
    setTimeout(() => {
        flashMessage.classList.add('is-hidden');
    }, 3000);
}


document.getElementById('login-form').addEventListener('submit', async function(event) {
    event.preventDefault();
    const username = document.querySelector('input[name="username"]').value;
    const password = document.querySelector('input[name="password"]').value;

    const response = await fetch('/login', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/x-www-form-urlencoded'
        },
        body: `username=${encodeURIComponent(username)}&password=${encodeURIComponent(password)}`
    });

    if (response.ok) {
        showFlashMessage('Login successful!', 'is-success');
        window.location.href = '/dashboard';
    } else {
        showFlashMessage('Login failed: Invalid credentials.', 'is-danger');
    }
});

function showFlashMessage(message, type) {
    const flashMessage = document.getElementById('flash-message');
    flashMessage.textContent = message;
    flashMessage.className = `notification ${type}`;
    flashMessage.classList.remove('is-hidden');
    setTimeout(() => {
        flashMessage.classList.add('is-hidden');
    }, 3000);
}
