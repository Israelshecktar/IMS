document.addEventListener('DOMContentLoaded', () => {
    // Navbar Toggle
    const navbarBurgers = Array.prototype.slice.call(document.querySelectorAll('.navbar-burger'), 0);
    if (navbarBurgers.length > 0) {
        navbarBurgers.forEach(el => {
            el.addEventListener('click', () => {
                const target = el.dataset.target;
                const $target = document.getElementById(target);
                el.classList.toggle('is-active');
                $target.classList.toggle('is-active');
            });
        });
    }

    // Search Functionality
    const searchButton = document.getElementById('searchButton');
    searchButton.addEventListener('click', () => {
        const query = document.getElementById('searchInput').value;
        fetch(`/search?query=${query}`)
            .then(response => response.json())
            .then(data => {
                const searchResults = document.getElementById('searchResults');
                searchResults.innerHTML = '';
                data.forEach(item => {
                    const div = document.createElement('div');
                    div.className = 'column is-one-quarter';
                    div.innerHTML = `<div class="box">${item.name}</div>`;
                    searchResults.appendChild(div);
                });
            })
            .catch(error => console.error('Error:', error));
    });

    // Dropdown Functionality
    const $dropdowns = Array.prototype.slice.call(document.querySelectorAll('.dropdown:not(.is-hoverable)'), 0);
    if ($dropdowns.length > 0) {
        $dropdowns.forEach(el => {
            const trigger = el.querySelector('.dropdown-trigger');
            trigger.addEventListener('click', event => {
                event.stopPropagation();
                el.classList.toggle('is-active');
            });
        });

        document.addEventListener('click', event => {
            $dropdowns.forEach(el => {
                el.classList.remove('is-active');
            });
        });
    }

    // Logout Functionality
    const logoutButton = document.getElementById('logoutButton');
    logoutButton.addEventListener('click', () => {
        fetch('/logout', { method: 'POST' })
            .then(response => {
                if (response.ok) {
                    window.location.href = '/login';
                }
            })
            .catch(error => console.error('Error:', error));
    });

    // Inventory Management Links
    document.getElementById('viewInventory').addEventListener('click', () => {
        window.location.href = '/inventory';
    });
    document.getElementById('addInventory').addEventListener('click', () => {
        window.location.href = '/add_inventory';
    });
    document.getElementById('updateInventory').addEventListener('click', () => {
        window.location.href = '/update_inventory';
    });
    document.getElementById('deleteInventory').addEventListener('click', () => {
        window.location.href = '/delete_inventory';
    });

    // Reports and Analytics Links
    document.getElementById('viewReports').addEventListener('click', () => {
        window.location.href = '/report/inventory_levels';
    });
    document.getElementById('generateReport').addEventListener('click', () => {
        window.location.href = '/report/inventory_taken';
    });

    // Filter Functionality
    const filterButton = document.getElementById('filterButton');
    filterButton.addEventListener('click', () => {
        const material = document.getElementById('filterMaterial').value;
        const productName = document.getElementById('filterProductName').value;
        const location = document.getElementById('filterLocation').value;
        fetch(`/inventory?material=${material}&product_name=${productName}&location=${location}`)
            .then(response => response.json())
            .then(data => {
                const searchResults = document.getElementById('searchResults');
                searchResults.innerHTML = '';
                data.forEach(item => {
                    const div = document.createElement('div');
                    div.className = 'column is-one-quarter';
                    div.innerHTML = `<div class="box">${item.name}</div>`;
                    searchResults.appendChild(div);
                });
            })
            .catch(error => console.error('Error:', error));
    });

    // Notifications
    const notificationButton = document.querySelector('.fa-bell');
    notificationButton.addEventListener('click', () => {
        fetch('/notifications')
            .then(response => response.json())
            .then(data => {
                // Handle notifications
                console.log(data);
            })
            .catch(error => console.error('Error:', error));
    });

    // Dynamic Content Update
    function updateDashboard() {
        fetch('/dashboard_data')
            .then(response => response.json())
            .then(data => {
                document.querySelector('.total-items').textContent = `Total Items: ${data.total_items}`;
                document.querySelector('.pending-tasks').textContent = `Pending Tasks: ${data.pending_tasks}`;
                document.querySelector('.new-reports').textContent = `New Reports: ${data.new_reports}`;
                document.querySelector('.items-to-delete').textContent = `Items to Delete: ${data.items_to_delete}`;
            })
            .catch(error => console.error('Error:', error));
    }

    updateDashboard();
    setInterval(updateDashboard, 60000); // Update every minute

    // Error Handling
    function handleError(error) {
        console.error('Error:', error);
        alert('An error occurred. Please try again.');
    }
});
