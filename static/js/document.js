/**
 * NyayaAI - Document Analysis Script
 * Manages document intelligence actions, mode switching, and AI insights rendering.
 */

document.addEventListener('DOMContentLoaded', function() {
    const metaEl = document.getElementById('doc-metadata');
    const docId = window.NYAYA_DOC_ID || (metaEl ? metaEl.getAttribute('data-doc-id') : null);
    const modePills = document.querySelectorAll('.mode-pill');
    const runBtn = document.getElementById('btn-run-analysis');
    const loadingState = document.getElementById('analysis-loading');
    const resultsArea = document.getElementById('analysis-results-area');
    const fullContainer = document.getElementById('full-analysis-container');
    const textContainer = document.getElementById('text-analysis-container');
    const emptyHint = document.getElementById('analysis-empty-hint');
    const copyRawBtn = document.getElementById('btn-copy-doc-text');

    let currentMode = 'full';

    // Copy Raw Extracted Text
    if (copyRawBtn) {
        copyRawBtn.addEventListener('click', function() {
            const rawBox = document.getElementById('extracted-raw-text');
            if (!rawBox) return;
            const text = rawBox.innerText || rawBox.textContent;
            navigator.clipboard.writeText(text).then(() => {
                if (window.showToast) window.showToast('Extracted text copied to clipboard', 'success');
            }).catch(() => {
                if (window.showToast) window.showToast('Failed to copy text', 'error');
            });
        });
    }

    // Analysis Mode Pills
    modePills.forEach(pill => {
        pill.addEventListener('click', function() {
            modePills.forEach(p => p.classList.remove('active'));
            this.classList.add('active');
            currentMode = this.getAttribute('data-type') || 'full';
        });
    });

    // Run Analysis Button
    if (runBtn) {
        runBtn.addEventListener('click', function(e) {
            e.preventDefault();
            if (!docId) return;

            // UI loading state
            runBtn.disabled = true;
            loadingState.style.display = 'flex';
            if (emptyHint) emptyHint.style.display = 'none';
            if (resultsArea) resultsArea.style.display = 'none';

            fetch(`/api/document/${docId}/analyze`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ type: currentMode })
            })
            .then(res => {
                if (!res.ok) {
                    return res.json().then(data => {
                        throw new Error(data.error || 'Analysis failed');
                    });
                }
                return res.json();
            })
            .then(data => {
                runBtn.disabled = false;
                loadingState.style.display = 'none';
                resultsArea.style.display = 'block';

                if (data.type === 'full' && typeof data.result === 'object') {
                    renderFullAnalysis(data.result);
                } else {
                    renderTextAnalysis(data.result, currentMode);
                }

                if (window.showToast) {
                    window.showToast('Analysis completed successfully', 'success');
                }
            })
            .catch(err => {
                runBtn.disabled = false;
                loadingState.style.display = 'none';
                if (emptyHint) emptyHint.style.display = 'block';
                if (window.showToast) {
                    window.showToast(err.message || 'Error running AI analysis', 'error');
                }
            });
        });
    }

    function renderFullAnalysis(obj) {
        textContainer.style.display = 'none';
        fullContainer.style.display = 'block';

        const summaryEl = document.getElementById('res-summary');
        const pointsEl = document.getElementById('res-points');
        const concernsEl = document.getElementById('res-concerns');
        const questionsEl = document.getElementById('res-questions');

        if (summaryEl) summaryEl.innerHTML = formatBlockContent(obj.summary || 'No summary generated.');
        if (pointsEl) pointsEl.innerHTML = formatBlockContent(obj.important_points || 'No key points identified.');
        if (concernsEl) concernsEl.innerHTML = formatBlockContent(obj.possible_concerns || 'No immediate concerns flagged.');
        if (questionsEl) questionsEl.innerHTML = formatBlockContent(obj.questions_for_lawyer || 'No questions generated.');
    }

    function renderTextAnalysis(content, mode) {
        fullContainer.style.display = 'none';
        textContainer.style.display = 'block';

        const titleEl = document.getElementById('text-result-title');
        const iconEl = document.getElementById('text-result-icon');
        const textEl = document.getElementById('res-plain-text');

        const modeTitles = {
            'summarize': { title: 'Executive Summary', icon: '📋' },
            'simple': { title: 'Plain Language Breakdown', icon: '💬' },
            'key_points': { title: 'Key Points & Clauses', icon: '📌' },
            'dates': { title: 'Important Dates & Deadlines', icon: '📅' },
            'legal_terms': { title: 'Legal Terminology Explained', icon: '📖' }
        };

        const config = modeTitles[mode] || { title: 'AI Analysis Result', icon: '📄' };
        if (titleEl) titleEl.textContent = config.title;
        if (iconEl) iconEl.textContent = config.icon;
        if (textEl) textEl.innerHTML = formatBlockContent(content);
    }

    function formatBlockContent(data) {
        if (!data) return '<p class="text-muted">None</p>';
        if (Array.isArray(data)) {
            return '<ul class="analysis-list">' + data.map(item => `<li>${escapeHtml(item)}</li>`).join('') + '</ul>';
        }
        if (typeof data === 'string') {
            return data.split('\n')
                .filter(p => p.trim().length > 0)
                .map(p => {
                    if (p.trim().startsWith('- ') || p.trim().startsWith('• ')) {
                        return `<li>${escapeHtml(p.trim().slice(2))}</li>`;
                    }
                    return `<p>${escapeHtml(p.trim())}</p>`;
                })
                .join('');
        }
        return `<pre>${escapeHtml(JSON.stringify(data, null, 2))}</pre>`;
    }

    function escapeHtml(str) {
        if (!str) return '';
        return String(str)
            .replace(/&/g, '&amp;')
            .replace(/</g, '&lt;')
            .replace(/>/g, '&gt;')
            .replace(/"/g, '&quot;')
            .replace(/'/g, '&#039;');
    }
});
