/**
 * Biomedical GraphRAG Frontend Application
 */

class BioGraphRAG {
    constructor() {
        this.apiBase = '';
        this.queryType = 'hybrid';
        this.isLoading = false;
        
        this.init();
    }
    
    init() {
        this.bindElements();
        this.bindEvents();
        this.loadStats();
    }
    
    bindElements() {
        // Query elements
        this.queryInput = document.getElementById('query-input');
        this.submitBtn = document.getElementById('submit-btn');
        this.toggleBtns = document.querySelectorAll('.toggle-btn');
        this.exampleBtns = document.querySelectorAll('.example-btn');
        
        // Results elements
        this.resultsSection = document.getElementById('results-section');
        this.loadingState = document.getElementById('loading-state');
        this.loadingStep = document.getElementById('loading-step');
        this.resultsContent = document.getElementById('results-content');
        this.queryTypeBadge = document.getElementById('query-type-badge');
        this.queryTime = document.getElementById('query-time');
        this.answerContent = document.getElementById('answer-content');
        this.sourcesGrid = document.getElementById('sources-grid');
        this.enrichmentSection = document.getElementById('enrichment-section');
        this.enrichmentContent = document.getElementById('enrichment-content');
    }
    
    bindEvents() {
        // Submit button
        this.submitBtn.addEventListener('click', () => this.submitQuery());
        
        // Enter key in textarea (Cmd/Ctrl + Enter)
        this.queryInput.addEventListener('keydown', (e) => {
            if ((e.metaKey || e.ctrlKey) && e.key === 'Enter') {
                this.submitQuery();
            }
        });
        
        // Query type toggle
        this.toggleBtns.forEach(btn => {
            btn.addEventListener('click', () => {
                this.toggleBtns.forEach(b => b.classList.remove('active'));
                btn.classList.add('active');
                this.queryType = btn.dataset.type;
            });
        });
        
        // Example queries
        this.exampleBtns.forEach(btn => {
            btn.addEventListener('click', () => {
                this.queryInput.value = btn.dataset.query;
                this.queryInput.focus();
            });
        });
    }
    
    async loadStats() {
        try {
            const response = await fetch(`${this.apiBase}/api/stats`);
            if (response.ok) {
                const stats = await response.json();
                document.getElementById('paper-count').textContent = 
                    this.formatNumber(stats.neo4j_nodes.papers);
                document.getElementById('gene-count').textContent = 
                    this.formatNumber(stats.neo4j_nodes.genes);
                document.getElementById('citation-count').textContent = 
                    this.formatNumber(stats.citation_relationships);
            }
        } catch (error) {
            console.log('Stats not available yet');
        }
    }
    
    formatNumber(num) {
        if (num >= 1000) {
            return (num / 1000).toFixed(num >= 10000 ? 0 : 1) + 'K';
        }
        return num.toLocaleString();
    }
    
