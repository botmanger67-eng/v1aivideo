document.addEventListener('DOMContentLoaded', function() {
    const form = document.getElementById('generationForm');
    const generateScriptBtn = document.getElementById('generateScript');
    const generateVoiceBtn = document.getElementById('generateVoice');
    const generateImagesBtn = document.getElementById('generateImages');
    const composeVideoBtn = document.getElementById('composeVideo');
    const statusDiv = document.getElementById('status');
    const progressBar = document.getElementById('progress');
    const resultArea = document.getElementById('result');

    // Store original button texts for all buttons
    document.querySelectorAll('button').forEach(btn => {
        btn.dataset.originalText = btn.textContent;
    });

    function setLoading(button, loading) {
        if (loading) {
            button.disabled = true;
            button.textContent = 'Processing...';
        } else {
            button.disabled = false;
            button.textContent = button.dataset.originalText || button.textContent;
        }
    }

    async function apiCall(endpoint, data, button) {
        setLoading(button, true);
        updateStatus('Processing...');
        try {
            const response = await fetch(endpoint, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify(data)
            });
            if (!response.ok) {
                const errorData = await response.json().catch(() => ({}));
                throw new Error(errorData.error || `HTTP error ${response.status}`);
            }
            const result = await response.json();
            updateStatus('Success');
            return result;
        } catch (error) {
            updateStatus(`Error: ${error.message}`);
            throw error;
        } finally {
            setLoading(button, false);
        }
    }

    function updateStatus(message) {
        if (statusDiv) {
            statusDiv.textContent = message;
        }
    }

    function updateProgress(percent) {
        if (progressBar) {
            progressBar.style.width = percent + '%';
            progressBar.textContent = percent + '%';
        }
    }

    function displayResult(data) {
        if (resultArea) {
            if (typeof data === 'string') {
                resultArea.textContent = data;
            } else {
                resultArea.textContent = JSON.stringify(data, null, 2);
            }
        }
    }

    // Generate Script
    if (generateScriptBtn) {
        generateScriptBtn.addEventListener('click', async function(e) {
            e.preventDefault();
            const topic = document.getElementById('topic').value.trim();
            if (!topic) {
                updateStatus('Please enter a topic.');
                return;
            }
            try {
                const result = await apiCall('/api/generate-script', { topic: topic }, generateScriptBtn);
                displayResult(result.script || result);
                updateProgress(25);
            } catch (error) {
                // already handled in apiCall
            }
        });
    }

    // Generate Voice
    if (generateVoiceBtn) {
        generateVoiceBtn.addEventListener('click', async function(e) {
            e.preventDefault();
            const script = document.getElementById('scriptText')?.value || resultArea?.textContent;
            if (!script) {
                updateStatus('Please generate a script first.');
                return;
            }
            try {
                const result = await apiCall('/api/generate-voice', { text: script }, generateVoiceBtn);
                displayResult(result.audioUrl || result);
                updateProgress(50);
            } catch (error) {}
        });
    }

    // Generate Images
    if (generateImagesBtn) {
        generateImagesBtn.addEventListener('click', async function(e) {
            e.preventDefault();
            const scenes = document.getElementById('scenesInput')?.value;
            if (!scenes) {
                updateStatus('Please provide scene descriptions.');
                return;
            }
            try {
                const result = await apiCall('/api/generate-images', { scenes: scenes.split('\n') }, generateImagesBtn);
                displayResult(result.images || result);
                updateProgress(75);
            } catch (error) {}
        });
    }

    // Compose Video
    if (composeVideoBtn) {
        composeVideoBtn.addEventListener('click', async function(e) {
            e.preventDefault();
            try {
                const result = await apiCall('/api/compose-video', {}, composeVideoBtn);
                displayResult(result.videoUrl || result);
                updateProgress(100);
            } catch (error) {}
        });
    }

    // Pipeline helper that does not touch button state (for full pipeline)
    async function pipelineApiCall(endpoint, data) {
        const response = await fetch(endpoint, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify(data)
        });
        if (!response.ok) {
            const errorData = await response.json().catch(() => ({}));
            throw new Error(errorData.error || `HTTP error ${response.status}`);
        }
        return await response.json();
    }

    // Full generation pipeline (one button to rule them all)
    const fullPipelineBtn = document.getElementById('fullPipeline');
    if (fullPipelineBtn) {
        fullPipelineBtn.addEventListener('click', async function(e) {
            e.preventDefault();
            const topic = document.getElementById('topic').value.trim();
            if (!topic) {
                updateStatus('Please enter a topic.');
                return;
            }
            setLoading(fullPipelineBtn, true);
            updateProgress(0);
            try {
                // Step 1: Script
                updateStatus('Generating script...');
                const scriptResult = await pipelineApiCall('/api/generate-script', { topic: topic });
                const script = scriptResult.script || scriptResult;
                displayResult(script);
                updateProgress(25);

                // Step 2: Voice
                updateStatus('Generating voice...');
                const voiceResult = await pipelineApiCall('/api/generate-voice', { text: script });
                updateProgress(50);

                // Step 3: Images (assuming scenes already defined in script)
                updateStatus('Generating images...');
                const imagesResult = await pipelineApiCall('/api/generate-images', { script: script });
                updateProgress(75);

                // Step 4: Compose
                updateStatus('Composing video...');
                const videoResult = await pipelineApiCall('/api/compose-video', {});
                updateProgress(100);
                displayResult(videoResult.videoUrl || videoResult);
                updateStatus('Video generation complete!');
            } catch (error) {
                updateStatus(`Pipeline failed: ${error.message}`);
            } finally {
                setLoading(fullPipelineBtn, false);
            }
        });
    }

    // Input validation for numeric fields
    document.querySelectorAll('input[type="number"]').forEach(input => {
        input.addEventListener('input', function() {
            const val = parseFloat(this.value);
            if (this.min && val < parseFloat(this.min)) {
                this.value = this.min;
            }
            if (this.max && val > parseFloat(this.max)) {
                this.value = this.max;
            }
        });
    });

    // Example: progress simulation for demo (can be removed)
    const progressSim = document.getElementById('simulateProgress');
    if (progressSim) {
        progressSim.addEventListener('click', function() {
            let p = 0;
            const interval = setInterval(() => {
                p += 10;
                updateProgress(p);
                if (p >= 100) {
                    clearInterval(interval);
                    updateStatus('Demo complete.');
                }
            }, 500);
        });
    }
});