// Utility function for smooth scrolling
document.getElementById("exploreBtn")?.addEventListener("click", function () {
  document.getElementById("quickSection")?.scrollIntoView({
    behavior: "smooth"
  });
});

// Filtering logic for Government Schemes
const filterSchemes = () => {
    const searchVal = document.getElementById('search')?.value.toLowerCase();
    const categoryVal = document.getElementById('category')?.value.toLowerCase();
    const schemeCards = document.querySelectorAll('.scheme-card');

    schemeCards.forEach(card => {
        const title = card.querySelector('h2').innerText.toLowerCase();
        const category = card.getAttribute('data-category').toLowerCase();
        
        const matchesSearch = !searchVal || title.includes(searchVal);
        const matchesCategory = categoryVal === 'all' || category === categoryVal;

        if (matchesSearch && matchesCategory) {
            card.style.display = 'block';
        } else {
            card.style.display = 'none';
        }
    });
};

// Filtering logic for MSP
const filterMsp = () => {
    const cropVal = document.getElementById('cropFilter')?.value.toLowerCase();
    const seasonVal = document.getElementById('seasonFilter')?.value.toLowerCase();
    const mspRows = document.querySelectorAll('#mspTable tbody tr');

    mspRows.forEach(row => {
        const crop = row.getAttribute('data-crop').toLowerCase();
        const season = row.getAttribute('data-season').toLowerCase();

        const matchesCrop = cropVal === 'all' || crop.includes(cropVal);
        const matchesSeason = seasonVal === 'all' || season === seasonVal;

        if (matchesCrop && matchesSeason) {
            row.style.display = '';
        } else {
            row.style.display = 'none';
        }
    });
};

// Initialize Event Listeners
document.addEventListener('DOMContentLoaded', () => {
    // Scheme filters
    document.getElementById('search')?.addEventListener('input', filterSchemes);
    document.getElementById('category')?.addEventListener('change', filterSchemes);

    // MSP filters
    document.getElementById('cropFilter')?.addEventListener('change', filterMsp);
    document.getElementById('seasonFilter')?.addEventListener('change', filterMsp);
});