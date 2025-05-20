const statusData = {
    labels: ['Pending', 'Confirmed', 'Parked Out', 'Cancelled/Rejected'],
    datasets: [{
        data: [
            {{ status_data.pending }},
    {{ status_data.confirmed }},
    {{ status_data.parked_out }},
{ { status_data.cancelled_rejected } }
            ],
backgroundColor: [
    'rgba(245, 158, 11, 0.4)',
    'rgba(16, 185, 129, 0.4)',
    'rgba(59, 130, 246, 0.4)',
    'rgba(239, 68, 68, 0.4)'

],

    borderWidth: 1
        }]
    };



new Chart(document.getElementById('reservationStatusChart'), {
    type: 'doughnut',  // or 'pie' if you prefer
    data: statusData,
    options: {
        responsive: true,
        cutout: '70%',  // For doughnut chart only
        maintainAspectRatio: true,
        aspectRatio: 5,
        plugins: {
            legend: {
                position: 'bottom',
            },
            title: {
                display: true,
                text: 'Reservation Status Distribution'
            },
            tooltip: {
                callbacks: {
                    label: function (context) {
                        const total = context.dataset.data.reduce((a, b) => a + b, 0);
                        const value = context.raw;
                        const percentage = Math.round((value / total) * 100);
                        return `${context.label}: ${value} (${percentage}%)`;
                    }
                }
            }
        },
        maintainAspectRatio: false
    }
});

// Get the data from Flask template
var spendingInfo = {{ spending_info | tojson }};

// Prepare the labels and data for the bar chart
var locations = spendingInfo.locations;
var totalSpending = spendingInfo.total_spending;

// Create the bar chart using Chart.js
var ctx = document.getElementById('totalSpendingChart').getContext('2d');


var totalSpendingChart = new Chart(ctx, {
    type: 'bar',
    data: {
        labels: locations,
        datasets: [{
            label: 'Total Spending (₹)',
            data: totalSpending,
            backgroundColor: 'rgba(54, 162, 235, 0.2)',
            borderColor: 'rgba(54, 162, 235, 1)',
            borderWidth: 1
        }]
    },
    options: {
        responsive: true,
        scales: {
            y: {
                beginAtZero: true
            }
        },
        plugins: {
            legend: {
                position: 'top',
            },
            tooltip: {
                callbacks: {
                    label: function (tooltipItem) {
                        return '₹' + tooltipItem.raw.toFixed(2);
                    }
                }
            }
        }
    }
});


var frequentInfo = {{ frequent_info | tojson }};

// Prepare the labels and data for the horizontal bar chart
var locations = frequentInfo.locations;
var reservationCounts = frequentInfo.reservation_counts;

// Create the horizontal bar chart using Chart.js
var ctx = document.getElementById('frequentLocationsChart').getContext('2d');
var frequentLocationsChart = new Chart(ctx, {
    type: 'bar',  // Horizontal bar chart
    data: {
        labels: locations,
        datasets: [{
            label: 'Number of Reservations',
            data: reservationCounts,
            backgroundColor: 'rgba(75, 192, 192, 0.2)',
            borderColor: 'rgba(75, 192, 192, 1)',
            borderWidth: 1
        }]
    },
    options: {
        responsive: true,
        indexAxis: 'y',  // This makes the bar chart horizontal
        scales: {
            x: {
                beginAtZero: true,
                ticks: {
                    stepSize: 1
                }
            },
            y: {
                title: {
                    display: true,
                    text: 'Parking Locations'
                }
            }
        },
        plugins: {
            legend: {
                position: 'top',
            },
            tooltip: {
                callbacks: {
                    label: function (tooltipItem) {
                        return tooltipItem.raw + ' reservations';
                    }
                }
            }
        }
    }
});



var vehicleInfo = {{ vehicle_info | tojson }};

// Prepare the labels and data for the bar chart
var vehicleNames = vehicleInfo.vehicle_names;
var reservationCounts = vehicleInfo.reservation_counts;

// Create the bar chart using Chart.js
var ctx = document.getElementById('vehicleUsageChart').getContext('2d');
var vehicleUsageChart = new Chart(ctx, {
    type: 'bar',  // Bar chart
    data: {
        labels: vehicleNames,
        datasets: [{
            label: 'Number of Reservations',
            data: reservationCounts,
            backgroundColor: 'rgba(153, 102, 255, 0.2)',
            borderColor: 'rgba(153, 102, 255, 1)',
            borderWidth: 1
        }]
    },
    options: {
        responsive: true,
        scales: {
            x: {
                title: {
                    display: true,
                    text: 'Vehicles'
                }
            },
            y: {
                beginAtZero: true,
                ticks: {
                    stepSize: 1
                },
                title: {
                    display: true,
                    text: 'Reservation Count'
                }
            }
        },
        plugins: {
            legend: {
                position: 'top',
            },
            tooltip: {
                callbacks: {
                    label: function (tooltipItem) {
                        return tooltipItem.raw + ' reservations';
                    }
                }
            }
        }
    }
});




// Common chart configuration
const chartConfig = {
    responsive: true,
    maintainAspectRatio: false,
    plugins: {
        legend: {
            position: 'top',
            labels: {
                font: {
                    family: "'Segoe UI', Tahoma, Geneva, Verdana, sans-serif",
                    size: 12
                },
                padding: 20
            }
        },
        tooltip: {
            backgroundColor: 'rgba(0,0,0,0.7)',
            titleFont: {
                family: "'Segoe UI', Tahoma, Geneva, Verdana, sans-serif",
                size: 14
            },
            bodyFont: {
                family: "'Segoe UI', Tahoma, Geneva, Verdana, sans-serif",
                size: 12
            },
            padding: 12,
            cornerRadius: 6
        }
    },
    scales: {
        y: {
            beginAtZero: true,
            grid: {
                color: 'rgba(0,0,0,0.05)'
            }
        },
        x: {
            grid: {
                color: 'rgba(0,0,0,0.05)'
            }
        }
    }
};

