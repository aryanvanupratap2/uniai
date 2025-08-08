document.addEventListener('DOMContentLoaded', () => {
    // API_URL is now just the endpoint, as it's on the same domain
    const API_URL = 'https://uniai-pubz.onrender.com/find-universities';

    const searchButton = document.getElementById('search-btn');
    const courseInput = document.getElementById('course-input');
    const degreeSelect = document.getElementById('degree-type');
    const feesSelect = document.getElementById('fees-select');
    const targetCountrySelect = document.getElementById('target-country-select');
    const studentCountrySelect = document.getElementById('student-country-select');
    const loader = document.getElementById('loader');
    const errorMessage = document.getElementById('error-message');

    searchButton.addEventListener('click', async () => {
        if (!validateInputs()) return;

        toggleLoading(true);
        const searchData = getSearchData();

        try {
            const response = await fetch(API_URL, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(searchData),
            });

            const result = await response.json();

            if (!response.ok) {
                throw new Error(result.error || `HTTP error! status: ${response.status}`);
            }
            
            // Pass data to the results page via localStorage
            localStorage.setItem('universityResults', JSON.stringify(result));
            // Redirect to the /results route
            window.location.href = '/results';

        } catch (error) {
            showError(`Failed to fetch results: ${error.message}. Please try again.`);
        } finally {
            toggleLoading(false);
        }
    });

    function getSearchData() {
        return {
            course: courseInput.value,
            degree: degreeSelect.value,
            fees: feesSelect.value,
            target_country: targetCountrySelect.value,
            student_country: studentCountrySelect.value,
        };
    }

    function validateInputs() {
        let isValid = true;
        hideError();
        [courseInput, degreeSelect, feesSelect, targetCountrySelect, studentCountrySelect].forEach(field => {
            if (!field.value) {
                isValid = false;
                field.style.borderColor = '#ff4d4d';
            } else {
                field.style.borderColor = '#ccc';
            }
        });
        if (!isValid) showError('Please fill out all fields.');
        return isValid;
    }

    function toggleLoading(isLoading) {
        loader.style.display = isLoading ? 'block' : 'none';
        searchButton.disabled = isLoading;
        searchButton.style.cursor = isLoading ? 'not-allowed' : 'pointer';
        if (isLoading) hideError();
    }

    function showError(message) {
        errorMessage.textContent = message;
        errorMessage.style.display = 'block';
    }

    function hideError() {
        errorMessage.style.display = 'none';
    }
});



