/**
 * Main application client scripts
 * Handles dynamic category fields toggling, tooltips, confirmations
 */

document.addEventListener('DOMContentLoaded', () => {
    // Dynamic form field switcher based on selected Category in Reminder form
    const categorySelect = document.getElementById('categorySelect');
    if (categorySelect) {
        const handleCategoryChange = () => {
            const val = categorySelect.value;

            const medicineSection = document.getElementById('medicineFields');
            const waterSection = document.getElementById('waterFields');
            const exerciseSection = document.getElementById('exerciseFields');
            const healthCheckSection = document.getElementById('healthCheckFields');

            if (medicineSection) medicineSection.style.display = (val === 'Medicine') ? 'block' : 'none';
            if (waterSection) waterSection.style.display = (val === 'Water') ? 'block' : 'none';
            if (exerciseSection) exerciseSection.style.display = (val === 'Exercise') ? 'block' : 'none';
            if (healthCheckSection) healthCheckSection.style.display = (val === 'Health Check') ? 'block' : 'none';
        };

        categorySelect.addEventListener('change', handleCategoryChange);
        handleCategoryChange(); // Run on initial load to reflect current selection
    }

    // Confirmation on destructive actions
    document.querySelectorAll('.btn-confirm-delete').forEach(btn => {
        btn.addEventListener('click', (e) => {
            if (!confirm('Are you sure you want to delete this item? This action cannot be undone.')) {
                e.preventDefault();
            }
        });
    });
});
