
        // Simulated API response data
        const aiData = {
            status: "success",
            data: [
                {
                    original_problem: "10 + 10",
                    rewritten_problem: "The quarterback completed 24 passes in the first half. During halftime, the coach reviewed 8 of those passes for training purposes. How many passes were not reviewed during halftime?",
                    category: "addition",
                    difficulty: "easy",
                    ml_analysis: { confidence_score: 0.95, accuracy: 0.98, processing_time_ms: 45 },
                    theme: "Football"
                },
                {
                    original_problem: "5 * 3",
                    rewritten_problem: "A soccer team scored 5 goals per game. If they played 3 games, how many goals did they score in total?",
                    category: "multiplication",
                    difficulty: "easy",
                    ml_analysis: { confidence_score: 0.92, accuracy: 0.97, processing_time_ms: 38 },
                    theme: "Soccer"
                },
                {
                    original_problem: "15 - 7",
                    rewritten_problem: "A basketball player made 15 shots but missed 7. How many shots were successful?",
                    category: "subtraction",
                    difficulty: "easy",
                    ml_analysis: { confidence_score: 0.94, accuracy: 0.99, processing_time_ms: 40 },
                    theme: "Basketball"
                }
            ],
            metadata: {
                total_records: 3,
                api_version: "1.0.0",
                timestamp: "2025-06-13T00:45:00Z"
            }
        };

        let currentIndex = 0;

        const originalProblemText = document.getElementById('originalProblemText');
        const rewrittenProblemText = document.getElementById('rewrittenProblemText');
        const problemTheme = document.getElementById('problemTheme');
        const copyButton = document.getElementById('copyButton');
        const toastNotification = document.getElementById('toastNotification');
        const copiedFeedback = document.getElementById('copiedFeedback');
        const tryAgainButton = document.getElementById('tryAgainButton');
        const beepSound = document.getElementById('beepSound');

        // Initialize with first problem
        function updateProblem(index) {
            const problem = aiData.data[index];
            originalProblemText.textContent = problem.original_problem;
            rewrittenProblemText.textContent = problem.rewritten_problem;
            problemTheme.innerHTML = `<i class="fas fa-${problem.theme.toLowerCase()}-ball text-lg mr-2"></i> ${problem.theme}`;
        }
        updateProblem(currentIndex);

        function copyToClipboard(text) {
            const textarea = document.createElement('textarea');
            textarea.value = text;
            document.body.appendChild(textarea);
            textarea.select();
            document.execCommand('copy');
            document.body.removeChild(textarea);
        }

        copyButton.addEventListener('click', () => {
            const textToCopy = rewrittenProblemText.textContent.trim();
            copyToClipboard(textToCopy);
            copiedFeedback.classList.add('show');
            toastNotification.classList.add('show');
            beepSound.play();
            setTimeout(() => {
                copiedFeedback.classList.remove('show');
                toastNotification.classList.remove('show');
            }, 3000);
        });

        tryAgainButton.addEventListener('click', () => {
            currentIndex = (currentIndex + 1) % aiData.data.length;
            updateProblem(currentIndex);
        });
