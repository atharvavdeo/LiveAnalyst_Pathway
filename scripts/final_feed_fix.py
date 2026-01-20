
import os
import re

HTML_PATH = "frontend/index.html"

# 1. CLEAN UP: Remove previous script patches
with open(HTML_PATH, 'r') as f:
    content = f.read()

# Pattern to remove Antigravity Reset V2 and V1
pattern1 = r'<script>\s*// === ANTIGRAVITY RESET V2: VERGE GRID RESTORATION ===[\s\S]*?</script>'
pattern2 = r'<script>\s*// === ANTIGRAVITY RESET: RESTORE MODAL & FIX UI ===[\s\S]*?</script>'
content = re.sub(pattern1, '', content)
content = re.sub(pattern2, '', content)

# 2. DEFINITIVE FINAL PATCH
# - GLOBAL PULSE: OPML ONLY, 5s REFRESH
# - MAIN FEED: MIXED GNEWS/OPML, 15s REFRESH
# - LAYOUT: GRID V2 (Approved)
# - LOGIC: Strict Time Sorting

FINAL_PATCH = """
<script>
// === ANTIGRAVITY FINAL: STRICT USER REQUIREMENTS ===

// 1. UTC-Aware Time Ago
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

// 2. GLOBAL PULSE: OPML ONLY, 5s REFRESH
window.fetchWorldUpdates = async function() {
    try {
        const response = await fetch(API_BASE + '/data');
        const data = await response.json();

        // USER DEMAND: ONLY OPML IN GLOBAL PULSE
        const opmlOnly = data.opml || [];

        // STRICT FRESHNESS: Only Show < 24h
        const now = Date.now();
        const freshPulse = opmlOnly.filter(item => {
            if (!item.created_utc) return false;
            return (now - new Date(item.created_utc).getTime()) < (24 * 60 * 60 * 1000);
        });

        // Sort: Newest First
        freshPulse.sort((a,b) => new Date(b.created_utc).getTime() - new Date(a.created_utc).getTime());
        const top5 = freshPulse.slice(0, 5);

        const container = document.getElementById("global-updates");
        
        if (top5.length > 0) {
            container.innerHTML = top5.map((item, index) => {
                const safeSource = (item.feed_title || item.source || 'OPML').toUpperCase();
                const displaySource = safeSource.length > 15 ? safeSource.substring(0, 15) + '..' : safeSource;
                
                return `
                <div class="popular-item" onclick="window.open('${item.url}', '_blank')" style="cursor:pointer;">
                    <div class="index-circle" style="background:${index===0?'#ff4757':'#333'}">${index + 1}</div>
                    <div class="popular-info">
                        <h4 title="${stripHtml(item.text).replace(/"/g, '&quot;')}">${stripHtml(item.text)}</h4>
                        <span style="color:#888; font-size:0.75rem;">${displaySource} • ${calculateTimeAgo(item.created_utc)}</span>
                    </div>
                </div>
            `;
            }).join('');
        }
    } catch (e) { console.error("Pulse Error", e); }
};

// AUTO-REFRESH GLOBAL PULSE EVERY 5 SECONDS
setInterval(window.fetchWorldUpdates, 5000);


// 3. MAIN FEED: MIXED SOURCES, GRID LAYOUT, 15s REFRESH
window.renderMainFeed = function(items) {
    const listContainer = document.getElementById("list-feed");
    const heroContainer = document.getElementById("hero-container");
    
    // FILTER BLACKLIST
    items = items.filter(i => !i.text.includes("Don't let your backend write checks"));

    if (!items || items.length === 0) {
        if (!listContainer.innerHTML.includes("available")) {
             listContainer.innerHTML = '<p class="text-center text-gray-500 py-10">No specific news available. Check Live Feed.</p>';
        }
        return;
    }

    const heroItem = items[0];
    const heroHasImage = heroItem.image_url && heroItem.image_url.startsWith('http');
    
    // HERO RENDER
    heroContainer.innerHTML = `
        <div class="hero-article" style="position:relative; margin-bottom:40px; cursor:pointer;" onclick="window.open('${heroItem.url}', '_blank')">
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

    // GRID RENDER
    const gridHTML = items.slice(1).map(item => {
        const hasImage = item.image_url && item.image_url.startsWith('http');
        const sourceName = (item.source || '').split('_')[0];
        const timeAgo = calculateTimeAgo(item.created_utc);
        const snippet = stripHtml(item.description || item.text || "").substring(0, 100) + '...';
        
        // MIXED AESTHETIC: NO PLACEHOLDERS
        return `
        <div class="feed-card" style="display:flex; flex-direction:column; gap:12px; padding-bottom:24px; border-bottom:1px solid rgba(255,255,255,0.1); cursor:pointer;" onclick="window.open('${item.url}', '_blank')">
            ${hasImage ? `
            <div class="card-image" style="width:100%; aspect-ratio:16/9; overflow:hidden; border-radius:8px;">
                <img src="${item.image_url}" style="width:100%; height:100%; object-fit:cover; transition:transform 0.3s;" onerror="this.parentElement.style.display='none'">
            </div>
            ` : ''}
            <div class="card-content">
                <div class="card-meta" style="color:#f5576c; font-weight:700; font-size:0.7rem; text-transform:uppercase; letter-spacing:0.5px; margin-bottom:6px;">
                    ${sourceName} <span style="color:#666; font-weight:400;">• ${timeAgo}</span>
                </div>
                <h3 style="font-size:1.1rem; font-weight:700; line-height:1.3; color:#e0e0e0; margin-bottom:8px;">
                    ${stripHtml(item.text).split(' - ')[0]}
                </h3>
                ${!hasImage ? `<p style="color:#888; font-size:0.9rem; line-height:1.5;">${snippet}</p>` : ''}
            </div>
        </div>
        `;
    }).join('');

    listContainer.innerHTML = `
        <div style="display:grid; grid-template-columns: repeat(auto-fill, minmax(300px, 1fr)); gap:32px;">
            ${gridHTML}
        </div>
    `;
};

// 4. MAIN FEED AUTO REFRESH (15s)
// Use existing loadCategoryData logic which calls /filter_topic
if (window.feedInterval) clearInterval(window.feedInterval);
window.feedInterval = setInterval(() => {
    // Only refresh if user is at top to avoid jump, OR just let it flow since user asked for "REPLACEMENT EVERY TIME"
    // User demand > UX nicety.
    if (typeof window.loadCategoryData === 'function' && window.currentCategory) {
        console.log("⚡ Auto-refreshing Main Feed...");
        window.loadCategoryData(window.currentCategory); 
    }
}, 15000);


// 5. RESTORE MODAL (Keep it)
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
        // Live Modal shows EVERYTHING fresh
        const all = [...(data.opml||[]), ...(data.gnews||[]), ...(data.hackernews||[])];
        const fresh = all.filter(i => i.created_utc && (Date.now() - new Date(i.created_utc).getTime() < 86400000));
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
            content.innerHTML += `<button onclick="applyLiveToFeed()" style="margin-top:10px; width:100%; padding:10px; cursor:pointer;">Show All Updates</button>`;
            window.latestFreshItems = fresh; 
        } else { content.innerHTML = '<div style="text-align:center; padding:40px;">No new updates.</div>'; }
        indicator.innerText = "Live";
    } catch (e) { indicator.innerText = "Error"; }
};

// Initial calls
window.fetchWorldUpdates();
</script>
"""

content += FINAL_PATCH

with open(HTML_PATH, 'w') as f:
    f.write(content)

print("✅ FINAL: OPML Pulse (5s), Mixed Feed (15s), Grid Layout applied.")
