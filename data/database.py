import sqlite3
import time
from pathlib import Path
from typing import List, Dict, Optional

# Database Path
DB_DIR = Path(__file__).parent
DB_PATH = DB_DIR / "news_archive.db"

def init_db():
    """Initialize the SQLite database and tables."""
    if not DB_DIR.exists():
        DB_DIR.mkdir(parents=True)

    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    # Articles Table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS articles (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        source TEXT,
        title TEXT,
        content TEXT,
        url TEXT UNIQUE,
        published_date TEXT,
        created_at REAL,
        reliability TEXT
    )
    """)
    
    # Create indexes for faster search
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_source ON articles(source)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_created_at ON articles(created_at)")
    
    conn.commit()
    conn.close()
    print(f"✅ SQLite Database initialized at {DB_PATH}")

def save_article(article: Dict) -> bool:
    """
    Save a single article to the database.
    Returns True if saved (new), False if duplicate (url exists).
    """
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    try:
        cursor.execute("""
        INSERT INTO articles (source, title, content, url, published_date, created_at, reliability)
        VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (
            article.get("source", "unknown"),
            article.get("title", "") or article.get("text", "")[:100], # Fallback title
            article.get("text", ""),
            article.get("url", ""),
            str(article.get("created_utc", "")),
            time.time(),
            article.get("reliability", "Unknown")
        ))
        conn.commit()
        return True
    except sqlite3.IntegrityError:
        # Duplicate URL
        return False
    except Exception as e:
        print(f"❌ DB Save Error: {e}")
        return False
    finally:
        conn.close()

def save_articles_batch(articles: List[Dict]) -> int:
    """
    Save a batch of articles. Returns count of new items.
    """
    count = 0
    for art in articles:
        if save_article(art):
            count += 1
    return count

def search_history(query: str, limit: int = 20) -> List[Dict]:
    """
    Search historical articles using simple LIKE query.
    """
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    
    # Simple keyword search
    like_query = f"%{query}%"
    
    cursor.execute("""
        SELECT * FROM articles 
        WHERE content LIKE ? OR title LIKE ?
        ORDER BY created_at DESC 
        LIMIT ?
    """, (like_query, like_query, limit))
    
    rows = cursor.fetchall()
    conn.close()
    
    results = []
    for row in rows:
        results.append({
            "source": row["source"],
            "text": row["content"],
            "url": row["url"],
            "created_utc": row["published_date"],
            "reliability": row["reliability"],
            "is_historical": True
        })
    return results

def get_stats() -> Dict:
    """Get database statistics."""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    stats = {}
    
    # Total count
    cursor.execute("SELECT COUNT(*) FROM articles")
    stats["total_articles"] = cursor.fetchone()[0]
    
    # Count by source
    cursor.execute("SELECT source, COUNT(*) FROM articles GROUP BY source")
    source_counts = cursor.fetchall()
    for source, count in source_counts:
        stats[f"source_{source}"] = count
        
    conn.close()
    return stats

# Initialize on module load
init_db()
