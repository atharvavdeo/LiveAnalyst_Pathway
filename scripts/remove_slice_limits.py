#!/usr/bin/env python3
"""
Fix: Remove .slice() limits from frontend to show ALL articles
"""
import re

HTML_PATH = "frontend/index.html"

with open(HTML_PATH, 'r') as f:
    content = f.read()

# Find and replace the slice limits
# Pattern 1: freshOpml.slice(0, 10)
content = re.sub(
    r'\.\.\.freshOpml\.slice\(0,\s*\d+\)',
    '...freshOpml',
    content
)

# Pattern 2: gnewsItems.slice(0, 5)
content = re.sub(
    r'\.\.\.gnewsItems\.slice\(0,\s*\d+\)',
    '...gnewsItems',
    content
)

# Pattern 3: newsapiItems.slice(0, 5)
content = re.sub(
    r'\.\.\.newsapiItems\.slice\(0,\s*\d+\)',
    '...newsapiItems',
    content
)

# Pattern 4: hnItems.slice(0, 3)
content = re.sub(
    r'\.\.\.hnItems\.slice\(0,\s*\d+\)',
    '...hnItems',
    content
)

# Pattern 5: otherItems.slice(0, 2)
content = re.sub(
    r'\.\.\.otherItems\.slice\(0,\s*\d+\)',
    '...otherItems',
    content
)

with open(HTML_PATH, 'w') as f:
    f.write(content)

print("✅ Removed all .slice() limits - frontend will now show ALL available articles")
