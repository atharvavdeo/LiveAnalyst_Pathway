
import os

# Define the file path
HTML_PATH = "frontend/index.html"

# Define the new aesthetic styles and logic
CSS_PATCH = """
<style>
/* ANTIGRAVITY AESTHETIC PATCH */
.live-modal { position:fixed; top:50%; left:50%; transform:translate(-50%, -50%); width:600px; max-width:90%; background:rgba(20, 20, 20, 0.95); border:1px solid rgba(255,255,255,0.1); border-radius:16px; padding:24px; box-shadow:0 25px 50px -12px rgba(0,0,0,0.5); z-index:10000; backdrop-filter:blur(10px); display:none; flex-direction:column; gap:16px; }
.live-modal-header { display:flex; justify-content:space-between; align-items:center; border-bottom:1px solid rgba(255,255,255,0.1); padding-bottom:12px; }
.live-modal-title { font-size:1.4rem; font-weight:700; color:#fff; display:flex; align-items:center; gap:8px; }
.live-modal-close { background:none; border:none; color:#888; cursor:pointer; font-size:1.5rem; }
.live-modal-list { display:flex; flex-direction:column; gap:12px; max-height:60vh; overflow-y:auto; }
.live-item { background:rgba(255,255,255,0.03); border-radius:8px; padding:12px; cursor:pointer; transition:all 0.2s; border:1px solid transparent; }
.live-item:hover { background:rgba(255,255,255,0.06); border-color:rgba(255,255,255,0.1); }
.live-item-top { display:flex; justify-content:space-between; font-size:0.75rem; color:#888; margin-bottom:6px; }
.live-item-source { font-weight:600; color:#aaa; text-transform:uppercase; letter-spacing:0.5px; }
.live-item-time { color:#666; }
.live-item h4 { margin:0; font-size:1rem; color:#eee; font-weight:500; line-height:1.4; }
.toast-notification { position:fixed; bottom:30px; right:30px; background:#111; border:1px solid #333; color:#fff; padding:12px 20px; border-radius:8px; z-index:9999; box-shadow:0 10px 15px -3px rgba(0,0,0,0.5); display:flex; align-items:center; gap:10px; font-size:0.9rem; animation:slideUp 0.3s cubic-bezier(0.16, 1, 0.3, 1); }
@keyframes slideUp { from { transform:translateY(20px); opacity:0; } to { transform:translateY(0); opacity:1; } }
</style>
<!-- LIVE MODAL CONTAINER -->
<div id="live-modal" class="live-modal">
    <div class="live-modal-header">
        <div class="live-modal-title">⚡ Live Updates</div>
        <button class="live-modal-close" onclick="closeLiveModal()">×</button>
    </div>
    <div id="live-modal-content" class="live-modal-list"></div>
</div>
"""

