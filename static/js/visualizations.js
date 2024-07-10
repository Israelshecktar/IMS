document.addEventListener('DOMContentLoaded', function() {
    const ctx = document.getElementById('inventoryChart').getContext('2d');
    const inventoryChart = new Chart(ctx, {
        type: 'bar',
        data: {
            labels: ['HEMPATHANE HS 55619 RAL 3000', 'HEMPEL CURING AGENT 95370-00000', 'HEMPADUR THINNER 08450 IMPR', 'HEMPEL 08080-0000 THINNER FINISH 1L'],
            datasets: [{
                label: 'Inventory Levels',
                data: [120, 150, 180, 90],
                backgroundColor: [
                    'rgba(54, 162, 235, 0.2)',
                    'rgba(255, 206, 86, 0.2)',
                    'rgba(75, 192, 192, 0.2)',
                    'rgba(153, 102, 255, 0.2)'
                ],
                borderColor: [
                    'rgba(54, 162, 235, 1)',
                    'rgba(255, 206, 86, 1)',
                    'rgba(75, 192, 192, 1)',
                    'rgba(153, 102, 255, 1)'
                ],
                borderWidth: 1
            }]
        },
        options: {
            scales: {
                y: {
                    beginAtZero: true
                }
            }
        }
    });
});
