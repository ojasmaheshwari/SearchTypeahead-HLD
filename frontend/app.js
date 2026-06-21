document.addEventListener('DOMContentLoaded', () => {
    const searchInput = document.getElementById('searchInput');
    const searchButton = document.getElementById('searchButton');
    const suggestionsDropdown = document.getElementById('suggestionsDropdown');
    const loader = document.getElementById('searchLoader');
    const statusMessage = document.getElementById('statusMessage');
    const trendingTags = document.getElementById('trendingTags');
    const cacheDebugSection = document.getElementById('cacheDebugSection');

    let debounceTimer;
    let selectedIndex = -1;
    let currentSuggestions = [];

    // Fetch trending searches on load
    fetchTrending();

    searchInput.addEventListener('input', (e) => {
        const query = e.target.value.trim();

        clearTimeout(debounceTimer);

        if (!query) {
            closeSuggestions();
            cacheDebugSection.classList.remove('active');
            return;
        }

        // Debounce API call
        debounceTimer = setTimeout(() => {
            fetchSuggestions(query);
            fetchCacheDebug(query);
        }, 300);
    });

    searchInput.addEventListener('keydown', (e) => {
        if (!suggestionsDropdown.classList.contains('active')) {
            if (e.key === 'Enter') {
                performSearch(searchInput.value);
            }
            return;
        }

        const items = suggestionsDropdown.querySelectorAll('.suggestion-item');

        if (e.key === 'ArrowDown') {
            e.preventDefault();
            selectedIndex = (selectedIndex + 1) % items.length;
            updateSelection(items);
        } else if (e.key === 'ArrowUp') {
            e.preventDefault();
            selectedIndex = (selectedIndex - 1 + items.length) % items.length;
            updateSelection(items);
        } else if (e.key === 'Enter') {
            e.preventDefault();
            if (selectedIndex >= 0 && selectedIndex < items.length) {
                performSearch(currentSuggestions[selectedIndex].query);
            } else {
                performSearch(searchInput.value);
            }
        } else if (e.key === 'Escape') {
            closeSuggestions();
        }
    });

    searchButton.addEventListener('click', () => {
        performSearch(searchInput.value);
    });

    // Close dropdown on click outside
    document.addEventListener('click', (e) => {
        if (!e.target.closest('.search-container')) {
            closeSuggestions();
        }
    });

    async function fetchSuggestions(prefix) {
        loader.classList.add('active');
        try {
            const response = await fetch(`/suggest?q=${encodeURIComponent(prefix)}`);
            if (response.ok) {
                const data = await response.json();
                renderSuggestions(data.suggestions || []);
            } else {
                renderSuggestions([]);
            }
        } catch (error) {
            console.error("Error fetching suggestions:", error);
            renderSuggestions([]);
        } finally {
            loader.classList.remove('active');
        }
    }

    async function fetchCacheDebug(prefix) {
        try {
            const response = await fetch(`/cache/debug?prefix=${encodeURIComponent(prefix.trim().toLowerCase())}`);
            if (response.ok) {
                const data = await response.json();
                cacheDebugSection.innerHTML = `
                    <div>Cache Query: ${data.prefix}</div>
                    <div>Node: ${data.cache_node}</div>
                    <div>Status: <span class="${data.cache_hit ? 'cache-hit' : 'cache-miss'}">${data.cache_hit ? 'HIT' : 'MISS'}</span></div>
                    <div>Hash: ${data.hash}</div>
                `;
                cacheDebugSection.classList.add('active');
            }
        } catch (e) {
            console.error(e);
        }
    }

    function renderSuggestions(suggestions) {
        currentSuggestions = suggestions;
        selectedIndex = -1;
        suggestionsDropdown.innerHTML = '';

        if (suggestions.length === 0) {
            closeSuggestions();
            return;
        }

        suggestions.forEach((item, index) => {
            const div = document.createElement('div');
            div.className = 'suggestion-item';

            // Highlight matching prefix
            const q = searchInput.value.trim().toLowerCase();
            let queryHtml = item.query;
            if (item.query.toLowerCase().startsWith(q)) {
                queryHtml = `<strong>${item.query.substring(0, q.length)}</strong>${item.query.substring(q.length)}`;
            }

            div.innerHTML = `
                <span class="suggestion-query">${queryHtml}</span>
                <span class="suggestion-count">${formatNumber(item.count)}</span>
            `;

            div.addEventListener('click', () => {
                performSearch(item.query);
            });

            suggestionsDropdown.appendChild(div);
        });

        suggestionsDropdown.classList.add('active');
    }

    function updateSelection(items) {
        items.forEach((item, index) => {
            if (index === selectedIndex) {
                item.classList.add('selected');
                searchInput.value = currentSuggestions[index].query; // Autofill input
            } else {
                item.classList.remove('selected');
            }
        });
    }

    function closeSuggestions() {
        suggestionsDropdown.classList.remove('active');
        selectedIndex = -1;
    }

    async function performSearch(query) {
        query = query.trim();
        if (!query) return;

        searchInput.value = query;
        closeSuggestions();

        try {
            const response = await fetch('/search', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({ query: query })
            });

            if (response.ok) {
                showStatus("Searched");
                // Refresh trending after search just to show life
                setTimeout(fetchTrending, 1000);
            } else {
                showStatus("Error searching");
            }
        } catch (error) {
            showStatus("API Error");
        }
    }

    function showStatus(msg) {
        statusMessage.textContent = msg;
        statusMessage.classList.add('show');
        setTimeout(() => {
            statusMessage.classList.remove('show');
        }, 2000);
    }

    async function fetchTrending() {
        try {
            const response = await fetch('/trending');
            if (response.ok) {
                const data = await response.json();
                renderTrending(data);
            }
        } catch (error) {
            console.error("Error fetching trending:", error);
        }
    }

    function renderTrending(data) {
        trendingTags.innerHTML = '';
        data.forEach(item => {
            const div = document.createElement('div');
            div.className = 'tag';
            div.innerHTML = `
                <span class="query">${item.query}</span>
                <span class="count">${formatNumber(item.count)}</span>
            `;
            div.addEventListener('click', () => {
                performSearch(item.query);
            });
            trendingTags.appendChild(div);
        });
    }

    function formatNumber(num) {
        if (num >= 1000000) return (num / 1000000).toFixed(1) + 'M';
        if (num >= 1000) return (num / 1000).toFixed(1) + 'k';
        return num.toString();
    }
});
