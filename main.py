#!/usr/bin/env python3
"""
METRC → Asana Integration
Monitors METRC for incoming transfers and creates Asana tasks
"""
import requests
import json
import os
from datetime import datetime, timedelta
from pathlib import Path

# Configuration - reads from environment variables if available, otherwise uses defaults
# METRC requires TWO API keys for authentication:
METRC_INTEGRATOR_KEY = os.getenv("METRC_INTEGRATOR_KEY", "10JqOc5bwSAdXvpn32XO5BqRujPkL1JGkp-u8lq-SpMRHsDm")  # Vendor/Integrator API Key
METRC_USER_KEY = os.getenv("METRC_USER_KEY", "r94vrDWi2CVsT2qYERqGHHc2oMjb5rC5XsgvunC8tE7fUADa")  # User API Key
METRC_LICENSE = os.getenv("METRC_LICENSE", "C11-0001638-LIC")
METRC_BASE_URL = "https://api-ca.metrc.com"

ASANA_PAT = os.getenv("ASANA_PAT", "2/1203280086662339/1212049949445851:025846d455d7cbe4b2af4bb70930e902")
ASANA_WORKSPACE_ID = os.getenv("ASANA_WORKSPACE_ID", "1168175464405652")
ASANA_PROJECT_ID = os.getenv("ASANA_PROJECT_ID", "1207340952387632")

# File to track processed transfers
TRACKING_FILE = "processed_transfers.json"


def load_processed_transfers():
    """Load the list of transfer IDs we've already processed"""
    if os.path.exists(TRACKING_FILE):
        with open(TRACKING_FILE, 'r') as f:
            return json.load(f)
    return {"transfer_ids": []}


def save_processed_transfers(data):
    """Save the list of processed transfer IDs"""
    with open(TRACKING_FILE, 'w') as f:
        json.dump(data, f, indent=2)


def get_incoming_transfers(hours_back=2):
    """Fetch incoming transfers from METRC (max 24 hours per METRC limitation)"""
    print(f"\n[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] Checking METRC for incoming transfers...")
    
    end_date = datetime.now()
    start_date = end_date - timedelta(hours=hours_back)
    
    # Use v2 endpoint (California has v2 per documentation)
    url = f"{METRC_BASE_URL}/transfers/v2/incoming"
    headers = {
        "Content-Type": "application/json"
    }
    # METRC requires Basic Auth with Integrator Key as username and User Key as password
    auth = (METRC_INTEGRATOR_KEY, METRC_USER_KEY)
    params = {
        "licenseNumber": METRC_LICENSE,
        "lastModifiedStart": start_date.strftime("%Y-%m-%dT%H:%M:%S"),
        "lastModifiedEnd": end_date.strftime("%Y-%m-%dT%H:%M:%S")
    }
    
    # Debug logging
    print(f"  URL: {url}")
    print(f"  License: {METRC_LICENSE}")
    print(f"  Date Range: {params['lastModifiedStart']} to {params['lastModifiedEnd']}")
    print(f"  Full URL with params: {url}?licenseNumber={METRC_LICENSE}&lastModifiedStart={params['lastModifiedStart']}&lastModifiedEnd={params['lastModifiedEnd']}")
    
    try:
        response = requests.get(url, headers=headers, auth=auth, params=params, timeout=30)
        
        print(f"  Response Status: {response.status_code}")
        print(f"  Response Headers: {dict(response.headers)}")
        
        if response.status_code != 200:
            print(f"  Response Body: {response.text}")
        
        response.raise_for_status()
        response_data = response.json()
        
        # METRC v2 returns paginated response with Data field
        if isinstance(response_data, dict) and 'Data' in response_data:
            transfers = response_data['Data']
            total_records = response_data.get('TotalRecords', len(transfers))
            print(f"  ✓ Found {len(transfers)} incoming transfers (Total: {total_records})")
        else:
            # Fallback for non-paginated response
            transfers = response_data if isinstance(response_data, list) else []
            print(f"  ✓ Found {len(transfers)} incoming transfers")
        
        return transfers
    except requests.exceptions.RequestException as e:
        print(f"  ✗ Error fetching transfers: {e}")
        if hasattr(e, 'response') and e.response is not None:
            print(f"  Response status: {e.response.status_code}")
            print(f"  Response body: {e.response.text}")
        return []