    async submitQuery() {
        const question = this.queryInput.value.trim();
        
        if (!question || this.isLoading) return;
        
        this.isLoading = true;
        this.showLoading();
        
        const startTime = Date.now();
        
        try {
            const response = await fetch(`${this.apiBase}/api/query`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                    question: question,
                    query_type: this.queryType,
                    top_k: 5
                })
            });
            
            if (!response.ok) {
                const error = await response.json();
                throw new Error(error.detail || 'Query failed');
            }
            
            const data = await response.json();
            const elapsed = ((Date.now() - startTime) / 1000).toFixed(2);
            
            this.showResults(data, elapsed);
            
        } catch (error) {
            console.error('Query error:', error);
            this.showError(error.message);
        } finally {
            this.isLoading = false;
        }
    }
    
    showLoading() {
        this.resultsSection.classList.add('visible');
        this.loadingState.classList.add('active');
        this.resultsContent.classList.remove('active');
        this.submitBtn.disabled = true;
        
        // Animate loading steps
        const steps = [
            'Retrieving relevant documents...',
            'Generating embeddings...',
            'Querying knowledge graph...',
            'Synthesizing response...'
        ];
        
        let stepIndex = 0;
        this.loadingInterval = setInterval(() => {
            this.loadingStep.textContent = steps[stepIndex % steps.length];
            stepIndex++;
        }, 2000);
    }
    
    showResults(data, elapsed) {
        clearInterval(this.loadingInterval);
        
        this.loadingState.classList.remove('active');
        this.resultsContent.classList.add('active');
        this.submitBtn.disabled = false;
        
        // Update metadata
        this.queryTypeBadge.textContent = data.query_type === 'hybrid' ? 'Hybrid' : 'Vector';
        this.queryTime.textContent = `${elapsed}s`;
        
        // Render answer
        this.answerContent.innerHTML = this.formatMarkdown(data.answer);
        
        // Render sources
        this.renderSources(data.sources);
        
        // Render Neo4j enrichment
        if (data.neo4j_enrichment && Object.keys(data.neo4j_enrichment).length > 0) {
            this.enrichmentSection.classList.add('visible');
            this.renderEnrichment(data.neo4j_enrichment);
        } else {
            this.enrichmentSection.classList.remove('visible');
        }
        
        // Scroll to results
        this.resultsSection.scrollIntoView({ behavior: 'smooth', block: 'start' });
    }
    
    showError(message) {
        clearInterval(this.loadingInterval);
        
        this.loadingState.classList.remove('active');
        this.resultsContent.classList.add('active');
        this.submitBtn.disabled = false;
        
        this.queryTypeBadge.textContent = 'Error';
        this.queryTime.textContent = '';
        
        this.answerContent.innerHTML = `
            <div style="color: var(--accent-magenta);">
                <strong>Error:</strong> ${this.escapeHtml(message)}
            </div>
            <p style="margin-top: 1rem; color: var(--text-muted);">
                Please check that the API server is running and try again.
            </p>
        `;
        
        this.sourcesGrid.innerHTML = '';
        this.enrichmentSection.classList.remove('visible');
    }
    
    renderSources(sources) {
        if (!sources || sources.length === 0) {
            this.sourcesGrid.innerHTML = '<p style="color: var(--text-muted);">No sources found</p>';
            return;
        }
        
        this.sourcesGrid.innerHTML = sources.map(source => `
            <div class="source-card">
                <div class="source-header">
                    <span class="source-pmid">PMID: ${this.escapeHtml(source.pmid)}</span>
                    <span class="source-score">Score: ${(source.score * 100).toFixed(1)}%</span>
                </div>
                <div class="source-title">${this.escapeHtml(source.title)}</div>
                <div class="source-meta">
                    ${source.authors && source.authors.length > 0 ? `
                        <div class="source-authors">
                            ${source.authors.map(a => this.escapeHtml(a.name || a)).join(', ')}
                            ${source.authors.length < 3 ? '' : ' et al.'}
                        </div>
                    ` : ''}
                    ${source.journal ? `<span>${this.escapeHtml(source.journal)}</span>` : ''}
                    ${source.publication_date ? ` · ${source.publication_date}` : ''}
                </div>
            </div>
        `).join('');
    }
    
    renderEnrichment(enrichment) {
        const tools = Object.entries(enrichment);
        
        if (tools.length === 0) {
            this.enrichmentContent.innerHTML = '<p style="color: var(--text-muted);">No graph enrichment data</p>';
            return;
        }
        
        this.enrichmentContent.innerHTML = tools.map(([toolName, results]) => {
            const formattedName = toolName.replace(/_/g, ' ').replace(/\b\w/g, c => c.toUpperCase());
            
            let resultsHtml = '';
            if (Array.isArray(results)) {
                resultsHtml = results.slice(0, 5).map(item => {
                    if (typeof item === 'object') {
                        return `<div class="tool-item">${this.formatToolItem(item)}</div>`;
                    }
                    return `<div class="tool-item">${this.escapeHtml(String(item))}</div>`;
                }).join('');
                if (results.length > 5) {
                    resultsHtml += `<div class="tool-item" style="color: var(--text-muted);">... and ${results.length - 5} more</div>`;
                }
            } else if (typeof results === 'string') {
                resultsHtml = `<div class="tool-item">${this.escapeHtml(results)}</div>`;
            } else {
                resultsHtml = `<div class="tool-item">${this.escapeHtml(JSON.stringify(results, null, 2))}</div>`;
            }
            
            return `
                <div class="enrichment-tool">
                    <div class="tool-name">${formattedName}</div>
                    <div class="tool-results">${resultsHtml}</div>
                </div>
            `;
        }).join('');
    }
    
    formatToolItem(item) {
        const parts = [];
        
        if (item.pmid) parts.push(`<strong>PMID:</strong> ${this.escapeHtml(item.pmid)}`);
        if (item.title) parts.push(`<strong>Title:</strong> ${this.escapeHtml(item.title)}`);
        if (item.name) parts.push(`<strong>Name:</strong> ${this.escapeHtml(item.name)}`);
        if (item.shared_terms) parts.push(`<strong>Shared Terms:</strong> ${item.shared_terms}`);
        if (item.paper_count) parts.push(`<strong>Papers:</strong> ${item.paper_count}`);
        if (item.institution) parts.push(`<strong>Institution:</strong> ${this.escapeHtml(item.institution)}`);
        
        if (parts.length === 0) {
            return this.escapeHtml(JSON.stringify(item));
        }
        
        return parts.join(' · ');
    }
    
    formatMarkdown(text) {
        if (!text) return '';
        
        // Basic markdown formatting
        let html = this.escapeHtml(text);
        
        // Headers
        html = html.replace(/^### (.+)$/gm, '<h3>$1</h3>');
        html = html.replace(/^## (.+)$/gm, '<h2>$1</h2>');
        html = html.replace(/^# (.+)$/gm, '<h1>$1</h1>');
        
        // Bold
        html = html.replace(/\*\*(.+?)\*\*/g, '<strong>$1</strong>');
        
        // Italic
        html = html.replace(/\*(.+?)\*/g, '<em>$1</em>');
        
        // Inline code
        html = html.replace(/`([^`]+)`/g, '<code>$1</code>');
        
        // Line breaks
        html = html.replace(/\n\n/g, '</p><p>');
        html = html.replace(/\n/g, '<br>');
        
        // Wrap in paragraphs
        html = '<p>' + html + '</p>';
        
        // Lists (basic)
        html = html.replace(/<p>- (.+?)<\/p>/g, '<li>$1</li>');
        html = html.replace(/(<li>.+<\/li>)/gs, '<ul>$1</ul>');
        
        // Numbered lists
        html = html.replace(/<p>(\d+)\. (.+?)<\/p>/g, '<li>$2</li>');
        
        return html;
    }
    
    escapeHtml(text) {
        if (!text) return '';
        const div = document.createElement('div');
        div.textContent = text;
        return div.innerHTML;
    }
}

// Initialize app when DOM is ready
document.addEventListener('DOMContentLoaded', () => {
    window.app = new BioGraphRAG();
});

