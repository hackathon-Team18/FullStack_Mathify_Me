
    document.addEventListener('DOMContentLoaded', () => {
        const aiData = {
            status: "success",
            data: [
                { original_problem: "10 + 10", rewritten_problem: "The quarterback completed 24 passes in the first half. During halftime, the coach reviewed 8 of those passes for training purposes. How many passes were not reviewed during halftime?", theme: "Football" },
                { original_problem: "10 + 10", rewritten_problem: "Steve collected 24 blocks of diamond ore while mining. He used 8 blocks to craft diamond tools for his friend Alex. How many diamond blocks does Steve have remaining?", theme: "Minecraft" },
                { original_problem: "10 + 10", rewritten_problem: "A wildlife ranger spotted 24 deer in the forest. 8 of them were tagged for research. How many deer were not tagged?", theme: "Wildlife" },
                { original_problem: "10 + 10", rewritten_problem: "An astronaut collected 24 moon rocks on one mission. 8 were sent back to Earth for analysis. How many moon rocks remain on the spacecraft?", theme: "Space" },
                { original_problem: "10 + 10", rewritten_problem: "A baker made 24 cupcakes for a party. She gave 8 to her friend for a tasting. How many cupcakes are left for the party?", theme: "Baking" },
                { original_problem: "10 + 10", rewritten_problem: "A band recorded 24 songs for an album. 8 were selected for a single release. How many songs are left for the album?", theme: "Music" },
                { original_problem: "10 + 10", rewritten_problem: "A director filmed 24 scenes for a movie. 8 were used in the trailer. How many scenes are left for the final cut?", theme: "Movies" }
            ],
            metadata: {
                total_records: 7,
                api_version: "1.0.0",
                timestamp: "2025-06-13T15:46:00+03:00"
            }
        };

        let currentIndex = 0;

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
        const customToast = document.getElementById('custom-toast'); // Renamed from snackbar
        const successMessage = document.getElementById('success-message');
        // Removed beepSound element

        async function fetchRewrittenProblem(original, theme) {
            return new Promise((resolve) => {
                setTimeout(() => {
                    const matchingProblem = aiData.data.find(p => p.original_problem === original && p.theme === theme);
                    if (matchingProblem) {
                        resolve(matchingProblem);
                    } else {
                        // If no specific theme match, try to find any problem with the original_problem
                        const genericMatch = aiData.data.find(p => p.original_problem === original);
                        if (genericMatch) {
                            resolve({ original_problem: original, rewritten_problem: genericMatch.rewritten_problem, theme: genericMatch.theme });
                        } else {
                            resolve({ original_problem: original, rewritten_problem: "No rewritten problem available for this input.", theme: theme });
                        }
                    }
                }, 500);
            });
        }

        function updateDisplay(problem) {
            originalText.textContent = problem.original_problem;
            rewrittenText.textContent = problem.rewritten_problem;
            problemTheme.textContent = problem.theme;
            results.style.display = 'flex';
            actionButtons.style.display = 'flex';

            // Show success message
            successMessage.classList.add('show');
            // Auto-hide success message after 3 seconds, unless closed manually
            setTimeout(() => {
                if (successMessage.classList.contains('show')) { // Only hide if still visible
                    successMessage.classList.remove('show');
                }
            }, 3000);
        }

        function showCustomToast() {
            customToast.style.display = 'block';
            customToast.classList.remove('hide'); // Ensure it's not starting hidden if re-shown quickly
            setTimeout(() => {
                customToast.classList.add('hide');
                // Give time for animation to complete before setting display to none
                setTimeout(() => {
                    customToast.style.display = 'none';
                }, 500); // Matches slideOutToRight animation duration
            }, 3000);
        }

        function copyToClipboard(text) {
            navigator.clipboard.writeText(text).then(() => {
                showCustomToast();
                // Removed beepSound.play()
            }).catch(err => {
                console.error('Failed to copy text: ', err);
            });
        }

        // Initialize the display with the first problem from aiData on page load
        if (aiData.data.length > 0) {
            const initialProblem = aiData.data[0];
            updateDisplay(initialProblem);
            mathInput.value = initialProblem.original_problem;
            themeSelect.value = initialProblem.theme;
            currentIndex = 0;
        }

        rewriteBtn.addEventListener('click', async () => {
            const input = mathInput.value.trim();
            const theme = themeSelect.value;

            if (!input) {
                alert('Please enter a math problem.');
                return;
            }
            if (!theme) { // Check if a theme is selected
                alert('Please select a theme.');
                return;
            }

            const problem = await fetchRewrittenProblem(input, theme);
            updateDisplay(problem);
            currentIndex = aiData.data.findIndex(p => p.original_problem === problem.original_problem && p.theme === problem.theme);
        });

        copyBtn.addEventListener('click', () => {
            const text = rewrittenText.textContent.trim();
            copyToClipboard(text);
        });

        tryAgainBtn.addEventListener('click', async () => {
            const currentOriginalProblem = originalText.textContent.trim();
            const currentTheme = problemTheme.textContent;

            const availableThemesForCurrentProblem = aiData.data.filter(p =>
                p.original_problem === currentOriginalProblem && p.theme !== currentTheme
            );

            if (availableThemesForCurrentProblem.length > 0) {
                // Find the index of the current theme within the filtered list of available themes
                const currentThemeIndexInAvailable = availableThemesForCurrentProblem.findIndex(p => p.theme === currentTheme);
                // Calculate the index of the next theme to display, cycling through the filtered list
                const nextThemeIndex = (currentThemeIndexInAvailable + 1) % availableThemesForCurrentProblem.length;
                const newTheme = availableThemesForCurrentProblem[nextThemeIndex].theme;

                const newProblem = await fetchRewrittenProblem(currentOriginalProblem, newTheme);
                updateDisplay(newProblem);
                // Update currentIndex to point to the newly displayed problem in the original aiData array
                currentIndex = aiData.data.findIndex(p => p.original_problem === newProblem.original_problem && p.theme === newProblem.theme);
            } else {
                rewrittenText.textContent = 'No other themes available for this problem.';
                problemTheme.textContent = 'N/A';
                // Potentially hide action buttons if no more options
                // actionButtons.style.display = 'none';
            }
        });
    });
