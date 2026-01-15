// Branch Picker - Keyboard-first UI
(function() {
    'use strict';
    
    // State
    let state = {
        view: 'loading',  // 'loading' | 'conversations' | 'turns'
        conversations: [],
        turns: [],
        filtered: [],
        selectedIndex: 0,
        conversationId: null,
        conversationSlug: null,
        query: '',
        modalOpen: false,
        pendingBranch: null,
        lastG: 0  // For gg shortcut
    };
    
    // DOM refs
    const $ = id => document.getElementById(id);
    const search = $('search');
    const content = $('content');
    const breadcrumb = $('breadcrumb');
    const title = $('title');
    const modal = $('modal');
    
    // Initialize
    function init() {
        const params = new URLSearchParams(location.search);
        const convId = params.get('c') || params.get('conversation');
        
        // If conversation specified, go directly to branch point picker
        // User can still go back to conversation list via breadcrumb/Esc
        if (convId) {
            loadTurns(convId);
        } else {
            loadConversations();
        }
        
        // Event listeners
        search.addEventListener('input', onSearch);
        search.addEventListener('keydown', onSearchKeydown);
        document.addEventListener('keydown', onGlobalKeydown);
        $('btn-confirm').addEventListener('click', confirmBranch);
        $('btn-cancel').addEventListener('click', closeModal);
        modal.addEventListener('click', e => {
            if (e.target === modal) closeModal();
        });
    }
    
    // Data loading
    async function loadConversations() {
        state.view = 'loading';
        render();
        
        try {
            const resp = await fetch('/api/conversations');
            state.conversations = await resp.json();
            state.filtered = state.conversations;
            state.view = 'conversations';
            state.query = '';
            search.value = '';
            
            // Pre-select conversation if specified in URL
            if (state.preselectedConversation) {
                const idx = state.conversations.findIndex(
                    c => c.conversation_id === state.preselectedConversation
                );
                state.selectedIndex = idx >= 0 ? idx : 0;
            } else {
                state.selectedIndex = 0;
            }
            
            render();
            scrollToSelected();
        } catch (e) {
            content.innerHTML = '<div class="loading">Error loading conversations</div>';
        }
    }
    
    async function loadTurns(convId) {
        state.view = 'loading';
        state.conversationId = convId;
        render();
        
        try {
            // Load conversation metadata
            const convResp = await fetch('/api/conversations');
            const convs = await convResp.json();
            const conv = convs.find(c => c.conversation_id === convId);
            state.conversationSlug = conv ? conv.slug : convId;
            
            // Load turns
            const resp = await fetch('/api/messages?conversation=' + convId);
            state.turns = await resp.json();
            state.filtered = state.turns;
            state.view = 'turns';
            state.selectedIndex = 0;
            state.query = '';
            search.value = '';
            render();
        } catch (e) {
            content.innerHTML = '<div class="loading">Error loading conversation</div>';
        }
    }
    
    // Search/filter
    function onSearch(e) {
        state.query = e.target.value.toLowerCase();
        filterItems();
        render();
    }
    
    function filterItems() {
        const q = state.query;
        
        if (state.view === 'conversations') {
            if (!q) {
                state.filtered = state.conversations;
            } else {
                state.filtered = state.conversations.filter(c => 
                    (c.slug || '').toLowerCase().includes(q) ||
                    c.conversation_id.toLowerCase().includes(q)
                );
            }
        } else if (state.view === 'turns') {
            if (!q) {
                state.filtered = state.turns;
            } else {
                state.filtered = state.turns.filter(t =>
                    t.summary.toLowerCase().includes(q) ||
                    t.type.toLowerCase().includes(q) ||
                    String(t.sequence_id).includes(q)
                );
            }
        }
        
        // Reset selection if out of bounds
        if (state.selectedIndex >= state.filtered.length) {
            state.selectedIndex = Math.max(0, state.filtered.length - 1);
        }
    }
    
    // Keyboard handling
    function onSearchKeydown(e) {
        if (e.key === 'Escape') {
            if (state.query) {
                search.value = '';
                state.query = '';
                filterItems();
                render();
            } else {
                search.blur();
            }
            e.preventDefault();
        } else if (e.key === 'ArrowDown' || (e.key === 'n' && e.ctrlKey)) {
            moveSelection(1);
            e.preventDefault();
        } else if (e.key === 'ArrowUp' || (e.key === 'p' && e.ctrlKey)) {
            moveSelection(-1);
            e.preventDefault();
        } else if (e.key === 'Enter') {
            selectItem();
            e.preventDefault();
        }
    }
    
    function onGlobalKeydown(e) {
        // Ignore if modal open (except Escape/Enter)
        if (state.modalOpen) {
            if (e.key === 'Escape') {
                closeModal();
                e.preventDefault();
            } else if (e.key === 'Enter') {
                confirmBranch();
                e.preventDefault();
            }
            return;
        }
        
        // Ignore if typing in search
        if (document.activeElement === search && !e.ctrlKey && !e.metaKey) {
            return;
        }
        
        switch (e.key) {
            case '/':
                search.focus();
                search.select();
                e.preventDefault();
                break;
            case 'j':
            case 'ArrowDown':
                moveSelection(1);
                e.preventDefault();
                break;
            case 'k':
            case 'ArrowUp':
                moveSelection(-1);
                e.preventDefault();
                break;
            case 'Enter':
                selectItem();
                e.preventDefault();
                break;
            case 'Escape':
                if (state.view === 'turns') {
                    loadConversations();
                    history.pushState({}, '', location.pathname);
                }
                e.preventDefault();
                break;
            case 'g':
                const now = Date.now();
                if (now - state.lastG < 500) {
                    // gg - go to top
                    state.selectedIndex = 0;
                    render();
                    scrollToSelected();
                }
                state.lastG = now;
                break;
            case 'G':
                // G - go to bottom
                state.selectedIndex = state.filtered.length - 1;
                render();
                scrollToSelected();
                e.preventDefault();
                break;
            case 'Home':
                state.selectedIndex = 0;
                render();
                scrollToSelected();
                e.preventDefault();
                break;
            case 'End':
                state.selectedIndex = state.filtered.length - 1;
                render();
                scrollToSelected();
                e.preventDefault();
                break;
        }
    }
    
    function moveSelection(delta) {
        const len = state.filtered.length;
        if (len === 0) return;
        
        state.selectedIndex = Math.max(0, Math.min(len - 1, state.selectedIndex + delta));
        render();
        scrollToSelected();
    }
    
    function scrollToSelected() {
        const selected = content.querySelector('.selected');
        if (selected) {
            selected.scrollIntoView({ block: 'nearest', behavior: 'smooth' });
        }
    }
    
    function selectItem() {
        const item = state.filtered[state.selectedIndex];
        if (!item) return;
        
        if (state.view === 'conversations') {
            history.pushState({}, '', '?c=' + item.conversation_id);
            loadTurns(item.conversation_id);
        } else if (state.view === 'turns') {
            showBranchModal(item);
        }
    }
    
    // Modal
    function showBranchModal(turn) {
        state.modalOpen = true;
        state.pendingBranch = turn;
        $('modal-seq').textContent = '#' + turn.sequence_id;
        $('modal-summary').textContent = turn.summary;
        modal.classList.add('active');
        $('btn-confirm').focus();
    }
    
    function closeModal() {
        state.modalOpen = false;
        state.pendingBranch = null;
        modal.classList.remove('active');
        search.focus();
    }
    
    async function confirmBranch() {
        if (!state.pendingBranch) return;
        
        const modalContent = modal.querySelector('.modal-content');
        modalContent.innerHTML = '<div class="loading">Creating branch...</div>';
        
        try {
            const resp = await fetch('/api/branch', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    conversation_id: state.conversationId,
                    sequence_id: state.pendingBranch.sequence_id
                })
            });
            
            const data = await resp.json();
            
            if (data.success) {
                // Build the Shelley URL - use port 9999 on same host
                var shelleyUrl = window.location.protocol + '//' + window.location.hostname + ':9999/c/' + data.new_conversation_id;
                modalContent.innerHTML = 
                    '<div class="modal-success">' +
                    '<h3>✓ Branch Created</h3>' +
                    '<p>New conversation: <code>' + data.new_conversation_id + '</code></p>' +
                    '<p><a href="' + shelleyUrl + '" target="_blank">Open in Shelley →</a></p>' +
                    '</div>';
            } else {
                throw new Error(data.error || 'Unknown error');
            }
        } catch (e) {
            modalContent.innerHTML = 
                '<div class="modal-error">' +
                '<h3>Error</h3>' +
                '<p>' + e.message + '</p>' +
                '<button class="btn-secondary" onclick="location.reload()">Retry</button>' +
                '</div>';
        }
    }
    
    // Rendering
    function render() {
        // Update title and breadcrumb
        if (state.view === 'conversations') {
            title.textContent = 'Select Conversation';
            breadcrumb.innerHTML = '';
        } else if (state.view === 'turns') {
            title.textContent = 'Branch: ' + (state.conversationSlug || state.conversationId);
            breadcrumb.innerHTML = '<a href="' + location.pathname + '">Conversations</a> / ' + 
                (state.conversationSlug || state.conversationId);
        }
        
        // Render content
        if (state.view === 'loading') {
            content.innerHTML = '<div class="loading">Loading...</div>';
        } else if (state.view === 'conversations') {
            renderConversations();
        } else if (state.view === 'turns') {
            renderTurns();
        }
    }
    
    function highlight(text, query) {
        if (!query) return escapeHtml(text);
        const escaped = escapeHtml(text);
        const regex = new RegExp('(' + escapeRegex(query) + ')', 'gi');
        return escaped.replace(regex, '<span class="highlight">$1</span>');
    }
    
    function escapeHtml(text) {
        return text
            .replace(/&/g, '&amp;')
            .replace(/</g, '&lt;')
            .replace(/>/g, '&gt;')
            .replace(/"/g, '&quot;');
    }
    
    function escapeRegex(str) {
        return str.replace(/[.*+?^${}()|[\]\\]/g, '\\$&');
    }
    
    function renderConversations() {
        if (state.filtered.length === 0) {
            content.innerHTML = '<div class="loading">No conversations found</div>';
            return;
        }
        
        let html = '';
        if (state.query) {
            html += '<div class="match-count">' + state.filtered.length + ' match' + 
                (state.filtered.length !== 1 ? 'es' : '') + '</div>';
        }
        
        html += '<ul class="conversation-list">';
        state.filtered.forEach((c, i) => {
            const selected = i === state.selectedIndex ? ' selected' : '';
            const slug = c.slug || '(untitled)';
            const date = new Date(c.updated_at).toLocaleDateString();
            
            html += '<li class="conversation' + selected + '" data-index="' + i + '">' +
                '<div class="slug">' + highlight(slug, state.query) + '</div>' +
                '<div class="meta"><span class="id">' + highlight(c.conversation_id, state.query) + 
                '</span> · ' + date + '</div></li>';
        });
        html += '</ul>';
        
        content.innerHTML = html;
        addClickHandlers();
    }
    
    function renderTurns() {
        if (state.filtered.length === 0) {
            content.innerHTML = '<div class="loading">No turns found</div>';
            return;
        }
        
        let html = '';
        if (state.query) {
            html += '<div class="match-count">' + state.filtered.length + ' match' + 
                (state.filtered.length !== 1 ? 'es' : '') + '</div>';
        }
        
        html += '<ul class="timeline">';
        state.filtered.forEach((t, i) => {
            const selected = i === state.selectedIndex ? ' selected' : '';
            
            html += '<li class="turn ' + t.type + selected + '" data-index="' + i + '">' +
                '<div class="header">' +
                '<span class="type">' + t.type + '</span>' +
                '<span class="seq">#' + t.sequence_id + '</span>' +
                '</div>' +
                '<div class="summary">' + highlight(t.summary, state.query) + '</div>' +
                '</li>';
        });
        html += '</ul>';
        
        content.innerHTML = html;
        addClickHandlers();
    }
    
    function addClickHandlers() {
        content.querySelectorAll('[data-index]').forEach(el => {
            el.addEventListener('click', () => {
                state.selectedIndex = parseInt(el.dataset.index);
                render();
                selectItem();
            });
        });
    }
    
    // Start
    init();
})();
