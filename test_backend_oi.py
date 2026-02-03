
import sys
import os
import json

# Add backend directory to path
sys.path.append(os.path.join(os.getcwd(), 'backend'))

try:
    print("Importing data_provider...")
    from backend.data_provider import data_provider
    from backend.models import OIDetails
    
    print("Testing get_oi_details('NIFTY')...")
    data = data_provider.get_oi_details("NIFTY")
    
    print("\nSUCCESS! Data received:")
    # print(json.dumps(data, indent=2)) 
    print(data)

    # Validate keys manually to simulate Pydantic
    required_keys = ["status", "symbol", "atm_strike", "strikes"]
    for key in required_keys:
        if key not in data:
            print(f"ERROR: Missing key '{key}'")
            
    if "strikes" in data:
        print(f"First strike sample: {data['strikes'][0]}")
        # Check Enum
        color = data['strikes'][0].get('ce_bar_color')
        if color not in ["GREEN", "RED", "GREY"]:
             print(f"ERROR: Invalid color '{color}'")

except Exception as e:
    print(f"\nFAILURE: {e}")
    import traceback
    traceback.print_exc()
