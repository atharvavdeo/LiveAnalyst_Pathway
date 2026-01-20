
import os

HTML_PATH = "frontend/index.html"

# Define the missing functions
MISSING_FUNCTIONS = """
<script>
// === ANTIGRAVITY FIX: MISSING MODAL FUNCTIONS ===

window.closeLiveModal = function() {
    const modal = document.getElementById('live-modal');
    if (modal) modal.style.display = 'none';
};

window.applyLiveToFeed = function() {
    if (window.latestFreshItems && window.latestFreshItems.length > 0) {
        console.log("⚡ Applying " + window.latestFreshItems.length + " live items to feed...");
        window.renderMainFeed(window.latestFreshItems);
        window.scrollTo({top: 0, behavior: 'smooth'});
        window.closeLiveModal();
        
        // Show success indicator logic if needed
        const indicator = document.getElementById("refresh-indicator");
        if (indicator) indicator.innerText = "Updated";
    } else {
        console.log("⚠️ No fresh items to apply.");
    }
};

console.log("✅ Modal Logic Repaired.");
</script>
"""

# Append to the end of the file (safest way to ensure they exist in global scope)
with open(HTML_PATH, 'a') as f:
    f.write(MISSING_FUNCTIONS)

print("✅ Injected missing closeLiveModal and applyLiveToFeed functions.")
