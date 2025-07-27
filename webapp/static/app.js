document.getElementById('flashcard-form').addEventListener('submit', async function(e) {
    e.preventDefault();
    const word = document.getElementById('word').value;
    const includeImages = document.getElementById('include_images').checked;
    const count = parseInt(document.getElementById('count').value, 10);
    const context = document.getElementById('context').value;
    const filename = document.getElementById('filename').value;
    const resultDiv = document.getElementById('result');
    resultDiv.textContent = 'Generating...';
    try {
        const response = await fetch('/api/generate', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ word, count, context, filename, include_images: includeImages })
        });
        const contentType = response.headers.get('content-type');
        if (response.ok && contentType && contentType.indexOf('text/csv') !== -1) {
            // Download the CSV file
            const blob = await response.blob();
            const downloadFilename = filename || 'flashcards.csv';
            const url = window.URL.createObjectURL(blob);
            const a = document.createElement('a');
            a.href = url;
            a.download = downloadFilename;
            document.body.appendChild(a);
            a.click();
            a.remove();
            window.URL.revokeObjectURL(url);
            resultDiv.textContent = 'Flashcards generated and downloaded!';
        } else {
            // Try to parse error JSON
            const data = await response.json();
            resultDiv.textContent = data.message || 'Error generating flashcards.';
        }
    } catch (err) {
        resultDiv.textContent = 'Error generating flashcards.';
    }
}); 