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
    const historyList = document.getElementById('historyList');
    const loginBtn = document.getElementById('loginBtn');
    const userInfo = document.getElementById('userInfo');

    // Initialize Mermaid
    mermaid.initialize({ startOnLoad: false, theme: 'default' });

    // Check for auth token
    const token = localStorage.getItem('github_token');
    if (token) {
        if (loginBtn) loginBtn.classList.add('hidden');
        if (userInfo) userInfo.classList.remove('hidden');
    }

    // Handle OAuth Callback
    const urlParams = new URLSearchParams(window.location.search);
    const code = urlParams.get('code');
    if (code) {
        handleAuthCallback(code);
    }

    // Load history on start
    loadHistory();

    if (loginBtn) {
        loginBtn.addEventListener('click', async () => {
            try {
                const response = await fetch('http://localhost:8000/auth/login');
                const data = await response.json();
                window.location.href = data.url;
            } catch (error) {
                alert('Login failed: ' + error.message);
            }
        });
    }

    async function handleAuthCallback(code) {
        try {
            const response = await fetch(`http://localhost:8000/auth/callback?code=${code}`);
            if (!response.ok) throw new Error('Auth failed');

            const data = await response.json();
            localStorage.setItem('github_token', data.access_token);

            // Clean URL
            window.history.replaceState({}, document.title, "/");

            if (loginBtn) loginBtn.classList.add('hidden');
            if (userInfo) userInfo.classList.remove('hidden');
            alert('Logged in successfully!');
        } catch (error) {
            alert('Authentication failed: ' + error.message);
        }
    }

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

            const headers = {
                'Content-Type': 'application/json',
            };

            const token = localStorage.getItem('github_token');
            if (token) {
                headers['Authorization'] = `Bearer ${token}`;
            }

            const response = await fetch(`http://localhost:8000/generate/${docType}`, {
                method: 'POST',
                headers: headers,
                body: JSON.stringify(body),
            });

            if (!response.ok) {
                throw new Error(`Error: ${response.statusText}`);
            }

            const data = await response.json();

            loadingSection.classList.add('hidden');
            resultSection.classList.remove('hidden');

            displayContent(data.content, docType);
            loadHistory(); // Refresh history

        } catch (error) {
            loadingSection.classList.add('hidden');
            alert('Failed to generate documentation: ' + error.message);
        }
    });

    function displayContent(content, type) {
        if (type.startsWith('diagram') || content.trim().startsWith('classDiagram') || content.trim().startsWith('sequenceDiagram')) {
            outputContent.classList.add('hidden');
            mermaidContent.classList.remove('hidden');
            mermaidContent.textContent = content;
            mermaid.run({ nodes: [mermaidContent] });
        } else {
            outputContent.classList.remove('hidden');
            mermaidContent.classList.add('hidden');
            outputContent.innerHTML = marked.parse(content);
        }

        // Setup download buttons
        downloadMdBtn.onclick = () => downloadFile(content, `${type}.md`, 'text/markdown');
        downloadWordBtn.onclick = () => downloadWord(content, `${type}.docx`);
    }

    async function loadHistory() {
        try {
            const response = await fetch('http://localhost:8000/documents');
            const docs = await response.json();

            if (historyList) {
                historyList.innerHTML = '';
                docs.forEach(doc => {
                    const li = document.createElement('li');
                    const date = new Date(doc.created_at).toLocaleDateString();
                    li.innerHTML = `
                        <strong>${doc.doc_type.toUpperCase()}</strong>
                        <span class="meta">${doc.repo_url.split('/').pop()} - ${date}</span>
                    `;
                    li.onclick = () => loadDocument(doc.id);
                    historyList.appendChild(li);
                });
            }
        } catch (error) {
            console.error('Failed to load history:', error);
        }
    }

    async function loadDocument(id) {
        try {
            const response = await fetch(`http://localhost:8000/documents/${id}`);
            const data = await response.json();

            resultSection.classList.remove('hidden');
            displayContent(data.content, data.doc_type);
        } catch (error) {
            alert('Failed to load document');
        }
    }

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
