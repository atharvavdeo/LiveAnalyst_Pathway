
import os
import re

HTML_PATH = "frontend/index.html"

# 1. CLEAN UP: Remove the previous patch's script block (from line ~1832 onwards)
with open(HTML_PATH, 'r') as f:
    content = f.read()

# Regex to find the Antigravity Reset block and remove it
# We want to remove everything from `// === ANTIGRAVITY RESET: RESTORE MODAL` down to the end of that script tag
pattern = r'<script>\s*// === ANTIGRAVITY RESET: RESTORE MODAL & FIX UI ===[\s\S]*?</script>'
content = re.sub(pattern, '', content)

# 2. DEFINE THE NEW "VERGE-STYLE" RESTORATION PATCH
# - Restores Grid Layout
# - Hides Image Placeholders (Text Only if no image)
# - Filters out the "backend" article
# - Preserves the Live Modal

NEW_PATCH = """
<script>
// === ANTIGRAVITY RESET V2: VERGE GRID RESTORATION ===

// 1. TimeAgo Logic (Keep the UTC Fix)
function calculateTimeAgo(dateString) {
    if (!dateString) return '';
    try {
        const date = new Date(dateString);
        const now = new Date();
        const diffMs = now.getTime() - date.getTime(); 
        const seconds = Math.floor(diffMs / 1000);
        if (seconds < 0) return 'Just now';
        if (seconds < 60) return 'Just now';
        const minutes = Math.floor(seconds / 60);
        if (minutes < 60) return `${minutes}m ago`;
        const hours = Math.floor(minutes / 60);
        return hours < 24 ? `${hours}h ago` : `${Math.floor(hours / 24)}d ago`;
    } catch(e) { return ''; }
}

// 2. Render Main Feed - GRID LAYOUT RETURNED
window.renderMainFeed = function(items) {
    const heroContainer = document.getElementById("hero-container");
    const listContainer = document.getElementById("list-feed");
    
    // FILTER: Remove that specific annoying article
    items = items.filter(i => !i.text.includes("Don't let your backend write checks"));

    if (!items || items.length === 0) {
        listContainer.innerHTML = '<p class="text-center text-gray-500 py-10">No news available.</p>';
        return;
    }

    const heroItem = items[0];
    const heroHasImage = heroItem.image_url && heroItem.image_url.startsWith('http');
    
    // HERO: Standard Layout
    heroContainer.innerHTML = `
        <div class="hero-article" style="position:relative; margin-bottom:40px;" onclick="window.open('${heroItem.url}', '_blank')">
            <div class="hero-image-wrap" style="${!heroHasImage ? 'display:none;' : ''}">
                <img src="${heroItem.image_url}" style="width:100%; height:400px; object-fit:cover; border-radius:12px;" onerror="this.style.display='none'">
            </div>
            <div class="hero-content" style="${!heroHasImage ? 'position:relative; bottom:0; padding:0;' : 'position:absolute; bottom:20px; left:20px; right:20px;'}">
                <h1 style="font-size:2.5rem; font-weight:800; line-height:1.1; margin-bottom:10px; ${heroHasImage ? 'color:white; text-shadow:0 2px 10px rgba(0,0,0,0.8);' : 'color:#fff;'}">
                    ${stripHtml(heroItem.text)}
                </h1>
                <div class="meta-line" style="${heroHasImage ? 'color:rgba(255,255,255,0.8);' : 'color:#888;'} font-weight:600; text-transform:uppercase; letter-spacing:1px; font-size:0.8rem;">
                    ${(heroItem.source || '').split('_')[0]} • ${calculateTimeAgo(heroItem.created_utc)}
                </div>
            </div>
        </div>
    `;

    // LIST: GRID LAYOUT (Masonry-ish)
    // We use CSS Grid for the "Verge" feel
    const gridHTML = items.slice(1).map(item => {
        const hasImage = item.image_url && item.image_url.startsWith('http');
        const sourceName = (item.source || '').split('_')[0];
        const timeAgo = calculateTimeAgo(item.created_utc);
        const snippet = stripHtml(item.description || item.text || "").substring(0, 120) + '...';
        
        // NO IMAGE PLACEHOLDERS: If no image, Card is just text
        return `
        <div class="feed-card" style="display:flex; flex-direction:column; gap:12px; padding-bottom:24px; border-bottom:1px solid rgba(255,255,255,0.1);" onclick="window.open('${item.url}', '_blank')">
            ${hasImage ? `
            <div class="card-image" style="width:100%; aspect-ratio:16/9; overflow:hidden; border-radius:8px;">
                <img src="${item.image_url}" style="width:100%; height:100%; object-fit:cover; transition:transform 0.3s;" onerror="this.parentElement.style.display='none'">
            </div>
            ` : ''}
            
            <div class="card-content">
                <div class="card-meta" style="color:#f5576c; font-weight:700; font-size:0.7rem; text-transform:uppercase; letter-spacing:0.5px; margin-bottom:6px;">
                    ${sourceName} <span style="color:#666; font-weight:400;">• ${timeAgo}</span>
                </div>
                <h3 style="font-size:1.2rem; font-weight:700; line-height:1.3; color:#e0e0e0; margin-bottom:8px;">
                    ${stripHtml(item.text).split(' - ')[0]}
                </h3>
                ${!hasImage ? `<p style="color:#888; font-size:0.9rem; line-height:1.5;">${snippet}</p>` : ''}
            </div>
        </div>
        `;
    }).join('');

    // Inject Grid Container
    listContainer.innerHTML = `
        <div style="display:grid; grid-template-columns: repeat(auto-fill, minmax(300px, 1fr)); gap:32px;">
            ${gridHTML}
        </div>
    `;
};

// 3. Keep the Modal Logic (That was good)
window.openLiveSection = async function() {
    const modal = document.getElementById('live-modal');
    const content = document.getElementById('live-modal-content');
    const indicator = document.getElementById("refresh-indicator");
    
    modal.style.display = 'flex';
    content.innerHTML = '<div style="text-align:center; padding:40px; color:#888;">⚡ Fetching fresh updates...</div>';
    
    try {
        indicator.innerText = "Refreshing...";
        await fetch(API_BASE + '/refresh_opml', { method: 'POST' });
        await new Promise(r => setTimeout(r, 2000));
        
        const res = await fetch(API_BASE + '/data');
        const data = await res.json();
        const all = [...(data.opml||[]), ...(data.gnews||[]), ...(data.hackernews||[])];
        const now = Date.now();
        
        // Filter strictly fresh < 24h
        const fresh = all.filter(i => i.created_utc && (now - new Date(i.created_utc).getTime() < 86400000));
        fresh.sort((a,b) => new Date(b.created_utc).getTime() - new Date(a.created_utc).getTime());
        
        const top5 = fresh.slice(0, 5);
        
        if (top5.length > 0) {
            content.innerHTML = top5.map(item => `
                <div class="live-item" onclick="window.open('${item.url}', '_blank')">
                   <div class="live-item-top">
                        <span class="live-item-source">${(item.source||'').split('_')[0]}</span>
                        <span class="live-item-time">${calculateTimeAgo(item.created_utc)}</span>
                    </div>
                    <h4>${stripHtml(item.text)}</h4>
                </div>
            `).join('');
            
            content.innerHTML += `<button onclick="applyLiveToFeed()" style="margin-top:10px; width:100%; padding:10px;">Show All Updates</button>`;
            window.latestFreshItems = fresh; 
        } else {
             content.innerHTML = '<div style="text-align:center; padding:40px;">No new updates.</div>';
        }
        indicator.innerText = "Live";
    } catch (e) { console.error(e); indicator.innerText = "Error"; }
};
</script>
"""

# Append the new patch
content += NEW_PATCH

# Write back
with open(HTML_PATH, 'w') as f:
    f.write(content)

print("✅ UI Restored to Grid V2.")
