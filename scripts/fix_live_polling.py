
import os
import re

HTML_PATH = "frontend/index.html"

# 1. CLEAN UP: Remove previous missing functions patch if it exists to avoid duplicates
with open(HTML_PATH, 'r') as f:
    content = f.read()

pattern = r'<script>\s*// === ANTIGRAVITY FIX: MISSING MODAL FUNCTIONS ===[\s\S]*?</script>'
content = re.sub(pattern, '', content)

# 2. INJECT ROBUST POLLING MODAL LOGIC
# This replaces openLiveSection completely with a version that:
# 1. Clears interval on close
# 2. Polls every 2s while open
# 3. Updates the list DOM in real-time

POLLING_LOGIC = """
<script>
// === ANTIGRAVITY REAL-TIME POLLING V1 ===

window.livePollInterval = null;

window.closeLiveModal = function() {
    const modal = document.getElementById('live-modal');
    if (modal) modal.style.display = 'none';
    if (window.livePollInterval) {
        clearInterval(window.livePollInterval);
        window.livePollInterval = null;
        console.log("🛑 Live Polling Stopped.");
    }
};

window.applyLiveToFeed = function() {
    if (window.latestFreshItems && window.latestFreshItems.length > 0) {
        // Apply directly to main feed
        window.renderMainFeed(window.latestFreshItems);
        window.scrollTo({top: 0, behavior: 'smooth'});
        window.closeLiveModal();
    }
};

window.updateLiveModalContent = async function() {
    const content = document.getElementById('live-modal-content');
    if (!content) return;
    
    try {
        // Fetch fresh data (Burst mode is running in background)
        const res = await fetch(API_BASE + '/data');
        const data = await res.json();
        
        const all = [...(data.opml||[]), ...(data.gnews||[]), ...(data.hackernews||[])];
        // Strict real-time filter (Only last 24h)
        const fresh = all.filter(i => i.created_utc && (Date.now() - new Date(i.created_utc).getTime() < 86400000));
        fresh.sort((a,b) => new Date(b.created_utc).getTime() - new Date(a.created_utc).getTime());
        
        // Store for "Show Updates"
        window.latestFreshItems = fresh; 
        
        const top10 = fresh.slice(0, 10); // Show more items in modal
        
        if (top10.length > 0) {
            content.innerHTML = top10.map(item => `
                <div class="live-item" onclick="window.open('${item.url}', '_blank')" style="background:#fff; border-bottom:1px solid #000; padding:15px; border-radius:0; animation: fadeIn 0.5s;">
                   <div class="live-item-top">
                        <span style="color:#FF0055; font-weight:bold; font-family:'Outfit'; text-transform:uppercase;">${(item.source||'').split('_')[0]}</span>
                        <span style="color:#000; font-weight:bold;">${calculateTimeAgo(item.created_utc)}</span>
                    </div>
                    <h4 style="color:#000; font-size:1.1rem; font-family:'Outfit'; font-weight:800; text-transform:uppercase;">${stripHtml(item.text)}</h4>
                </div>
            `).join('');
            
            content.innerHTML += `
                <button onclick="applyLiveToFeed()" style="margin-top:16px; width:100%; padding:16px; background:#000; color:#fff; border:none; border-radius:0; font-weight:900; font-family:'Outfit'; text-transform:uppercase; font-size:1.2rem; cursor:pointer;">
                    SHOW ${fresh.length} UPDATES
                </button>
            `;
        } else {
             content.innerHTML = '<div style="text-align:center; padding:40px; color:#000; font-weight:bold;">SCANNING STREAMS...</div>';
        }
    } catch(e) { console.error("Poll Error", e); }
};

window.openLiveSection = async function() {
    const modal = document.getElementById('live-modal');
    const content = document.getElementById('live-modal-content');
    
    // Style reset (High Contrast)
    modal.style.display = 'flex';
    modal.style.background = "#fff";
    modal.style.border = "4px solid #000";
    modal.style.borderRadius = "0";
    modal.style.backdropFilter = "none";
    document.querySelector('.live-modal-close').style.color = "#000";
    document.querySelector('.live-modal-title').style.color = "#000";

    content.innerHTML = '<div style="text-align:center; padding:40px; color:#000; font-weight:bold;">⚡ STARTING BURST REFRESH...</div>';
    
    // 1. Trigger Burst
    try { await fetch(API_BASE + '/refresh_opml', { method: 'POST' }); } catch(e) {}
    
    // 2. Start Polling Loop (Every 1.5s)
    if (window.livePollInterval) clearInterval(window.livePollInterval);
    
    console.log("⚡ Live Polling Started.");
    window.updateLiveModalContent(); // Immediate call
    window.livePollInterval = setInterval(window.updateLiveModalContent, 1500);
};

// CSS Animation for new items
const style = document.createElement('style');
style.innerHTML = `
@keyframes fadeIn {
  from { opacity: 0; transform: translateY(10px); }
  to { opacity: 1; transform: translateY(0); }
}
`;
document.head.appendChild(style);

</script>
"""

content += POLLING_LOGIC

with open(HTML_PATH, 'w') as f:
    f.write(content)

print("✅ Live Polling Logic Injected.")
