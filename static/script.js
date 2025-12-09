document.addEventListener('DOMContentLoaded', () => {
    const predictionForm = document.getElementById('predictionForm');
    const uploadForm = document.getElementById('uploadForm');
    
    // States
    const stateWelcome = document.getElementById('welcomeState');
    const stateResult = document.getElementById('resultState');
    const stateBatch = document.getElementById('batchState');
    
    // Result Elements
    const gaugeFill = document.getElementById('gaugeFill');
    const resultPercent = document.getElementById('resultPercent');
    const riskLabel = document.getElementById('riskLabel');
    const riskDesc = document.getElementById('riskDesc');
    const factorsList = document.getElementById('factorsList');
    
    // --- Helper: State Switcher ---
    function switchState(targetState) {
        [stateWelcome, stateResult, stateBatch].forEach(el => {
            el.classList.remove('active');
        });
        targetState.classList.add('active');
    }

    // --- Helper: Animate Gauge ---
    function animateGauge(percent) {
        // 0% -> rotate(0deg), 100% -> rotate(360deg) for fill
        const deg = (percent / 100) * 360;
        gaugeFill.style.transform = `rotate(${deg}deg)`;
        
        // Counter animation
        let start = 0;
        const duration = 1500;
        const stepTime = Math.abs(Math.floor(duration / percent));
        
        const timer = setInterval(() => {
            start++;
            resultPercent.innerText = start + "%";
            if (start >= percent) clearInterval(timer);
        }, stepTime);
        
        // Color logic
        if (percent < 30) {
            gaugeFill.style.borderTopColor = "#10b981"; // Green
            riskLabel.style.color = "#10b981";
        } else if (percent < 60) {
            gaugeFill.style.borderTopColor = "#facc15"; // Yellow
            riskLabel.style.color = "#facc15";
        } else {
            gaugeFill.style.borderTopColor = "#ef4444"; // Red
            riskLabel.style.color = "#ef4444";
        }
    }

    // --- Handle Single Prediction ---
    predictionForm.addEventListener('submit', async (e) => {
        e.preventDefault();
        const btn = document.getElementById('predictBtn');
        const originalText = btn.innerHTML;
        
        btn.innerHTML = '<i class="fa-solid fa-circle-notch fa-spin"></i> Analyzing...';
        btn.disabled = true;

        const formData = new FormData(predictionForm);
        const data = Object.fromEntries(formData.entries());

        try {
            const response = await fetch('/predict', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(data)
            });
            const result = await response.json();

            if (result.error) {
                alert("Error: " + result.error);
                return;
            }

            // Update UI
            switchState(stateResult);
            
            // Risk Label Logic
            riskLabel.innerText = result.risk_level + " Risk";
            if (result.risk_level === "High") {
                riskDesc.innerText = "Medical consultation strongly recommended.";
            } else {
                riskDesc.innerText = "Maintain healthy habits.";
            }

            // Render factors
            factorsList.innerHTML = "";
            if (result.risk_factors && result.risk_factors.length > 0) {
                factorsList.innerHTML = "<h4>⚠️ Primary Contributors:</h4>";
                result.risk_factors.forEach((f, index) => {
                    const div = document.createElement('div');
                    div.className = 'factor-item';
                    div.style.animationDelay = (index * 0.1) + "s";
                    div.innerHTML = `<i class="fa-solid fa-triangle-exclamation"></i> ${f}`;
                    factorsList.appendChild(div);
                });
            } else {
                factorsList.innerHTML = "<p style='color:#10b981'><i class='fa-solid fa-check-circle'></i> No critical risk factors detected.</p>";
            }

            // Trigger Animation
            setTimeout(() => {
                animateGauge(result.probability);
            }, 100);

        } catch (err) {
            console.error(err);
            alert("Connection error.");
        } finally {
            btn.innerHTML = originalText;
            btn.disabled = false;
        }
    });

    // --- Handle File Upload ---
    document.getElementById('csvIn').addEventListener('change', function() {
        if(this.files && this.files.length > 0) {
            document.getElementById('fileName').innerText = this.files[0].name;
            // Auto submit or wait? logic below uses auto event dispatch
        }
    });

    uploadForm.addEventListener('submit', async (e) => {
        e.preventDefault();
        if(!document.getElementById('csvIn').files.length) return;

        const formData = new FormData(uploadForm);
        
        try {
            const response = await fetch('/upload', {
                method: 'POST',
                body: formData
            });
            const result = await response.json();
            
            if(result.error) {
                alert(result.error);
                return;
            }

            // Render Table in Modal/View
            switchState(stateBatch);
            const tableDiv = document.getElementById('batchTable');
            
            let html = `
                <table style="width:100%; text-align:left; border-collapse:collapse; color:white;">
                    <thead style="background:rgba(255,255,255,0.1); color:var(--primary);">
                        <tr>
                            <th style="padding:10px;">Age/Sex</th>
                            <th style="padding:10px;">Risk</th>
                            <th style="padding:10px;">Factors</th>
                        </tr>
                    </thead>
                    <tbody>
            `;
            
            result.results.slice(0, 50).forEach(row => {
                const color = row.Risk_Probability > 50 ? '#ef4444' : '#10b981';
                html += `
                    <tr style="border-bottom:1px solid rgba(255,255,255,0.05);">
                        <td style="padding:10px;">${row.Age} / ${row.Sex}</td>
                        <td style="padding:10px; color:${color}; font-weight:bold;">
                            ${row.Risk_Probability}%
                        </td>
                        <td style="padding:10px; font-size:0.85rem; color:#94a3b8;">
                            ${row.Risk_Factors.join(', ')}
                        </td>
                    </tr>
                `;
            });
            html += "</tbody></table>";
            tableDiv.innerHTML = html;

        } catch (err) {
            alert("Upload failed.");
        }
    });
});
