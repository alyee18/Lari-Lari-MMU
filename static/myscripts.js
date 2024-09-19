document.addEventListener('DOMContentLoaded', () => {
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
        // Example data structure
        const numOrders = data.num_orders;
        const numRunners = data.num_runners;
        const numBuyers = data.num_buyers;
        const numSellers = data.num_sellers;
        const financialData = data.financial_data; // Ensure this is an object with restaurant data

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

        // Pie Chart - Financial Overview
        const ctxFinancial = document.getElementById('financialOverviewChart').getContext('2d');
        new Chart(ctxFinancial, {
            type: 'pie',
            data: {
                labels: Object.keys(financialData),
                datasets: [{
                    label: 'Financial Overview',
                    data: Object.values(financialData).map(r => r.total_earnings),
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

    fetchDashboardData();
});
