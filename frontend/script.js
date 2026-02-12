document.getElementById('generateBtn').addEventListener('click', async () => {
    const codeInput = document.getElementById('codeInput').value;
    const statusMsg = document.getElementById('statusMessage');
    const codeOutput = document.getElementById('codeOutput');

    if (!codeInput.trim()) {
        statusMsg.style.color = "#f44336";
        statusMsg.textContent = "Error: Input is empty.";
        return;
    }

    statusMsg.style.color = "#ffeb3b";
    statusMsg.textContent = "Generating docstrings...";
    codeOutput.value = "";

    try {
        const response = await fetch('/api/generate', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({ source_code: codeInput, filename: "snippet.py" })
        });

        const data = await response.json();

        if (response.ok) {
            codeOutput.value = data.documented_code;
            statusMsg.style.color = "#4caf50";
            statusMsg.textContent = data.message;
        } else {
            throw new Error(data.detail || "An error occurred");
        }
    } catch (error) {
        statusMsg.style.color = "#f44336";
        statusMsg.textContent = "Error: " + error.message;
        codeOutput.value = "# An error occurred while communicating with the server.";
    }
});