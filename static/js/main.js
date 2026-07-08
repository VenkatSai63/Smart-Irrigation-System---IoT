document.addEventListener("DOMContentLoaded", function() {
    
    // Sidebar toggle functionality
    var sidebar = document.getElementById('sidebar');
    var sidebarCollapse = document.getElementById('sidebarCollapse');
    
    if (sidebarCollapse && sidebar) {
        sidebarCollapse.addEventListener('click', function() {
            sidebar.classList.toggle('active');
        });
    }

    // Theme Switcher (Dark / Light Mode)
    var themeToggle = document.getElementById('themeToggle');
    var body = document.body;
    
    // Check saved preference or system theme
    var currentTheme = localStorage.getItem('theme');
    if (currentTheme === 'dark') {
        body.classList.add('dark-mode');
        body.classList.remove('light-mode');
        updateThemeIcon(true);
    } else {
        body.classList.add('light-mode');
        body.classList.remove('dark-mode');
        updateThemeIcon(false);
    }

    if (themeToggle) {
        themeToggle.addEventListener('click', function() {
            if (body.classList.contains('dark-mode')) {
                body.classList.remove('dark-mode');
                body.classList.add('light-mode');
                localStorage.setItem('theme', 'light');
                updateThemeIcon(false);
            } else {
                body.classList.remove('light-mode');
                body.classList.add('dark-mode');
                localStorage.setItem('theme', 'dark');
                updateThemeIcon(true);
            }
        });
    }

    function updateThemeIcon(isDark) {
        if (!themeToggle) return;
        var icon = themeToggle.querySelector('i');
        if (isDark) {
            icon.className = 'fa-solid fa-sun text-warning';
        } else {
            icon.className = 'fa-solid fa-moon';
        }
    }
});
