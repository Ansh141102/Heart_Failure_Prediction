document.addEventListener('DOMContentLoaded', () => {
    const predictionForm = document.getElementById('predictionForm');
    const uploadForm = document.getElementById('uploadForm');
    const fileInput = document.querySelector('.file-input');
    const fileMsg = document.querySelector('.file-msg');
    const predictBtn = document.getElementById('predictBtn');
    const uploadBtn = document.getElementById('uploadBtn');
    const presetChips = document.querySelectorAll('.preset-chip');

    // Helper: button loading state
    function setLoading(button, isLoading, loadingText) {
        if (!button) return;
        if (isLoading) {
            button.disabled = true;
            button.classList.add('is-loading');
            button.dataset.originalText = button.textContent;
            if (loadingText) {
                button.textContent = loadingText;
            }
        } else {
            button.disabled = false;
            button.classList.remove('is-loading');
            if (button.dataset.originalText) {
                button.textContent = button.dataset.originalText;
            }
        }
    }

    // Sample presets for quick testing
    const presets = {
        low: {
            Age: 32,
            Sex: 'F',
            ChestPainType: 'NAP',
            RestingBP: 118,
            Cholesterol: 190,
            FastingBS: '0',
            RestingECG: 'Normal',
            MaxHR: 172,
            ExerciseAngina: 'N',
            Oldpeak: 0.0,
            ST_Slope: 'Up'
        },
        medium: {
            Age: 56,
            Sex: 'M',
            ChestPainType: 'ATA',
            RestingBP: 135,
            Cholesterol: 230,
            FastingBS: '1',
            RestingECG: 'ST',
            MaxHR: 145,
            ExerciseAngina: 'N',
            Oldpeak: 1.4,
            ST_Slope: 'Flat'
        },
        high: {
            Age: 67,
            Sex: 'M',
            ChestPainType: 'ASY',
            RestingBP: 160,
            Cholesterol: 290,
            FastingBS: '1',
            RestingECG: 'LVH',
            MaxHR: 110,
            ExerciseAngina: 'Y',
            Oldpeak: 3.0,
            ST_Slope: 'Down'
        }
    };

    // Apply presets on click
    presetChips.forEach(chip => {
        chip.addEventListener('click', () => {
            const key = chip.dataset.preset;
            const preset = presets[key];
            if (!preset) return;

            Object.entries(preset).forEach(([name, value]) => {
                if (predictionForm.elements[name]) {
                    predictionForm.elements[name].value = value;
                }
            });
        });
    });

    // Handle Manual Prediction
    predictionForm.addEventListener('submit', async (e) => {
        e.preventDefault();
        const formData = new FormData(predictionForm);
        const data = Object.fromEntries(formData.entries());
        const resultBox = document.getElementById('manualResult');

        resultBox.className = 'result-box';
        resultBox.style.display = 'block';
        resultBox.innerHTML = 'Analyzing...';

        setLoading(predictBtn, true, 'Analyzing…');

        try {
            const response = await fetch('/predict', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify(data),
            });

            const result = await response.json();

            if (result.error) {
                resultBox.innerHTML = `Error: ${result.error}`;
                return;
            }

            const riskClass = result.risk_level === 'High' ? 'result-high' : 'result-low';
            resultBox.className = `result-box ${riskClass}`;

            let factorsHtml = '';
            if (result.risk_factors && result.risk_factors.length > 0) {
                factorsHtml = `
                    <div class="risk-factors">
                        <h4>⚠️ Key Risk Factors:</h4>
                        <ul>
                            ${result.risk_factors.map(f => `<li>${f}</li>`).join('')}
                        </ul>
                    </div>
                `;
            } else {
                factorsHtml = `<p class="safe-msg">✅ No major risk factors identified by the model.</p>`;
            }

            resultBox.innerHTML = `
                <h3>Assessment Result</h3>
                <span class="probability">${result.probability}%</span>
                <p>Estimated probability of heart failure for this profile.</p>
                <p><strong>Risk Level: ${result.risk_level}</strong></p>
                ${factorsHtml}
            `;
        } catch (error) {
            console.error(error);
            resultBox.innerHTML = 'An unexpected error occurred. Please try again.';
        } finally {
            setLoading(predictBtn, false);
        }
    });

    // Handle File Upload Display
    fileInput.addEventListener('change', (e) => {
        if (e.target.files.length > 0) {
            fileMsg.textContent = e.target.files[0].name;
        } else {
            fileMsg.textContent = 'Drag & drop or click to select a CSV file';
        }
    });

    // Handle Batch Prediction
    uploadForm.addEventListener('submit', async (e) => {
        e.preventDefault();
        const formData = new FormData(uploadForm);
        const resultBox = document.getElementById('uploadResult');

        resultBox.className = 'result-box';
        resultBox.style.display = 'block';
        resultBox.innerHTML = 'Processing file...';

        setLoading(uploadBtn, true, 'Processing…');

        try {
            const response = await fetch('/upload', {
                method: 'POST',
                body: formData,
            });

            const result = await response.json();

            if (result.error) {
                resultBox.innerHTML = `Error: ${result.error}`;
                return;
            }

            if (!result.results || !Array.isArray(result.results)) {
                resultBox.innerHTML = 'Unexpected response format from server.';
                return;
            }

            // Create a table for first 50 results
            let tableHtml = `
                <h3>Batch Analysis Complete</h3>
                <p>Processed ${result.results.length} records.</p>
                <div class="table-container">
                    <table>
                        <thead>
                            <tr>
                                <th>Age</th>
                                <th>Sex</th>
                                <th>Risk %</th>
                                <th>Level</th>
                                <th>Key Factors</th>
                            </tr>
                        </thead>
                        <tbody>
            `;

            // Show up to top 50 results
            result.results.slice(0, 50).forEach(row => {
                const factors = row.Risk_Factors && row.Risk_Factors.length > 0
                    ? row.Risk_Factors.join(', ')
                    : 'None';

                tableHtml += `
                    <tr>
                        <td>${row.Age}</td>
                        <td>${row.Sex}</td>
                        <td>${row.Risk_Probability}%</td>
                        <td>${row.Risk_Level}</td>
                        <td class="factors-cell">${factors}</td>
                    </tr>
                `;
            });

            tableHtml += `
                        </tbody>
                    </table>
                </div>
                <p style="margin-top: 1rem; font-size: 0.8rem;">*Showing first 50 results</p>
            `;

            resultBox.innerHTML = tableHtml;
        } catch (error) {
            console.error(error);
            resultBox.innerHTML = 'An error occurred during upload. Please check the CSV and try again.';
        } finally {
            setLoading(uploadBtn, false);
        }
    });
});
