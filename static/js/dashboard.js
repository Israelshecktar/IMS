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
        window.location.href = '/inventory';
    });

    document.getElementById('addInventory').addEventListener('click', function() {
        window.location.href = '/add_inventory';
    });

    document.getElementById('updateInventory').addEventListener('click', function() {
        const id = prompt("Enter the ID of the inventory item to update:");
        if (id) {
            window.location.href = `/update_inventory/${id}`;
        }
    });

    document.getElementById('takeInventory').addEventListener('click', function() {
        window.location.href = '/take_inventory';
    });

    document.getElementById('viewReports').addEventListener('click', function() {
        window.location.href = '/report/inventory_levels';
    });

    document.getElementById('generateReport').addEventListener('click', function() {
        window.location.href = '/report/inventory_levels';
    });

    document.getElementById('deleteInventory').addEventListener('click', function() {
        const id = prompt("Enter the ID of the inventory item to delete:");
        if (id) {
            window.location.href = `/delete_inventory/${id}`;
        }
    });

    // Enhanced search functionality
    document.getElementById('searchButton').addEventListener('click', async function() {
        const query = document.getElementById('searchInput').value;
        const token = localStorage.getItem('jwtToken');

        const response = await fetch(`/inventory?material=${query}&product_name=${query}&location=${query}`, {
            method: 'GET',
            headers: {
                'Authorization': `Bearer ${token}`
            }
        });

        if (response.ok) {
            const data = await response.json();
            const searchResults = document.getElementById('searchResults');
            searchResults.innerHTML = ''; // Clear previous results

            data.items.forEach(item => {
                const column = document.createElement('div');
                column.className = 'column is-full-mobile is-half-tablet is-one-quarter-desktop';

                const card = document.createElement('div');
                card.className = 'card';

                const cardHeader = document.createElement('header');
                cardHeader.className = 'card-header';

                const cardHeaderTitle = document.createElement('p');
                cardHeaderTitle.className = 'card-header-title';
                cardHeaderTitle.textContent = item.product_name;

                const cardHeaderIcon = document.createElement('button');
                cardHeaderIcon.className = 'card-header-icon';
                cardHeaderIcon.setAttribute('aria-label', 'more options');

                const iconSpan = document.createElement('span');
                iconSpan.className = 'icon';

                const icon = document.createElement('i');
                icon.className = 'fas fa-angle-down';
                icon.setAttribute('aria-hidden', 'true');

                iconSpan.appendChild(icon);
                cardHeaderIcon.appendChild(iconSpan);
                cardHeader.appendChild(cardHeaderTitle);
                cardHeader.appendChild(cardHeaderIcon);

                const cardContent = document.createElement('div');
                cardContent.className = 'card-content';

                const content = document.createElement('div');
                content.className = 'content';

                const material = document.createElement('p');
                material.textContent = `Material: ${item.material}`;

                const location = document.createElement('p');
                location.textContent = `Location: ${item.location}`;

                const totalLitres = document.createElement('p');
                totalLitres.textContent = `Total Litres: ${item.total_litres}`;

                const dateReceived = document.createElement('p');
                dateReceived.textContent = `Date Received: ${new Date(item.date_received).toLocaleDateString()}`;

                const bestBeforeDate = document.createElement('p');
                bestBeforeDate.textContent = `Best Before Date: ${new Date(item.best_before_date).toLocaleDateString()}`;

                content.appendChild(material);
                content.appendChild(location);
                content.appendChild(totalLitres);
                content.appendChild(dateReceived);
                content.appendChild(bestBeforeDate);
                cardContent.appendChild(content);
                card.appendChild(cardHeader);
                card.appendChild(cardContent);
                column.appendChild(card);
                searchResults.appendChild(column);
            });
        } else {
            const data = await response.json();
            alert('Search failed: ' + data.message);
        }
    });

    // Filter functionality
    document.getElementById('filterButton').addEventListener('click', async function() {
        const material = document.getElementById('filterMaterial').value;
        const productName = document.getElementById('filterProductName').value;
        const location = document.getElementById('filterLocation').value;
        const token = localStorage.getItem('jwtToken');

        const response = await fetch(`/inventory?material=${material}&product_name=${productName}&location=${location}`, {
            method: 'GET',
            headers: {
                'Authorization': `Bearer ${token}`
            }
        });

        if (response.ok) {
            const data = await response.json();
            const searchResults = document.getElementById('searchResults');
            searchResults.innerHTML = ''; // Clear previous results

            data.items.forEach(item => {
                const column = document.createElement('div');
                column.className = 'column is-full-mobile is-half-tablet is-one-quarter-desktop';

                const card = document.createElement('div');
                card.className = 'card';

                const cardHeader = document.createElement('header');
                cardHeader.className = 'card-header';

                const cardHeaderTitle = document.createElement('p');
                cardHeaderTitle.className = 'card-header-title';
                cardHeaderTitle.textContent = item.product_name;

                const cardHeaderIcon = document.createElement('button');
                cardHeaderIcon.className = 'card-header-icon';
                cardHeaderIcon.setAttribute('aria-label', 'more options');

                const iconSpan = document.createElement('span');
                iconSpan.className = 'icon';

                const icon = document.createElement('i');
                icon.className = 'fas fa-angle-down';
                icon.setAttribute('aria-hidden', 'true');

                iconSpan.appendChild(icon);
                cardHeaderIcon.appendChild(iconSpan);
                cardHeader.appendChild(cardHeaderTitle);
                cardHeader.appendChild(cardHeaderIcon);

                const cardContent = document.createElement('div');
                cardContent.className = 'card-content';

                const content = document.createElement('div');
                content.className = 'content';

                const material = document.createElement('p');
                material.textContent = `Material: ${item.material}`;

                const location = document.createElement('p');
                location.textContent = `Location: ${item.location}`;

                const totalLitres = document.createElement('p');
                totalLitres.textContent = `Total Litres: ${item.total_litres}`;

                const dateReceived = document.createElement('p');
                dateReceived.textContent = `Date Received: ${new Date(item.date_received).toLocaleDateString()}`;

                const bestBeforeDate = document.createElement('p');
                bestBeforeDate.textContent = `Best Before Date: ${new Date(item.best_before_date).toLocaleDateString()}`;

                content.appendChild(material);
                content.appendChild(location);
                content.appendChild(totalLitres);
                content.appendChild(dateReceived);
                content.appendChild(bestBeforeDate);
                cardContent.appendChild(content);
                card.appendChild(cardHeader);
                card.appendChild(cardContent);
                column.appendChild(card);
                searchResults.appendChild(column);
            });
        } else {
            const data = await response.json();
            alert('Filter failed: ' + data.message);
        }
    });
});
