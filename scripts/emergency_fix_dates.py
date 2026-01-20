import re

HTML_PATH = "frontend/index.html"

# Read the file
with open(HTML_PATH, 'r') as f:
    content = f.read()

# Find and REPLACE the existing calculateTimeAgo function
# This regex finds the function definition and its body
pattern = r'(window\.calculateTimeAgo\s*=\s*function\s*\([^)]*\)\s*\{[\s\S]*?\n\s*\};)'

replacement = '''window.calculateTimeAgo = function(dateString) {
    if (!dateString) return 'Unknown Date';
    
    const now = new Date();
    const date = new Date(dateString);
    
    // DEBUG: Log what we're parsing
    // console.log(`Parsing date: ${dateString} -> ${date.toString()}`);
    
    // If date is invalid, return the raw string
    if (isNaN(date.getTime())) {
        console.warn(`Invalid date: ${dateString}`);
        return dateString.substring(0, 20); // Show first 20 chars
    }
    
    const diffMs = now - date;
    const diffSec = Math.floor(diffMs / 1000);
    const diffMin = Math.floor(diffSec / 60);
    const diffHour = Math.floor(diffMin / 60);
    const diffDay = Math.floor(diffHour / 24);
    
    // FUTURE DATE? (Clock skew or bad data) - Show the actual date
    if (diffMs < -3600000) { // More than 1 hour in future
        const options = { month: 'short', day: 'numeric', year: 'numeric' };
        return date.toLocaleDateString('en-US', options);
    }
    
    // Very recent (treat small negative values as "now")
    if (diffMs < 0) return 'Just now';
    
    // < 1 Minute
    if (diffSec < 60) return 'Just now';
    
    // < 1 Hour
    if (diffMin < 60) return diffMin + 'm ago';
    
    // < 24 Hours
    if (diffHour < 24) return diffHour + 'h ago';
    
    // < 7 Days
    if (diffDay < 7) return diffDay + 'd ago';
    
    // Older: Show actual date
    const options = { month: 'short', day: 'numeric' };
    if (diffDay > 365) options.year = 'numeric';
    return date.toLocaleDateString('en-US', options);
};'''

# Check if we found the function
if re.search(pattern, content):
    content = re.sub(pattern, replacement, content, count=1)
    print("✅ Found and REPLACED existing calculateTimeAgo function")
else:
    # If not found, try to find where to insert it (after </style> tag or at script start)
    print("⚠️ Original function not found, appending new one")
    script_marker = '<script>'
    if script_marker in content:
        insert_pos = content.find(script_marker) + len(script_marker)
        content = content[:insert_pos] + '\n' + replacement + '\n' + content[insert_pos:]
    else:
        content += '\n<script>\n' + replacement + '\n</script>\n'

# Write back
with open(HTML_PATH, 'w') as f:
    f.write(content)

print("✅ Date function updated in index.html")
