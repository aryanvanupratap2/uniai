document.addEventListener('DOMContentLoaded', () => {
    // --- CONFIGURATION ---
    // The URL of your backend server.
    // If you are running the Python script locally, this will be the correct URL.
    const API_URL = 'http://127.0.0.1:5000/find-universities';

    // --- DOM ELEMENTS ---
    const searchButton = document.getElementById('search-btn');
    const courseInput = document.getElementById('course-input');
    const degreeSelect = document.getElementById('degree-type');
    const feesSelect = document.getElementById('fees-select');
    const targetCountrySelect = document.getElementById('target-country-select');
    const studentCountrySelect = document.getElementById('student-country-select');
    const loader = document.getElementById('loader');
    const errorMessage = document.getElementById('error-message');

    // --- EVENT LISTENER ---
    searchButton.addEventListener('click', async () => {
        // 1. Validate inputs
        if (!validateInputs()) {
            return; // Stop if validation fails
        }

        // 2. Prepare for API call
        toggleLoading(true);
        const searchData = getSearchData();

        try {
            // 3. Make the API call
            const response = await fetch(API_URL, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify(searchData),
            });

            const result = await response.json();

            // 4. Handle the response
            if (!response.ok) {
                // If response is not 2xx, handle error
                throw new Error(result.error || `HTTP error! status: ${response.status}`);
            }
            
            // 5. Success: Store results and redirect
            // We use localStorage to pass the data to the results page
            localStorage.setItem('universityResults', JSON.stringify(result));
            window.location.href = 'results.html'; // Redirect to the results page

        } catch (error) {
            // 6. Handle any errors during the fetch
            showError(`Failed to fetch results: ${error.message}. Please check if the backend server is running and try again.`);
        } finally {
            // 7. Ensure loader is turned off
            toggleLoading(false);
        }
    });

    // --- HELPER FUNCTIONS ---

    /**
     * Gathers data from all form inputs.
     * @returns {object} The data payload for the API.
     */
    function getSearchData() {
        return {
            course: courseInput.value,
            degree: degreeSelect.value,
            fees: feesSelect.value,
            target_country: targetCountrySelect.value,
            student_country: studentCountrySelect.value,
        };
    }

    /**
     * Validates that all required fields are filled.
     * @returns {boolean} True if all inputs are valid, false otherwise.
     */
    function validateInputs() {
        let isValid = true;
        const fields = [courseInput, degreeSelect, feesSelect, targetCountrySelect, studentCountrySelect];
        
        // Reset previous error states
        hideError();
        fields.forEach(field => field.style.borderColor = '#ccc');

        for (const field of fields) {
            if (!field.value) {
                isValid = false;
                field.style.borderColor = '#ff4d4d'; // Highlight empty field
            }
        }

        if (!isValid) {
            showError('Please fill out all fields before searching.');
        }
        
        return isValid;
    }

    /**
     * Shows or hides the loading indicator and disables/enables the button.
     * @param {boolean} isLoading - Whether to show the loader.
     */
    function toggleLoading(isLoading) {
        if (isLoading) {
            loader.style.display = 'block';
            searchButton.disabled = true;
            searchButton.style.cursor = 'not-allowed';
            searchButton.style.backgroundColor = '#ccc';
            hideError();
        } else {
            loader.style.display = 'none';
            searchButton.disabled = false;
            searchButton.style.cursor = 'pointer';
            searchButton.style.backgroundColor = '#ffc107';
        }
    }

    /**
     * Displays an error message to the user.
     * @param {string} message - The error message to display.
     */
    function showError(message) {
        errorMessage.textContent = message;
        errorMessage.style.display = 'block';
    }

    /**
     * Hides the error message.
     */
    function hideError() {
        errorMessage.style.display = 'none';
    }
});
