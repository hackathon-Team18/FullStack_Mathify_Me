document.addEventListener('DOMContentLoaded', () => {
    const API_URL = 'http://127.0.0.1:8000';
    const REWRITE_ENDPOINT = `${API_URL}/rewrite`;

    const mathInput = document.getElementById('math-input');
    const themeSelect = document.getElementById('theme');
    const rewriteBtn = document.getElementById('rewrite-btn');
    const results = document.getElementById('results');
    const originalText = document.getElementById('original-text');
    const rewrittenText = document.getElementById('rewritten-text');
    const problemTheme = document.getElementById('problem-theme');
    const actionButtons = document.getElementById('action-buttons');
    const copyBtn = document.getElementById('copy-btn');
    const tryAgainBtn = document.getElementById('try-again-btn');
    const customToast = document.getElementById('custom-toast');
    const successMessage = document.getElementById('success-message');

    async function fetchRewrittenProblem(original, theme, numExamples = 3) {
        console.log('Sending POST request to:', REWRITE_ENDPOINT);
        console.log('Request payload:', { original_problem: original, theme, num_examples: numExamples });
        try {
            // Health check
            console.log('Testing API health at:', `${API_URL}/health`);
            const healthResponse = await fetch(`${API_URL}/health`);
            console.log('Health check status:', healthResponse.status, healthResponse.statusText);
            if (!healthResponse.ok) {
                throw new Error(`API health check failed. Status: ${healthResponse.status}`);
            }

            const response = await fetch(REWRITE_ENDPOINT, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'Accept': 'application/json',
                },
                body: JSON.stringify({
                    original_problem: original,
                    theme: theme,
                    num_examples: numExamples,
                }),
            });

            console.log('Rewrite response status:', response.status, response.statusText);
            if (!response.ok) {
                let errorDetail;
                try {
                    errorDetail = await response.json();
                    console.error('Error response:', errorDetail);
                } catch {
                    errorDetail = { detail: 'No response body' };
                }
                if (response.status === 404) {
                    throw new Error(`The /rewrite endpoint was not found at ${REWRITE_ENDPOINT}. Ensure the FastAPI server is running and the endpoint is defined in app/main.py.`);
                }
                throw new Error(`HTTP error! Status: ${response.status}, Detail: ${JSON.stringify(errorDetail.detail || 'Unknown error')}`);
            }

            const data = await response.json();
            console.log('Response data:', data);
            return {
                original_problem: original,
                rewritten_problem: data.rewritten_problem || 'No rewritten problem returned',
                theme: theme,
                examples_used: data.examples_used || [],
            };
        } catch (error) {
            console.error('Fetch error:', error);
            alert(`Failed to rewrite problem: ${error.message}\nCheck the console for details.`);
            return {
                original_problem: original,
                rewritten_problem: `Error: ${error.message}`,
                theme: theme,
                examples_used: [],
            };
        }
    }

    function updateDisplay(problem) {
        originalText.textContent = problem.original_problem;
        rewrittenText.textContent = problem.rewritten_problem;
        problemTheme.textContent = problem.theme;
        results.style.display = 'flex';
        actionButtons.style.display = 'flex';

        successMessage.classList.add('show');
        setTimeout(() => {
            if (successMessage.classList.contains('show')) {
                successMessage.classList.remove('show');
            }
        }, 3000);
    }

    function showCustomToast() {
        customToast.style.display = 'block';
        customToast.classList.remove('hide');
        setTimeout(() => {
            customToast.classList.add('hide');
            setTimeout(() => {
                customToast.style.display = 'none';
            }, 500);
        }, 3000);
    }

    function copyToClipboard(text) {
        navigator.clipboard.writeText(text).then(() => {
            showCustomToast();
        }).catch(err => {
            console.error('Failed to copy text:', err);
            alert('Failed to copy text to clipboard.');
        });
    }

    rewriteBtn.addEventListener('click', async () => {
        const input = mathInput.value.trim();
        const theme = themeSelect.value;

        if (!input) {
            alert('Please enter a math problem.');
            return;
        }
        if (!theme) {
            alert('Please select a theme.');
            return;
        }

        rewriteBtn.disabled = true;
        rewriteBtn.textContent = 'Rewriting...';

        const problem = await fetchRewrittenProblem(input, theme);
        updateDisplay(problem);

        rewriteBtn.disabled = false;
        rewriteBtn.textContent = '✨ Rewrite Problem';
    });

    copyBtn.addEventListener('click', () => {
        const text = rewrittenText.textContent.trim();
        copyToClipboard(text);
    });

    tryAgainBtn.addEventListener('click', async () => {
        const currentOriginalProblem = originalText.textContent.trim();
        const currentTheme = problemTheme.textContent;

        const availableThemes = Array.from(themeSelect.options)
            .map(option => option.value)
            .filter(theme => theme && theme !== currentTheme);

        if (availableThemes.length > 0) {
            const newTheme = availableThemes[Math.floor(Math.random() * availableThemes.length)];

            tryAgainBtn.disabled = true;
            tryAgainBtn.textContent = 'Trying...';

            const newProblem = await fetchRewrittenProblem(currentOriginalProblem, newTheme);
            updateDisplay(newProblem);
            themeSelect.value = newTheme;

            tryAgainBtn.disabled = false;
            tryAgainBtn.textContent = 'Try Different Theme';
        } else {
            alert('No other themes available.');
            rewrittenText.textContent = 'No other themes available for this problem.';
            problemTheme.textContent = 'N/A';
        }
    });

    // Initialize with an example problem
    const initialProblem = {
        original_problem: 'Sarah has 24 apples. She gives 8 apples to her friend. How many apples does she have left?',
        rewritten_problem: '',
        theme: '',
        examples_used: [],
    };
    updateDisplay(initialProblem);
    mathInput.value = initialProblem.original_problem;
    results.style.display = 'flex';
    actionButtons.style.display = 'none';
});