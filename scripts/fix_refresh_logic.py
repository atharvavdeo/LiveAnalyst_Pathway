
import os

HTML_PATH = "frontend/index.html"

# Patch Logic:
# 1. Update Global Pulse Interval to 20s
# 2. Update 'Fetch Live' (openLiveSection) to TRIGGER MAIN FEED UPDATE immediately after burst.
# 3. Ensure Main Feed refresh interval is reasonable (15s).

PATCH_SCRIPT = """
<script>
// === ANTIGRAVITY REFRESH LOGIC V2 ===
// Enforcing strict 20s Pulse and Unified Feed Refresh

// 1. GLOBAL PULSE (20s Strict)
if (window.worldInterval) clearInterval(window.worldInterval);
window.worldInterval = setInterval(() => {
    console.log("🌍 Updating Global Pulse (20s)...");
    window.fetchWorldUpdates(); 
}, 20000);

// 2. MAIN FEED AUTO-REFRESH (15s)
if (window.feedInterval) clearInterval(window.feedInterval);
window.feedInterval = setInterval(() => {
    if (typeof window.loadCategoryData === 'function' && window.currentCategory) {
        console.log("⚡ Auto-refreshing Main Feed...");
        window.loadCategoryData(window.currentCategory); 
    }
}, 15000);

// 3. ENHANCED FETCH LIVE (Burst + Main Feed Reload)
const originalOpenLive = window.openLiveSection;
window.openLiveSection = async function() {
    // A. Call the original modal logic (Burst + Polling)
    if (originalOpenLive) originalOpenLive();

    const indicator = document.getElementById("refresh-indicator");
    if (indicator) indicator.innerText = "Refreshing...";

    // B. Wait 2 seconds for Burst Mode to ingest new OPML data
    setTimeout(async () => {
        console.log("🔥 Fetch Live: Triggering Main Feed Update...");
        
        // C. Force reload of the main feed with the new data
        if (window.currentCategory) {
            await window.loadCategoryData(window.currentCategory);
        }
        
        // D. Also refresh Global Pulse
        await window.fetchWorldUpdates();
        
        if (indicator) indicator.innerText = "Live";
        
        // E. Notify User
        const toast = document.createElement("div");
        toast.className = "toast-notification";
        toast.innerText = "🚀 FEEDS REFRESHED WITH LIVE DATA";
        toast.style.cssText = "position:fixed; bottom:20px; right:20px; background:#00FF00; color:#000; padding:15px; font-weight:900; z-index:9999;";
        document.body.appendChild(toast);
        setTimeout(() => toast.remove(), 4000);
        
    }, 2500); // 2.5s delay to allow Burst Mode to yield items
};

console.log("✅ Unified Refresh Logic Applied (Pulse: 20s, Live: Burst+Reload)");
</script>
"""

with open(HTML_PATH, 'a') as f:
    f.write(PATCH_SCRIPT)

print("✅ Applied unified refresh logic to index.html")
