#!/usr/bin/env python3
"""
DEBUG VERSION - Check last 24 hours instead of 2 hours
Use this to troubleshoot and see all recent transfers
"""

import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Import from main.py
from main import *

if __name__ == "__main__":
    print("="*70)
    print("DEBUG MODE - Checking Last 24 Hours")
    print("="*70)
    print()
    print("⚠️  This will check the last 24 hours (instead of 2) to help debug")
    print("⚠️  It will NOT create Asana tasks - just show what would happen")
    print()
    
    # Load tracking data
    tracking_data = load_processed_transfers()
    processed_ids = set(tracking_data['transfer_ids'])
    
    print(f"📊 Currently tracking {len(processed_ids)} processed transfers")
    if processed_ids:
        print(f"   IDs: {list(processed_ids)[:5]}..." if len(processed_ids) > 5 else f"   IDs: {list(processed_ids)}")
    
    # Get incoming transfers (last 24 hours for debugging)
    print("\n" + "="*70)
    transfers = get_incoming_transfers(hours_back=24)
    print("="*70)
    
    if not transfers:
        print("\n❌ No transfers found in last 24 hours")
        print("\nPossible reasons:")
        print("  1. No incoming transfers in the last 24 hours")
        print("  2. Transfers haven't been 'modified' in the last 24 hours")
        print("  3. API filters are excluding them")
        print("\nTry checking METRC directly to see when transfers were last modified.")
        sys.exit(0)
    
    print(f"\n✅ Found {len(transfers)} transfer(s) in last 24 hours")
    print("\n" + "="*70)
    print("TRANSFER DETAILS:")
    print("="*70)
    
    new_count = 0
    already_processed_count = 0
    
    for i, transfer in enumerate(transfers, 1):
        transfer_id = transfer.get('Id', 'NO_ID')
        manifest = transfer.get('ManifestNumber', 'NO_MANIFEST')
        shipper = transfer.get('ShipperFacilityName', 'UNKNOWN')
        created = transfer.get('CreatedDateTime', 'UNKNOWN')
        modified = transfer.get('LastModified', 'UNKNOWN')
        
        print(f"\n#{i} Transfer ID: {transfer_id}")
        print(f"   Manifest: {manifest}")
        print(f"   Shipper: {shipper}")
        print(f"   Created: {created}")
        print(f"   Last Modified: {modified}")
        
        if transfer_id in processed_ids:
            print(f"   Status: ⏭️  ALREADY PROCESSED (would skip)")
            already_processed_count += 1
        else:
            print(f"   Status: ✅ NEW (would create Asana task)")
            new_count += 1
            
            # Show what the Asana task would look like
            task_name, description = format_transfer_for_asana(transfer)
            print(f"\n   📋 Would create Asana task:")
            print(f"      Title: {task_name}")
            print(f"      Description preview: {description[:150]}...")
    
    print("\n" + "="*70)
    print("SUMMARY:")
    print("="*70)
    print(f"Total transfers found: {len(transfers)}")
    print(f"New transfers (would create tasks): {new_count}")
    print(f"Already processed (would skip): {already_processed_count}")
    print()
    
    if new_count > 0:
        print("✅ Good news! There are new transfers that should create Asana tasks.")
        print("\nNext steps:")
        print("  1. Check GitHub Actions logs to see if these are being found")
        print("  2. If not found, the 2-hour window might be too short")
        print("  3. Consider temporarily increasing hours_back in main.py")
    else:
        print("⏭️  All transfers have already been processed.")
        print("\nNext steps:")
        print("  1. Wait for NEW incoming transfers to arrive")
        print("  2. Or delete processed_transfers.json to reprocess old ones")
        print("  3. Then run 'python main.py' to create tasks")
    
    print("\n" + "="*70)
    print("DEBUG COMPLETE - No Asana tasks were created")
    print("="*70)