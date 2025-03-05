// Dark Mode Toggle
const darkModeToggle = document.getElementById('darkModeToggle');
const body = document.body;

darkModeToggle.addEventListener('click', () => {
    body.classList.toggle('dark-mode');
    const isDarkMode = body.classList.contains('dark-mode');
    darkModeToggle.innerHTML = isDarkMode ? '<i class="bi bi-sun"></i>' : '<i class="bi bi-moon-stars"></i>';
    localStorage.setItem('darkMode', isDarkMode ? 'enabled' : 'disabled');
    updateCharts();
});

// Load Dark Mode Preference
if (localStorage.getItem('darkMode') === 'enabled') {
    body.classList.add('dark-mode');
    darkModeToggle.innerHTML = '<i class="bi bi-sun"></i>';
}

// Client-side validation for URL input
document.querySelector('form')?.addEventListener('submit', function(e) {
    const urlInput = document.querySelector('input[name="original_url"]');
    if (urlInput && !urlInput.value.match(/^https?:\/\//)) {
        e.preventDefault();
        alert('Please enter a valid URL starting with http:// or https://');
    } else {
        const button = document.querySelector('button[type="submit"]');
        if (button) {
            button.innerHTML = '<i class="bi bi-arrow-repeat me-2"></i>Shortening...';
            button.disabled = true;
        }
    }
});

// Update charts for dark mode
function updateCharts() {
    const charts = [Chart.getChart('clickTrendsChart'), Chart.getChart('deviceChart'), Chart.getChart('geoChart')];
    const isDarkMode = body.classList.contains('dark-mode');
    charts.forEach(chart => {
        if (chart) {
            chart.options.scales.x.title.color = isDarkMode ? '#e0e0e0' : '#333';
            chart.options.scales.x.ticks.color = isDarkMode ? '#e0e0e0' : '#333';
            chart.options.scales.y.title.color = isDarkMode ? '#e0e0e0' : '#333';
            chart.options.scales.y.ticks.color = isDarkMode ? '#e0e0e0' : '#333';
            chart.options.plugins.legend.labels.color = isDarkMode ? '#e0e0e0' : '#333';
            chart.update();
        }
    });
}