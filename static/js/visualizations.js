document.addEventListener('DOMContentLoaded', () => {
    const $navbarBurgers = Array.prototype.slice.call(document.querySelectorAll('.navbar-burger'), 0);
    if ($navbarBurgers.length > 0) {
        $navbarBurgers.forEach(el => {
            el.addEventListener('click', () => {
                const target = el.dataset.target;
                const $target = document.getElementById(target);
                el.classList.toggle('is-active');
                $target.classList.toggle('is-active');
            });
        });
    }

    fetch('/inventory/expiring_soon')
        .then(response => response.json())
        .then(data => {
            if (data.length > 0) {
                const ctx = document.getElementById('expiringSoonChart').getContext('2d');
                new Chart(ctx, {
                    type: 'pie',
                    data: {
                        labels: data.map(item => item.product_name),
                        datasets: [{
                            label: 'Total Litres',
                            data: data.map(item => item.total_litres),
                            backgroundColor: data.map(() => `rgba(${Math.floor(Math.random() * 255)}, ${Math.floor(Math.random() * 255)}, ${Math.floor(Math.random() * 255)}, 0.6)`),
                            borderColor: data.map(() => `rgba(0, 0, 0, 0.1)`),
                            borderWidth: 2
                        }]
                    },
                    options: {
                        responsive: true,
                        plugins: {
                            legend: {
                                position: 'right',
                                labels: {
                                    font: {
                                        size: 14
                                    },
                                    color: '#333'
                                }
                            },
                            tooltip: {
                                callbacks: {
                                    label: function(context) {
                                        let label = context.label || '';
                                        if (label) {
                                            label += ': ';
                                        }
                                        label += context.raw;
                                        return label;
                                    }
                                }
                            }
                        },
                        animation: {
                            animateScale: true,
                            animateRotate: true
                        },
                        scales: {
                            x: {
                                display: false // Hide x-axis labels
                            }
                        }
                    }
                });
            } else {
                document.getElementById('expiringSoonChart').parentElement.innerHTML = '<p>No products expiring soon.</p>';
            }
        });

    fetch('/inventory/below_threshold')
        .then(response => response.json())
        .then(data => {
            if (data.length > 0) {
                const ctx = document.getElementById('belowThresholdChart').getContext('2d');
                new Chart(ctx, {
                    type: 'line',
                    data: {
                        labels: data.map(item => item.product_name),
                        datasets: [{
                            label: 'Total Litres',
                            data: data.map(item => item.total_litres),
                            backgroundColor: 'rgba(54, 162, 235, 0.2)',
                            borderColor: 'rgba(54, 162, 235, 1)',
                            borderWidth: 1,
                            fill: true,
                            tension: 0.4
                        }]
                    },
                    options: {
                        responsive: true,
                        plugins: {
                            legend: {
                                position: 'top',
                            },
                            tooltip: {
                                callbacks: {
                                    label: function(context) {
                                        let label = context.label || '';
                                        if (label) {
                                            label += ': ';
                                        }
                                        label += context.raw;
                                        return label;
                                    }
                                }
                            }
                        },
                        scales: {
                            y: {
                                beginAtZero: true
                            },
                            x: {
                                display: false // Hide x-axis labels
                            }
                        }
                    }
                });
            } else {
                document.getElementById('belowThresholdChart').parentElement.innerHTML = '<p>No products below threshold.</p>';
            }
        });
});
