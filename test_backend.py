
import sys
import os

# Add backend directory to path
sys.path.append(os.path.join(os.getcwd(), 'backend'))

try:
    print("Importing live_data...")
    from backend import live_data
    
    print("Testing get_live_dashboard_data('NIFTY')...")
    data = live_data.get_live_dashboard_data("NIFTY")
    
    print("\nSUCCESS! Data received:")
    print(f"Price: {data.get('price')}")
    print(f"Change: {data.get('price_change')}")
    print(f"Sentiment: {data.get('sentiment')}")
    print("-" * 30)
    print(data)

except Exception as e:
    print(f"\nFAILURE: {e}")
    import traceback
    traceback.print_exc()
