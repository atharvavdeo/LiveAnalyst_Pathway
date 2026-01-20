from ingest.gnews_connector import search_historical
import time

def test_search(query):
    print(f"\n🔎 Testing Query: '{query}'")
    try:
        items = search_historical(query)
        if items:
            print(f"✅ Found {len(items)} items.")
            print(f"Sample: {items[0]['text'][:100]}...")
            return True
        else:
            print("❌ No items found.")
            return False
    except Exception as e:
        print(f"❌ Error: {e}")
        return False

if __name__ == "__main__":
    print("--- DEBUGGING GNEWS SEARCH ---")
    
    # Test 1: Broad term
    test_search("Apple")
    
    # Test 2: The problematic query
    success = test_search("India Russia")
    
    if not success:
        print("\n⚠️ 'India Russia' failed. Trying 'India AND Russia'...")
        test_search("India AND Russia")
        
    print("\n--- Done ---")
