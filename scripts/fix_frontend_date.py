
import os
import re

HTML_PATH = "frontend/index.html"

# New robust date parser
# 1. Handles strict ISO
# 2. Handles widely used RSS formats
# 3. Defaults to RAW STRING if parsing fails (Never "Just now")
# 4. Shows "Jan 16" for > 24h old

DATE_FIX_SCRIPT = """
<script>
// === ANTIGRAVITY FIX: ROBUST DATE PARSING ===

window.calculateTimeAgo = function(dateString) {
    if (!dateString) return 'Unknown Date';

    const now = new Date();
    const date = new Date(dateString);

    // If date is invalid, return the raw string (better than lying)
    if (isNaN(date.getTime())) {
        return dateString; 
    }

    const diffMs = now - date;
    const diffSec = Math.floor(diffMs / 1000);
    const diffMin = Math.floor(diffSec / 60);
    const diffHour = Math.floor(diffMin / 60);
    const diffDay = Math.floor(diffHour / 24);

    // FUTURE DATE? (Clock screw)
    if (diffMs < 0) {
        return 'Just now'; 
    }

    // < 1 Minute
    if (diffSec < 60) return 'Just now';
    
    // < 1 Hour
    if (diffMin < 60) return diffMin + 'm ago';
    
    // < 24 Hours
    if (diffHour < 24) return diffHour + 'h ago';
    
    // > 24 Hours: Show Date (e.g. "Jan 16")
    const options = { month: 'short', day: 'numeric' };
    return date.toLocaleDateString('en-US', options); 
};

console.log("✅ Fixed Date Parsing Logic Applied.");
</script>
"""

with open(HTML_PATH, 'a') as f:
    f.write(DATE_FIX_SCRIPT)

print("✅ Injected robust date parsing logic.")
