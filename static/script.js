/**
 * Alpha Engine — Frontend Interactivity
 * =======================================
 */

// Click handler for stock rows -> navigate to analyser
document.querySelectorAll('.clickable-row').forEach(row => {
    row.addEventListener('click', () => {
        const ticker = row.dataset.ticker;
        if (ticker) {
            window.location.href = `analyse.html?ticker=${ticker}`;
        }
    });
});

// Click handler for ticker cells
document.querySelectorAll('.ticker-cell').forEach(cell => {
    cell.addEventListener('click', (e) => {
        e.stopPropagation();
        const ticker = cell.textContent.trim();
        if (ticker) {
            window.location.href = `analyse.html?ticker=${ticker}`;
        }
    });
});

// Auto-refresh timestamp
const timeEl = document.querySelector('.scan-time');
if (timeEl) {
    const updateAge = () => {
        const scanTime = timeEl.textContent;
        // Could add "X minutes ago" logic here
    };
    setInterval(updateAge, 60000);
}

// Sortable tables
document.querySelectorAll('.data-table thead th').forEach((th, i) => {
    th.style.cursor = 'pointer';
    th.addEventListener('click', () => {
        const table = th.closest('table');
        const tbody = table.querySelector('tbody');
        const rows = Array.from(tbody.querySelectorAll('tr'));
        const isNumeric = (val) => !isNaN(parseFloat(val.replace(/[^0-9.-]/g, '')));

        const currentDir = th.dataset.sortDir || 'asc';
        const newDir = currentDir === 'asc' ? 'desc' : 'asc';

        // Reset all headers
        table.querySelectorAll('th').forEach(h => {
            h.dataset.sortDir = '';
            h.textContent = h.textContent.replace(/ [▲▼]/, '');
        });

        th.dataset.sortDir = newDir;
        th.textContent += newDir === 'asc' ? ' ▲' : ' ▼';

        rows.sort((a, b) => {
            let aVal = a.children[i]?.textContent.trim() || '';
            let bVal = b.children[i]?.textContent.trim() || '';

            if (isNumeric(aVal) && isNumeric(bVal)) {
                aVal = parseFloat(aVal.replace(/[^0-9.-]/g, ''));
                bVal = parseFloat(bVal.replace(/[^0-9.-]/g, ''));
            }

            if (aVal < bVal) return newDir === 'asc' ? -1 : 1;
            if (aVal > bVal) return newDir === 'asc' ? 1 : -1;
            return 0;
        });

        rows.forEach(row => tbody.appendChild(row));
    });
});

// Keyboard shortcut: / to focus search
document.addEventListener('keydown', (e) => {
    if (e.key === '/' && document.activeElement.tagName !== 'INPUT') {
        e.preventDefault();
        const input = document.getElementById('ticker-input');
        if (input) input.focus();
    }
});
