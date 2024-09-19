document.addEventListener('DOMContentLoaded', () => {
    fetchDashboardData();
    fetchFinancialData();
});

async function fetchDashboardData() {
    try {
        const response = await fetch('/api/dashboard_data');
        const data = await response.json();
        updateCharts(data);
    } catch (error) {
        console.error('Error fetching dashboard data:', error);
    }
}

function updateCharts(data) {
    const numOrders = data.num_orders;
    const numRunners = data.num_runners;
    const numBuyers = data.num_buyers;
    const numSellers = data.num_sellers;

    // Bar Chart - Summary
    const ctxSummary = document.getElementById('summaryChart').getContext('2d');
    new Chart(ctxSummary, {
        type: 'bar',
        data: {
            labels: ['Orders', 'Runners', 'Buyers', 'Sellers'],
            datasets: [{
                label: 'Counts',
                data: [numOrders, numRunners, numBuyers, numSellers],
                backgroundColor: [
                    'rgba(255, 99, 132, 0.2)',
                    'rgba(54, 162, 235, 0.2)',
                    'rgba(255, 206, 86, 0.2)',
                    'rgba(75, 192, 192, 0.2)'
                ],
                borderColor: [
                    'rgba(255, 99, 132, 1)',
                    'rgba(54, 162, 235, 1)',
                    'rgba(255, 206, 86, 1)',
                    'rgba(75, 192, 192, 1)'
                ],
                borderWidth: 1
            }]
        },
        options: {
            scales: {
                y: {
                  beginAtZero: true,
                    ticks:{
                     stepSize: 1,
                     callback: function(value) {
                        return Number.isInteger(value) ? value : '';
                     }
                    }
                   }
            }
        }
    });
}

function fetchFinancialData() {
    const financialDataText = document.getElementById('financialData').textContent;
    const financialData = JSON.parse(financialDataText);
    updateFinancialCharts(financialData);
}

function updateFinancialCharts(financialData) {
    const labels = Object.keys(financialData);
    const earningsData = Object.values(financialData).map(r => r.total_earnings);
    const ordersData = Object.values(financialData).map(r => r.total_orders);

    // Pie Chart - Total Earnings
    const ctxEarnings = document.getElementById('earningsChart').getContext('2d');
    new Chart(ctxEarnings, {
        type: 'pie',
        data: {
            labels: labels,
            datasets: [{
                label: 'Total Earnings',
                data: earningsData,
                backgroundColor: [
                    'rgba(255, 99, 132, 0.2)',
                    'rgba(54, 162, 235, 0.2)',
                    'rgba(255, 206, 86, 0.2)',
                    'rgba(75, 192, 192, 0.2)',
                    'rgba(153, 102, 255, 0.2)',
                    'rgba(255, 159, 64, 0.2)'
                ],
                borderColor: [
                    'rgba(255, 99, 132, 1)',
                    'rgba(54, 162, 235, 1)',
                    'rgba(255, 206, 86, 1)',
                    'rgba(75, 192, 192, 1)',
                    'rgba(153, 102, 255, 1)',
                    'rgba(255, 159, 64, 1)'
                ],
                borderWidth: 1
            }]
        }
    });

    // Pie Chart - Total Orders
    const ctxOrders = document.getElementById('ordersChart').getContext('2d');
    new Chart(ctxOrders, {
        type: 'pie',
        data: {
            labels: labels,
            datasets: [{
                label: 'Total Orders',
                data: ordersData,
                backgroundColor: [
                    'rgba(255, 99, 132, 0.2)',
                    'rgba(54, 162, 235, 0.2)',
                    'rgba(255, 206, 86, 0.2)',
                    'rgba(75, 192, 192, 0.2)',
                    'rgba(153, 102, 255, 0.2)',
                    'rgba(255, 159, 64, 0.2)'
                ],
                borderColor: [
                    'rgba(255, 99, 132, 1)',
                    'rgba(54, 162, 235, 1)',
                    'rgba(255, 206, 86, 1)',
                    'rgba(75, 192, 192, 1)',
                    'rgba(153, 102, 255, 1)',
                    'rgba(255, 159, 64, 1)'
                ],
                borderWidth: 1
            }]
        }
    });
}