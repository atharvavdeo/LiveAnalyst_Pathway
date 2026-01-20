import re

HTML_PATH = "frontend/index.html"

# This script adds ULTRA-STRICT 1-hour freshness filter for main feed display

ULTRA_STRICT_FILTER = """
<script>
// === ULTRA-STRICT FRESHNESS FILTER ===
// Override renderMainFeed to ONLY show items < 1 hour old

const originalRenderMainFeed = window.renderMainFeed;
window.renderMainFeed = function(items) {
    const ONE_HOUR_MS = 60 * 60 * 1000;
    const now = Date.now();
    
    // Filter to only items published in the last hour
    const ultraFresh = items.filter(item => {
        if (!item.created_utc) return false;
        const itemTime = new Date(item.created_utc).getTime();
        if (isNaN(itemTime)) return false;
        const age = now - itemTime;
        return age >= 0 && age < ONE_HOUR_MS;
    });
    
    console.log(`🔥 ULTRA-STRICT FILTER: ${items.length} items -> ${ultraFresh.length} items (< 1h old)`);
    
    if (ultraFresh.length === 0) {
        console.warn("⚠️ No items found within the last hour. Showing items within 6 hours instead.");
        const SIX_HOUR_MS = 6 * 60 * 60 * 1000;
        const lessFresh = items.filter(item => {
            if (!item.created_utc) return false;
            const itemTime = new Date(item.created_utc).getTime();
            if (isNaN(itemTime)) return false;
            const age = now - itemTime;
            return age >= 0 && age < SIX_HOUR_MS;
        });
        return originalRenderMainFeed ? originalRenderMainFeed(lessFresh) : null;
    }
    
    return originalRenderMainFeed ? originalRenderMainFeed(ultraFresh) : null;
};

console.log("✅ Ultra-Strict 1-Hour Freshness Filter Applied");
</script>
"""

with open(HTML_PATH, 'a') as f:
    f.write(ULTRA_STRICT_FILTER)

print("✅ Added ultra-strict 1-hour freshness filter")
