document.addEventListener('DOMContentLoaded', function() {
    const adminCheckbox = document.getElementById('is_admin');
    const adminCodeField = document.querySelector('.admin-code-field');

    if (adminCheckbox && adminCodeField) {
        adminCheckbox.addEventListener('change', function() {
            if (this.checked) {
                adminCodeField.style.display = 'block';
                setTimeout(() => adminCodeField.classList.add('visible'), 50);
            } else {
                adminCodeField.classList.remove('visible');
                setTimeout(() => adminCodeField.style.display = 'none', 300);
            }
        });
    }
});

// Sidebar toggle functionality
document.addEventListener('DOMContentLoaded', function() {
    const sidebarToggle = document.getElementById('navbarSidebarToggle');
    const sidebar = document.getElementById('sidebar');
    const mainContent = document.querySelector('main.container');
    
    // Check if sidebar state is stored in localStorage
    const sidebarCollapsed = localStorage.getItem('sidebarCollapsed') === 'true';
    
    // Apply initial state
    if (sidebarCollapsed) {
        sidebar.classList.add('collapsed');
        mainContent.classList.add('expanded');
        document.body.classList.add('sidebar-collapsed');
    } else {
        document.body.classList.add('sidebar-visible');
    }
    
    sidebarToggle.addEventListener('click', function() {
        sidebar.classList.toggle('collapsed');
        mainContent.classList.toggle('expanded');
        document.body.classList.toggle('sidebar-collapsed');
        document.body.classList.toggle('sidebar-visible');
        
        // Store state in localStorage
        localStorage.setItem('sidebarCollapsed', sidebar.classList.contains('collapsed'));
    });
});