JS_OVERRIDES = """
<script>
// === ANTIGRAVITY RESET: RESTORE MODAL & FIX UI ===

// 1. Cleaner Time Ago (Fixes "Just Now" bugs)
function calculateTimeAgo(dateString) {
    if (!dateString) return '';
    try {
        const date = new Date(dateString);
        const now = new Date();
        // Convert to UTC timestamps to avoid timezone mess
        const diffMs = now.getTime() - date.getTime(); 
        const seconds = Math.floor(diffMs / 1000);

        if (seconds < 0) return 'Just now'; // Future dates handle
        if (seconds < 60) return 'Just now';
        const minutes = Math.floor(seconds / 60);
        if (minutes < 60) return `${minutes}m ago`;
        const hours = Math.floor(minutes / 60);
        if (hours < 24) return `${hours}h ago`;
        return `${Math.floor(hours / 24)}d ago`;
    } catch(e) { return ''; }
}

// 2. Updated Render Feed (Removes Ugly Red Labels)
// Redefine rendering to be cleaner
const originalRenderFeed = window.renderMainFeed; 

window.renderMainFeed = function(items) {
    const heroContainer = document.getElementById("hero-container");
    const listContainer = document.getElementById("list-feed");
    
    if (!items || items.length === 0) {
        listContainer.innerHTML = '<p class="text-center text-gray-500 py-10">No live news available right now.</p>';
        return;
    }

    const heroItem = items[0];
    const heroHasImage = heroItem.image_url && heroItem.image_url.startsWith('http');
    const heroIsSaved = typeof isBookmarked === 'function' ? isBookmarked(heroItem.url) : false;
    
    // Clean Hero
    heroContainer.innerHTML = `
        <div class="hero-article" style="position:relative;" onclick="window.open('${heroItem.url}', '_blank')">
             <button class="bookmark-icon-btn ${heroIsSaved ? 'saved' : ''}" style="top:20px; right:20px; width:48px; height:48px;" onclick="event.stopPropagation(); addBookmark(JSON.parse(decodeURIComponent('${encodeURIComponent(JSON.stringify(heroItem))}')))"> 
                <svg viewBox="0 0 24 24" xmlns="http://www.w3.org/2000/svg"><path d="M17 3H7c-1.1 0-2 .9-2 2v16l7-3 7 3V5c0-1.1-.9-2-2-2z"/></svg>
            </button>
            <div class="hero-image-wrap" style="${!heroHasImage ? 'background:linear-gradient(135deg, #1e3c72 0%, #2a5298 100%); display:flex; align-items:center; justify-content:center;' : ''}">
                ${heroHasImage ? `<img src="${heroItem.image_url}" onerror="this.style.display='none'; this.parentElement.style.background='#222';">` : '<span style="font-size:3rem; opacity:0.2;">🗞️</span>'}
            </div>
            <div class="hero-content">
                <h2 style="font-family:'Inter', sans-serif; font-weight:700; letter-spacing:-0.02em;">${stripHtml(heroItem.text)}</h2>
                <div class="meta-line" style="color:#aaa; font-weight:500;">
                    ${(heroItem.source || 'Unknown').split('_')[0].toUpperCase()} • ${calculateTimeAgo(heroItem.created_utc)}
                </div>
            </div>
        </div>
    `;

    // Clean List Items (No Red/Blue Labels!)
    listContainer.innerHTML = items.slice(1).map(item => {
        const isSaved = typeof isBookmarked === 'function' ? isBookmarked(item.url) : false;
        let snippet = stripHtml(item.description || item.text || "");
        if (snippet.length > 140) snippet = snippet.substring(0, 140) + '...';
        const sourceName = (item.source || 'Unknown').split('_')[0];

        return `
        <div class="feed-item" style="padding:20px; border-bottom:1px solid rgba(255,255,255,0.05);" onclick="window.open('${item.url}', '_blank')">
            <button class="bookmark-icon-btn ${isSaved ? 'saved' : ''}" style="top:15px; right:15px;" onclick="event.stopPropagation(); addBookmark(JSON.parse(decodeURIComponent('${encodeURIComponent(JSON.stringify(item))}')))">
                <svg viewBox="0 0 24 24"><path d="M17 3H7c-1.1 0-2 .9-2 2v16l7-3 7 3V5c0-1.1-.9-2-2-2z"/></svg>
            </button>
            <div class="feed-info" style="width:100%;">
                <div style="margin-bottom:6px; font-size:0.75rem; color:#666; text-transform:uppercase; font-weight:600; letter-spacing:0.5px; display:flex; align-items:center; gap:8px;">
                    <span style="color:#888;">${sourceName}</span>
                    <span style="width:3px; height:3px; background:#444; border-radius:50%;"></span>
                    <span style="color:#666;">${calculateTimeAgo(item.created_utc)}</span>
                </div>
                <h3 style="margin-bottom:8px; font-size:1.1rem; font-weight:600; line-height:1.4; color:#e0e0e0;">${stripHtml(item.text).split(' - ')[0]}</h3>
                <p style="color:#777; font-size:0.9rem; line-height:1.5; margin:0;">${snippet}</p>
            </div>
        </div>
        `;
    }).join('');
};

// 3. RESTORE THE MODAL FOR "FETCH LIVE"
window.openLiveSection = async function() {
    const modal = document.getElementById('live-modal');
    const content = document.getElementById('live-modal-content');
    const indicator = document.getElementById("refresh-indicator");
    
    // Show Loading State in Modal
    modal.style.display = 'flex';
    content.innerHTML = '<div style="text-align:center; padding:40px; color:#888;">⚡ Fetching fresh updates from 1800+ sources...</div>';
    
    try {
        indicator.innerText = "Refreshing...";
        
        // A. Trigger Backend Refresh
        await fetch(API_BASE + '/refresh_opml', { method: 'POST' });
        
        // B. Wait briefly allowing backend to process
        await new Promise(r => setTimeout(r, 2000));
        
        // C. Fetch Data
        const res = await fetch(API_BASE + '/data');
        const data = await res.json();
        
        // D. Combine & Sort
        const all = [...(data.opml||[]), ...(data.gnews||[]), ...(data.hackernews||[])];
        const now = Date.now();
        
        // Filter: Strict 24h freshness for "Live" modal
        const fresh = all.filter(i => {
           if (!i.created_utc) return false; 
           const d = new Date(i.created_utc).getTime();
           return (now - d) < (24 * 60 * 60 * 1000);
        });
        
        // Sort: Newest First
        fresh.sort((a,b) => new Date(b.created_utc).getTime() - new Date(a.created_utc).getTime());
        
        // Take Top 5
        const top5 = fresh.slice(0, 5);
        
        // Render Modal Content
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
            
            // Allow user to apply these to main feed
            content.innerHTML += `
                <button onclick="applyLiveToFeed()" style="margin-top:16px; width:100%; padding:12px; background:#fff; color:#000; border:none; border-radius:8px; font-weight:600; cursor:pointer;">
                    See All ${fresh.length} Updates in Feed
                </button>
            `;
            
            // Store for "See All" action
            window.latestFreshItems = fresh; 
            
        } else {
            content.innerHTML = '<div style="text-align:center; padding:40px;">No brand new updates found in the last 24h.</div>';
        }
        
        indicator.innerText = "Live";
        
    } catch (e) {
        console.error(e);
        content.innerHTML = '<div style="text-align:center; padding:20px; color:#f55;">Connection Error. Try again.</div>';
        indicator.innerText = "Error";
    }
};

window.closeLiveModal = function() {
    document.getElementById('live-modal').style.display = 'none';
};

window.applyLiveToFeed = function() {
    if (window.latestFreshItems) {
        window.renderMainFeed(window.latestFreshItems);
        closeLiveModal();
        window.scrollTo({top:0, behavior:'smooth'});
    }
};

// Attach Logic
// (We append this script at the end of body to ensure overrides work)
</script>
"""

# Read existing HTML
with open(HTML_PATH, 'r') as f:
    content = f.read()

# Inject CSS before </head>
if "<!-- ANTIGRAVITY AESTHETIC PATCH -->" not in content:
    content = content.replace('</head>', CSS_PATCH + '</head>')

# Append JS at the end
content += JS_OVERRIDES

# Write back
with open(HTML_PATH, 'w') as f:
    f.write(content)

print("✅ UI patched successfully.")
