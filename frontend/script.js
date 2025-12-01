document.addEventListener('DOMContentLoaded', () => {
    const generateBtn = document.getElementById('generateBtn');
    const repoUrlInput = document.getElementById('repoUrl');
    const docTypeSelect = document.getElementById('docType');
    const diagramTypeGroup = document.getElementById('diagramTypeGroup');
    const diagramTypeSelect = document.getElementById('diagramType');
    const loadingSection = document.getElementById('loading');
    const resultSection = document.getElementById('resultSection');
    const outputContent = document.getElementById('outputContent');
    const mermaidContent = document.getElementById('mermaidContent');
    const downloadMdBtn = document.getElementById('downloadMdBtn');
    const downloadWordBtn = document.getElementById('downloadWordBtn');

    // Initialize Mermaid
    mermaid.initialize({ startOnLoad: false, theme: 'default' });

    docTypeSelect.addEventListener('change', () => {
        if (docTypeSelect.value === 'diagram') {
            diagramTypeGroup.classList.remove('hidden');
        } else {
            diagramTypeGroup.classList.add('hidden');
        }
    });

    generateBtn.addEventListener('click', async () => {
        const repoUrl = repoUrlInput.value.trim();
        const docType = docTypeSelect.value;
        const diagramType = diagramTypeSelect.value;

        if (!repoUrl) {
            alert('Please enter a GitHub repository URL');
            return;
        }

        // Reset UI
        resultSection.classList.add('hidden');
        outputContent.innerHTML = '';
        mermaidContent.innerHTML = '';
        mermaidContent.classList.add('hidden');
        outputContent.classList.remove('hidden');
        loadingSection.classList.remove('hidden');

        try {
            const body = { repo_url: repoUrl };
            if (docType === 'diagram') {
                body.diagram_type = diagramType;
            }

            const response = await fetch(`http://localhost:8000/generate/${docType}`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify(body),
            });

            if (!response.ok) {
                throw new Error(`Error: ${response.statusText}`);
            }

            const data = await response.json();

            loadingSection.classList.add('hidden');
            resultSection.classList.remove('hidden');

            if (docType === 'diagram') {
                outputContent.classList.add('hidden');
                mermaidContent.classList.remove('hidden');
                mermaidContent.textContent = data.content;
                await mermaid.run({ nodes: [mermaidContent] });
            } else {
                outputContent.innerHTML = marked.parse(data.content);
            }

            // Setup download buttons
            downloadMdBtn.onclick = () => downloadFile(data.content, `${docType}.md`, 'text/markdown');
            downloadWordBtn.onclick = () => downloadWord(data.content, `${docType}.docx`);

        } catch (error) {
            loadingSection.classList.add('hidden');
            alert('Failed to generate documentation: ' + error.message);
        }
    });

    function downloadFile(content, filename, type) {
        const blob = new Blob([content], { type: type });
        const url = URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = filename;
        document.body.appendChild(a);
        a.click();
        document.body.removeChild(a);
        URL.revokeObjectURL(url);
    }

    async function downloadWord(content, filename) {
        try {
            const response = await fetch('http://localhost:8000/download/word', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({ content: content, filename: filename }),
            });

            if (!response.ok) throw new Error('Download failed');

            const blob = await response.blob();
            const url = window.URL.createObjectURL(blob);
            const a = document.createElement('a');
            a.href = url;
            a.download = filename;
            document.body.appendChild(a);
            a.click();
            document.body.removeChild(a);
            window.URL.revokeObjectURL(url);
        } catch (error) {
            alert('Failed to download Word document: ' + error.message);
        }
    }
});
