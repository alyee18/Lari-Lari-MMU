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
                     
                   }
               }
           }
           
       });

       
   }

   fetchDashboardData();

   // Search functionality for orders
   document.getElementById('search').addEventListener('input', function () {
       const searchQuery = this.value.toLowerCase();
       const rows = document.querySelectorAll('#orders_table tbody tr');
       rows.forEach(row => {
           const cells = row.getElementsByTagName('td');
           let match = false;
           for (let i = 0; i < cells.length; i++) {
               if (cells[i].textContent.toLowerCase().includes(searchQuery)) {
                   match = true;
                   break;
               }
           }
           row.style.display = match ? '' : 'none';
       });
   });
});