def format_transfer_for_asana(transfer):
    """Format transfer data into Asana task name and description"""
    
    # Extract key info
    transfer_id = transfer.get('Id', 'Unknown')
    manifest_number = transfer.get('ManifestNumber', 'Unknown')
    shipper_name = transfer.get('ShipperFacilityName', 'Unknown Shipper')
    created_date = transfer.get('CreatedDateTime', '')
    est_arrival = transfer.get('EstimatedArrivalDateTime', 'Not specified')
    
    # Parse dates
    if created_date:
        try:
            created_dt = datetime.fromisoformat(created_date.replace('Z', '+00:00'))
            created_str = created_dt.strftime('%Y-%m-%d %I:%M %p')
        except:
            created_str = created_date
    else:
        created_str = 'Unknown'
    
    if est_arrival and est_arrival != 'Not specified':
        try:
            arrival_dt = datetime.fromisoformat(est_arrival.replace('Z', '+00:00'))
            arrival_str = arrival_dt.strftime('%Y-%m-%d %I:%M %p')
        except:
            arrival_str = est_arrival
    else:
        arrival_str = 'Not specified'
    
    # Count deliveries and packages
    deliveries = transfer.get('Deliveries', [])
    num_deliveries = len(deliveries)
    
    total_packages = 0
    for delivery in deliveries:
        total_packages += len(delivery.get('Packages', []))
    
    # Create task name
    task_name = f"Inbound Transfer: {shipper_name} - Manifest #{manifest_number}"
    
    # Create detailed description
    description = f"""**New Inbound Transfer from METRC**

**Shipper:** {shipper_name}
**Manifest Number:** {manifest_number}
**Transfer ID:** {transfer_id}

**Timing:**
• Created: {created_str}
• Estimated Arrival: {arrival_str}

**Contents:**
• {num_deliveries} delivery/deliveries
• {total_packages} total packages

**Next Steps:**
1. Review transfer in METRC
2. Verify contents match manifest
3. Accept/reject transfer in METRC
4. Update inventory in Blaze/Distru

---
_Auto-created by METRC Integration on {datetime.now().strftime('%Y-%m-%d %I:%M %p')}_
"""
    
    return task_name, description


def create_asana_task(task_name, description, workspace_id, project_id):
    """Create a task in Asana"""
    
    url = "https://app.asana.com/api/1.0/tasks"
    headers = {
        "Authorization": f"Bearer {ASANA_PAT}",
        "Content-Type": "application/json"
    }
    
    task_data = {
        "data": {
            "workspace": workspace_id,
            "projects": [project_id],
            "name": task_name,
            "notes": description,
            "completed": False
        }
    }
    
    try:
        response = requests.post(url, headers=headers, json=task_data, timeout=30)
        response.raise_for_status()
        task = response.json()['data']
        print(f"  ✓ Created Asana task: {task_name}")
        return task
    except requests.exceptions.RequestException as e:
        print(f"  ✗ Error creating task: {e}")
        return None


def get_asana_workspaces():
    """Get user's Asana workspaces"""
    url = "https://app.asana.com/api/1.0/users/me"
    headers = {
        "Authorization": f"Bearer {ASANA_PAT}",
        "Content-Type": "application/json"
    }
    
    try:
        response = requests.get(url, headers=headers, timeout=30)
        response.raise_for_status()
        user_data = response.json()
        return user_data['data']['workspaces']
    except requests.exceptions.RequestException as e:
        print(f"Error fetching workspaces: {e}")
        return []


def get_asana_projects(workspace_id):
    """Get projects in a workspace"""
    url = "https://app.asana.com/api/1.0/projects"
    headers = {
        "Authorization": f"Bearer {ASANA_PAT}",
        "Content-Type": "application/json"
    }
    params = {
        "workspace": workspace_id,
        "limit": 50
    }
    
    try:
        response = requests.get(url, headers=headers, params=params, timeout=30)
        response.raise_for_status()
        return response.json()['data']
    except requests.exceptions.RequestException as e:
        print(f"Error fetching projects: {e}")
        return []


