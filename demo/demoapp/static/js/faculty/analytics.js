/**
 * Faculty Analytics Dashboard Charts
 * 
 * This file contains the code for initializing and rendering all charts
 * on the faculty analytics dashboard.
 */

document.addEventListener('DOMContentLoaded', function() {
    // Configuration options shared across charts
    const chartOptions = {
        responsive: true,
        maintainAspectRatio: false,
        plugins: {
            legend: {
                position: 'top',
            },
            tooltip: {
                mode: 'index',
                intersect: false
            }
        }
    };
    
    // Chart 1: Popular Equipment (Top 10)
    function initPopularEquipmentChart() {
        const ctx = document.getElementById('popularEquipmentChart');
        if (!ctx) return; // Skip if element doesn't exist
        
        const data = JSON.parse(document.getElementById('popular-equipment-data').textContent);
        
        new Chart(ctx.getContext('2d'), {
            type: 'bar',
            data: {
                labels: data.map(item => item.equipment__name),
                datasets: [{
                    label: 'Usage Count',
                    data: data.map(item => item.usage_count),
                    backgroundColor: 'rgba(54, 162, 235, 0.5)',
                    borderColor: 'rgba(54, 162, 235, 1)',
                    borderWidth: 1
                }]
            },
            options: {
                ...chartOptions,
                scales: {
                    y: {
                        beginAtZero: true,
                        title: {
                            display: true,
                            text: 'Number of Reservations'
                        }
                    },
                    x: {
                        title: {
                            display: true,
                            text: 'Equipment'
                        }
                    }
                }
            }
        });
    }
    
    // Chart 2: Underutilized Equipment
    function initUnderutilizedEquipmentChart() {
        const ctx = document.getElementById('underutilizedEquipmentChart');
        if (!ctx) return; // Skip if element doesn't exist
        
        const data = JSON.parse(document.getElementById('underutilized-equipment-data').textContent);
        
        new Chart(ctx.getContext('2d'), {
            type: 'bar',
            data: {
                labels: data.map(item => item.name),
                datasets: [{
                    label: 'Usage Count',
                    data: data.map(item => item.usage_count),
                    backgroundColor: 'rgba(255, 99, 132, 0.5)',
                    borderColor: 'rgba(255, 99, 132, 1)',
                    borderWidth: 1
                }]
            },
            options: {
                ...chartOptions,
                scales: {
                    y: {
                        beginAtZero: true,
                        title: {
                            display: true,
                            text: 'Number of Reservations'
                        }
                    },
                    x: {
                        title: {
                            display: true,
                            text: 'Equipment'
                        }
                    }
                }
            }
        });
    }
    
    // Chart 3: Category Usage - Removed as we're now using a table instead
    
    // Chart 4: Reservation Duration Statistics
    function initDurationStatisticsChart() {
        const ctx = document.getElementById('durationStatisticsChart');
        if (!ctx) return; // Skip if element doesn't exist
        
        const data = JSON.parse(document.getElementById('duration-statistics-data').textContent);
        
        // Group durations into buckets for histogram
        const buckets = {
            '0-1 hours': 0,
            '1-2 hours': 0,
            '2-4 hours': 0,
            '4-8 hours': 0,
            '8+ hours': 0
        };
        
        data.forEach(duration => {
            if (duration <= 1) buckets['0-1 hours']++;
            else if (duration <= 2) buckets['1-2 hours']++;
            else if (duration <= 4) buckets['2-4 hours']++;
            else if (duration <= 8) buckets['4-8 hours']++;
            else buckets['8+ hours']++;
        });
        
        new Chart(ctx.getContext('2d'), {
            type: 'bar',
            data: {
                labels: Object.keys(buckets),
                datasets: [{
                    label: 'Number of Reservations',
                    data: Object.values(buckets),
                    backgroundColor: 'rgba(75, 192, 192, 0.5)',
                    borderColor: 'rgba(75, 192, 192, 1)',
                    borderWidth: 1
                }]
            },
            options: {
                ...chartOptions,
                scales: {
                    y: {
                        beginAtZero: true,
                        title: {
                            display: true,
                            text: 'Number of Reservations'
                        }
                    },
                    x: {
                        title: {
                            display: true,
                            text: 'Duration'
                        }
                    }
                }
            }
        });
    }
    
    // Chart 5: Reservation Status Distribution
    function initStatusDistributionChart() {
        const ctx = document.getElementById('statusDistributionChart');
        if (!ctx) return; // Skip if element doesn't exist
        
        const data = JSON.parse(document.getElementById('status-distribution-data').textContent);
        
        new Chart(ctx.getContext('2d'), {
            type: 'doughnut',
            data: {
                labels: Object.keys(data),
                datasets: [{
                    data: Object.values(data),
                    backgroundColor: [
                        'rgba(255, 99, 132, 0.5)',
                        'rgba(54, 162, 235, 0.5)',
                        'rgba(255, 206, 86, 0.5)',
                        'rgba(75, 192, 192, 0.5)',
                        'rgba(153, 102, 255, 0.5)',
                        'rgba(255, 159, 64, 0.5)'
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
            },
            options: chartOptions
        });
    }
    
    // Initialize all charts
    try {
        initPopularEquipmentChart();
        initUnderutilizedEquipmentChart();
        // Category usage is now a table, so we don't initialize that chart
        initDurationStatisticsChart();
        initStatusDistributionChart();
        
        console.log('All charts initialized successfully');
    } catch (error) {
        console.error('Error initializing charts:', error);
    }
});
