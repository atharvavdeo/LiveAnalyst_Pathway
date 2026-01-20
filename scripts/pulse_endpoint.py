# Add this after the /data endpoint in app_pathway.py

@app.get("/pulse")
async def get_global_pulse():
    """Return top 5 freshest articles from DB for Global Pulse"""
    try:
        from datetime import datetime, timedelta, timezone
        
        # Query DB for articles from last 30 minutes
        thirty_min_ago = datetime.now(timezone.utc) - timedelta(minutes=30)
        
       cursor = db_conn.cursor()
        cursor.execute("""
            SELECT source, text, url, created_utc, feed_title
            FROM news_items
            WHERE created_utc > ?
            AND datetime(created_utc) <= datetime('now')
            ORDER BY created_utc DESC
            LIMIT 5
        """, (thirty_min_ago.isoformat(),))
        
        rows = cursor.fetchall()
        
        pulse_items = []
        for row in rows:
            pulse_items.append({
                "source": row[0],
                "text": row[1],
                "url": row[2],
                "created_utc": row[3],
                "feed_title": row[4] if row[4] else row[0]
            })
        
        print(f"✅ /pulse: Returning {len(pulse_items)} fresh articles")
        return {"pulse": pulse_items}
    except Exception as e:
        print(f"❌ Pulse endpoint error: {e}")
        return {"pulse": []}