def setup_asana_config():
    """Interactive setup to choose workspace and project"""
    print("\n=== Asana Configuration Setup ===\n")
    
    # Get workspaces
    workspaces = get_asana_workspaces()
    if not workspaces:
        print("Error: Could not fetch workspaces. Check your Asana PAT.")
        return None, None
    
    print("Your Asana Workspaces:")
    for i, ws in enumerate(workspaces, 1):
        print(f"  {i}. {ws['name']} (ID: {ws['gid']})")
    
    # Choose workspace
    while True:
        try:
            choice = int(input(f"\nSelect workspace (1-{len(workspaces)}): "))
            if 1 <= choice <= len(workspaces):
                workspace_id = workspaces[choice - 1]['gid']
                workspace_name = workspaces[choice - 1]['name']
                break
        except (ValueError, KeyboardInterrupt):
            print("Invalid choice. Try again.")
    
    print(f"\nSelected workspace: {workspace_name}")
    
    # Get projects
    print("\nFetching projects...")
    projects = get_asana_projects(workspace_id)
    if not projects:
        print("Error: Could not fetch projects.")
        return workspace_id, None
    
    print("\nYour Projects:")
    for i, proj in enumerate(projects, 1):
        print(f"  {i}. {proj['name']} (ID: {proj['gid']})")
    
    # Choose project
    while True:
        try:
            choice = int(input(f"\nSelect project for METRC tasks (1-{len(projects)}): "))
            if 1 <= choice <= len(projects):
                project_id = projects[choice - 1]['gid']
                project_name = projects[choice - 1]['name']
                break
        except (ValueError, KeyboardInterrupt):
            print("Invalid choice. Try again.")
    
    print(f"\nSelected project: {project_name}")
    
    # Save to config
    print("\nSaving configuration...")
    return workspace_id, project_id


def main():
    """Main execution function"""
    global ASANA_WORKSPACE_ID, ASANA_PROJECT_ID
    
    print("="*60)
    print("METRC → Asana Integration")
    print("="*60)
    
    # Check if Asana is configured
    if not ASANA_WORKSPACE_ID or not ASANA_PROJECT_ID:
        print("\n⚠ Asana not configured. Running setup...")
        ASANA_WORKSPACE_ID, ASANA_PROJECT_ID = setup_asana_config()
        
        if not ASANA_WORKSPACE_ID or not ASANA_PROJECT_ID:
            print("\n✗ Setup failed. Exiting.")
            return
        
        print(f"\n✓ Configuration complete!")
        print(f"  Workspace ID: {ASANA_WORKSPACE_ID}")
        print(f"  Project ID: {ASANA_PROJECT_ID}")
        print("\nNOTE: Edit the script and update these values at the top to skip setup next time:")
        print(f'  ASANA_WORKSPACE_ID = os.getenv("ASANA_WORKSPACE_ID", "{ASANA_WORKSPACE_ID}")')
        print(f'  ASANA_PROJECT_ID = os.getenv("ASANA_PROJECT_ID", "{ASANA_PROJECT_ID}")')
    else:
        print(f"\n✓ Asana configured")
        print(f"  Workspace ID: {ASANA_WORKSPACE_ID}")
        print(f"  Project ID: {ASANA_PROJECT_ID}")
    
    # Load tracking data
    tracking_data = load_processed_transfers()
    processed_ids = set(tracking_data['transfer_ids'])
    
    print(f"\n📊 Currently tracking {len(processed_ids)} processed transfers")
    
    # Get incoming transfers (last 2 hours - METRC's 24-hour limit)
    transfers = get_incoming_transfers(hours_back=2)
    
    if not transfers:
        print("\n✓ No new transfers found")
        return
    
    # Process each transfer
    new_count = 0
    for transfer in transfers:
        transfer_id = transfer.get('Id')
        
        if not transfer_id:
            continue
        
        # Skip if already processed
        if transfer_id in processed_ids:
            continue
        
        print(f"\n📦 Processing new transfer ID: {transfer_id}")
        
        # Format and create task
        task_name, description = format_transfer_for_asana(transfer)
        task = create_asana_task(task_name, description, ASANA_WORKSPACE_ID, ASANA_PROJECT_ID)
        
        if task:
            # Mark as processed
            processed_ids.add(transfer_id)
            new_count += 1
    
    # Save updated tracking data
    tracking_data['transfer_ids'] = list(processed_ids)
    tracking_data['last_run'] = datetime.now().isoformat()
    save_processed_transfers(tracking_data)
    
    print(f"\n{'='*60}")
    print(f"✓ Processed {new_count} new transfer(s)")
    print(f"✓ Total tracked: {len(processed_ids)} transfers")
    print(f"{'='*60}\n")


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\nInterrupted by user. Exiting.")
    except Exception as e:
        print(f"\n✗ Unexpected error: {e}")
        raise