
import os
import re

HTML_PATH = "frontend/index.html"

# 1. CLEAN UP: Remove previous script/style patches
with open(HTML_PATH, 'r') as f:
    content = f.read()

# Pattern to remove previous "V4" and other patches
pattern_css = r'<style>\s*/\* ANTIGRAVITY GLASS THEME(.*?)<\/style>'
content = re.sub(pattern_css, '', content, flags=re.DOTALL)

pattern_script = r'<script>\s*// === ANTIGRAVITY FINAL: STRICT USER REQUIREMENTS ===[\s\S]*?</script>'
content = re.sub(pattern_script, '', content)

# 2. DEFINITIVE RESTORATION: VERGE (WHITE/BLACK/SHARP)
# User wants: Black Headlines, No Rounded Corners, No Box Space wasteland.

FINAL_RESTORE_SCRIPT = """
<script>
// === ANTIGRAVITY RESTORE: VERGE ORIGINAL THEME ===

// 1. UTC-Aware Time Ago
function calculateTimeAgo(dateString) {
    if (!dateString) return '';
    try {
        const date = new Date(dateString);
        const now = new Date();
        const diffMs = now.getTime() - date.getTime(); 
        const seconds = Math.floor(diffMs / 1000);
        if (seconds < 60) return 'JUST NOW';
        const minutes = Math.floor(seconds / 60);
        if (minutes < 60) return `${minutes}M AGO`;
        const hours = Math.floor(minutes / 60);
        return hours < 24 ? `${hours}H AGO` : `${Math.floor(hours / 24)}D AGO`;
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
                
                return `
                <div class="popular-item" onclick="window.open('${item.url}', '_blank')" style="cursor:pointer; border-bottom:1px solid #ddd; padding:15px 0;">
                    <div class="index-circle" style="background:#000; color:#fff; font-family:'Outfit'; font-weight:700;">${index + 1}</div>
                    <div class="popular-info">
                        <h4 style="color:#000; font-family:'Outfit'; font-weight:700; font-size:1.1rem; line-height:1.2; text-transform:none;">${stripHtml(item.text)}</h4>
                        <span style="color:#FF0055; font-size:0.7rem; font-weight:bold; letter-spacing:1px; margin-top:5px; display:block;">${safeSource} • <span style="color:#888;">${calculateTimeAgo(item.created_utc)}</span></span>
                    </div>
                </div>
            `;
            }).join('');
        }
    } catch (e) { console.error("Pulse Error", e); }
};

// AUTO-REFRESH GLOBAL PULSE EVERY 5 SECONDS
setInterval(window.fetchWorldUpdates, 5000);


// 3. MAIN FEED: MIXED SOURCES, MASONRY GRID, SHARP CORNERS
window.renderMainFeed = function(items) {
    const listContainer = document.getElementById("list-feed");
    const heroContainer = document.getElementById("hero-container");
    const now = Date.now();

    // 1. STRICT FRONTEND FILTER (24h Hard Limit)
    // Filter out blacklist AND old items
    items = items.filter(i => {
        if (i.text.includes("Don't let your backend write checks")) return false;
        if (!i.created_utc) return true; // Keep if no date, but maybe dangerous
        const ageMs = now - new Date(i.created_utc).getTime();
        return ageMs < (24 * 60 * 60 * 1000); // 24 HOURS
    });

    if (!items || items.length === 0) {
        if (!listContainer.innerHTML.includes("available")) {
             listContainer.innerHTML = '<p style="text-align:center; padding:40px; font-weight:bold; font-family:var(--font-head);">NO FRESH NEWS AVAILABLE</p>';
        }
        return;
    }

    const heroItem = items[0];
    const heroHasImage = heroItem.image_url && heroItem.image_url.startsWith('http');
    
    // HERO RENDER (Sharp, Bold, Black Text)
    // Using 'Outfit' for headers
    heroContainer.innerHTML = `
        <div class="hero-article" style="margin-bottom:60px; cursor:pointer;" onclick="window.open('${heroItem.url}', '_blank')">
            <div class="hero-image-wrap" style="${!heroHasImage ? 'display:none;' : ''}">
                <img src="${heroItem.image_url}" style="width:100%; height:500px; object-fit:cover; border-radius:0;" onerror="this.style.display='none'">
            </div>
            <div class="hero-content" style="padding-top:20px;">
                <div class="meta-line" style="color:#FF0055; font-weight:900; text-transform:uppercase; letter-spacing:1px; font-size:0.9rem; font-family:'Outfit'; margin-bottom:10px;">
                    ${(heroItem.source || '').split('_')[0]} <span style="color:#000;">//</span> ${calculateTimeAgo(heroItem.created_utc)}
                </div>
                <h1 style="font-size:3.5rem; font-weight:900; line-height:1.0; color:#000; font-family:'Outfit'; text-transform:uppercase; letter-spacing:-1px;">
                    ${stripHtml(heroItem.text)}
                </h1>
            </div>
        </div>
    `;

    // GRID RENDER (Sharp Cards, Black Text)
    const gridHTML = items.slice(1).map(item => {
        const hasImage = item.image_url && item.image_url.startsWith('http');
        const sourceName = (item.source || '').split('_')[0];
        const timeAgo = calculateTimeAgo(item.created_utc);
        const snippet = stripHtml(item.description || item.text || "").substring(0, 100) + '...';
        
        // VERGE STYLE CARD
        return `
        <div class="feed-card" style="border-top:4px solid #000; padding-top:15px; cursor:pointer; margin-bottom:20px;" onclick="window.open('${item.url}', '_blank')">
             <div class="card-meta" style="color:#FF0055; font-weight:800; font-size:0.7rem; text-transform:uppercase; letter-spacing:0.5px; margin-bottom:8px; font-family:'Outfit';">
                    ${sourceName} <span style="color:#888;">// ${timeAgo}</span>
            </div>
            ${hasImage ? `
            <div class="card-image" style="width:100%; aspect-ratio:16/9; margin-bottom:10px;">
                <img src="${item.image_url}" style="width:100%; height:100%; object-fit:cover; border-radius:0;" onerror="this.parentElement.style.display='none'">
            </div>
            ` : ''}
            <div class="card-content">
                <h3 style="font-family:'Outfit'; font-weight:800; font-size:1.4rem; line-height:1.1; color:#000; margin-bottom:10px; text-transform:uppercase;">
                    ${stripHtml(item.text).split(' - ')[0]}
                </h3>
                ${!hasImage ? `<p style="color:#000; font-family:'Inter'; font-size:1rem; line-height:1.5; font-weight:500;">${snippet}</p>` : ''}
            </div>
        </div>
        `;
    }).join('');

    listContainer.innerHTML = `
        <div style="display:grid; grid-template-columns: repeat(auto-fill, minmax(300px, 1fr)); gap:40px;">
            ${gridHTML}
        </div>
    `;
};

// 4. MAIN FEED AUTO REFRESH (15s)
if (window.feedInterval) clearInterval(window.feedInterval);
window.feedInterval = setInterval(() => {
    if (typeof window.loadCategoryData === 'function' && window.currentCategory) {
        console.log("⚡ Auto-refreshing Main Feed...");
        window.loadCategoryData(window.currentCategory); 
    }
}, 15000);


// 5. MODAL (Sharp, White, Black Text)
window.openLiveSection = async function() {
    const modal = document.getElementById('live-modal');
    const content = document.getElementById('live-modal-content');
    const indicator = document.getElementById("refresh-indicator");
    modal.style.display = 'flex';
    // RESET STYLES FOR MODAL (Remove Glass)
    modal.style.background = "#fff";
    modal.style.border = "4px solid #000";
    modal.style.borderRadius = "0";
    modal.style.backdropFilter = "none";
    
    // Close button
    document.querySelector('.live-modal-close').style.color = "#000";
    document.querySelector('.live-modal-title').style.color = "#000";

    content.innerHTML = '<div style="text-align:center; padding:40px; color:#000; font-weight:bold;">⚡ FETCHING LIVE UPDATES...</div>';
    try {
        indicator.innerText = "Refreshing...";
        await fetch(API_BASE + '/refresh_opml', { method: 'POST' });
        await new Promise(r => setTimeout(r, 2000));
        const res = await fetch(API_BASE + '/data');
        const data = await res.json();
        
        const all = [...(data.opml||[]), ...(data.gnews||[]), ...(data.hackernews||[])];
        const fresh = all.filter(i => i.created_utc && (Date.now() - new Date(i.created_utc).getTime() < 86400000));
        fresh.sort((a,b) => new Date(b.created_utc).getTime() - new Date(a.created_utc).getTime());
        const top5 = fresh.slice(0, 5);
        if (top5.length > 0) {
            content.innerHTML = top5.map(item => `
                <div class="live-item" onclick="window.open('${item.url}', '_blank')" style="background:#fff; border-bottom:1px solid #000; padding:15px; border-radius:0;">
                   <div class="live-item-top">
                        <span style="color:#FF0055; font-weight:bold; font-family:'Outfit'; text-transform:uppercase;">${(item.source||'').split('_')[0]}</span>
                        <span style="color:#000; font-weight:bold;">${calculateTimeAgo(item.created_utc)}</span>
                    </div>
                    <h4 style="color:#000; font-size:1.2rem; font-family:'Outfit'; font-weight:800; text-transform:uppercase;">${stripHtml(item.text)}</h4>
                </div>
            `).join('');
            content.innerHTML += `<button onclick="applyLiveToFeed()" style="margin-top:16px; width:100%; padding:16px; background:#000; color:#fff; border:none; border-radius:0; font-weight:900; font-family:'Outfit'; text-transform:uppercase; font-size:1.2rem; cursor:pointer;">SHOW UPDATES</button>`;
            window.latestFreshItems = fresh; 
        } else { content.innerHTML = '<div style="text-align:center; padding:40px; color:#000; font-weight:bold;">NO NEW UPDATES.</div>'; }
        indicator.innerText = "Live";
    } catch (e) { indicator.innerText = "Error"; }
};

window.fetchWorldUpdates();
</script>
"""

content += FINAL_RESTORE_SCRIPT

with open(HTML_PATH, 'w') as f:
    f.write(content)

print("✅ UI RESTORED TO ORIGINAL (Sharp/Black/White).")
