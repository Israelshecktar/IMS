document.addEventListener('DOMContentLoaded', function() {
    const username = localStorage.getItem('username');
    document.getElementById('username').textContent = username;

    document.getElementById('logoutButton').addEventListener('click', async function() {
        const token = localStorage.getItem('jwtToken');

        const response = await fetch('/auth/logout', {
            method: 'POST',
            headers: {
                'Authorization': `Bearer ${token}`
            }
        });

        if (response.ok) {
            localStorage.removeItem('jwtToken');
            alert('Logout successful!');
            window.location.href = '/';
        } else {
            const data = await response.json();
            alert('Logout failed: ' + data.message);
        }
    });

    document.getElementById('updateProfile').addEventListener('click', function() {
        window.location.href = '/update_profile';
    });

    document.getElementById('viewInventory').addEventListener('click', function() {
        window.location.href = '/inventory/view';
    });

    document.getElementById('addInventory').addEventListener('click', function() {
        window.location.href = '/inventory/add';
    });

    document.getElementById('updateInventory').addEventListener('click', function() {
        window.location.href = '/inventory/update';
    });

    document.getElementById('takeInventory').addEventListener('click', function() {
        window.location.href = '/inventory/take';
    });

    document.getElementById('viewReports').addEventListener('click', function() {
        window.location.href = '/reports/view';
    });

    document.getElementById('generateReport').addEventListener('click', function() {
        window.location.href = '/reports/generate';
    });

    document.getElementById('deleteInventory').addEventListener('click', function() {
        window.location.href = '/inventory/delete';
    });
});
