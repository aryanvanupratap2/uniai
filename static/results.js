document.addEventListener('DOMContentLoaded', () => {
    const resultsGrid = document.getElementById('results-grid');
    const disclaimerContainer = document.getElementById('disclaimer-container');
    const noResultsContainer = document.getElementById('no-results');

    // Retrieve the results from localStorage, where they were placed by programs.js
    const resultsData = localStorage.getItem('universityResults');

    if (resultsData) {
        try {
            const { disclaimer, universities } = JSON.parse(resultsData);

            // Display the disclaimer message from the backend
            if (disclaimer) {
                disclaimerContainer.innerHTML = `<div class="disclaimer"><i class="fas fa-info-circle"></i> ${disclaimer}</div>`;
            }

            // Check if the universities array exists and has content
            if (universities && universities.length > 0) {
                // Loop through each university and create a display card for it
                universities.forEach(uni => {
                    const card = createUniversityCard(uni);
                    resultsGrid.appendChild(card);
                });
            } else {
                // If the array is empty, show the 'no results' message
                showNoResults();
            }

        } catch (error) {
            console.error('Failed to parse university results:', error);
            showNoResults();
        } finally {
            // Clear the data from localStorage to prevent old results from showing
            localStorage.removeItem('universityResults');
        }
    } else {
        // If no data was found in localStorage, show the 'no results' message
        showNoResults();
    }

    /**
     * Creates an HTML element for a single university card.
     * @param {object} uni - The university data object.
     * @returns {HTMLElement} The created card element.
     */
    function createUniversityCard(uni) {
        const card = document.createElement('div');
        card.className = 'university-card';

        // Set default values to prevent errors if data is missing
        const name = uni.name || 'N/A';
        const city = uni.city || 'N/A';
        const tuition = uni.tuition || 'Contact University';
        const website = uni.website || '#';

        // Populate the card with the university's information
        card.innerHTML = `
            <div class="card-content">
                <h2>${escapeHTML(name)}</h2>
                <p class="city"><i class="fas fa-map-marker-alt"></i> ${escapeHTML(city)}</p>
                <div class="info-item">
                    <i class="fas fa-dollar-sign"></i>
                    <span><strong>Tuition:</strong> ${escapeHTML(tuition)}</span>
                </div>
            </div>
            <div class="card-footer">
                <a href="${escapeHTML(website)}" target="_blank" rel="noopener noreferrer" class="website-link">
                    Visit Website <i class="fas fa-external-link-alt"></i>
                </a>
            </div>
        `;
        return card;
    }
    
    /**
     * Hides the results grid and shows a 'no results' message.
     */
    function showNoResults() {
        resultsGrid.style.display = 'none';
        disclaimerContainer.style.display = 'none';
        noResultsContainer.style.display = 'block';
    }

    /**
     * A utility to prevent XSS attacks by escaping HTML special characters.
     * @param {string} str - The string to escape.
     * @returns {string} The escaped string.
     */
    function escapeHTML(str) {
        const p = document.createElement('p');
        p.appendChild(document.createTextNode(str));
        return p.innerHTML;
    }
});
