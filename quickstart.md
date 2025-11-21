# Quick Start - Get Running in 5 Minutes

## Step 1: Download and Install

```bash
# If you cloned from GitHub:
cd dc-metrc-inbound
pip install -r requirements.txt

# If you downloaded as a ZIP:
# Extract it, then:
cd dc-metrc-inbound
pip install requests python-dotenv
```

## Step 2: Run It

```bash
python main.py
```

## Step 3: Follow the Prompts

The script will ask you:

```
Your Asana Workspaces:
  1. Haven Cannabis (ID: 123456789)
  2. Personal Workspace (ID: 987654321)

Select workspace (1-2): 
```

**→ Choose the number for your work workspace**

Then:

```
Your Projects:
  1. Operations
  2. Compliance
  3. Inventory Management
  4. Team Tasks

Select project for METRC tasks (1-4):
```

**→ Choose where you want METRC transfer tasks to appear**

## Step 4: Watch It Work!

The script will:
- ✅ Check METRC for incoming transfers
- ✅ Show you what it found
- ✅ Create Asana tasks for new transfers
- ✅ Tell you what it did

Example output:
```
============================================================
METRC → Asana Integration
============================================================

[2024-11-21 14:30:00] Checking METRC for incoming transfers...
  ✓ Found 3 incoming transfers

📦 Processing new transfer ID: 12345
  ✓ Created Asana task: Inbound Transfer: Acme Cannabis Co - Manifest #789

📦 Processing new transfer ID: 12346
  ✓ Created Asana task: Inbound Transfer: XYZ Distributors - Manifest #790

============================================================
✓ Processed 2 new transfer(s)
✓ Total tracked: 2 transfers
============================================================
```

## Step 5: Check Asana

Go to Asana and look in the project you selected. You should see new tasks!

## Step 6: Run It Again (Test for Duplicates)

```bash
python main.py
```

This time it should say:
```
✓ No new transfers found
```

Perfect! It's not creating duplicates.

## You're Done! 🎉

The script works. Now you can either:

**A) Run it manually whenever you want**
```bash
python main.py
```

**B) Set up automatic scheduling**

See SETUP.md for instructions on:
- GitHub Actions (free, runs in the cloud)
- Cron (Mac/Linux)
- Task Scheduler (Windows)

---

## Quick Troubleshooting

**"Error fetching transfers"**
- Check that your METRC API key is correct
- Make sure you have internet access

**"Error fetching workspaces"**
- Check that your Asana PAT is correct
- Make sure you have internet access

**"No transfers found"**
- This is normal if you don't have recent incoming transfers
- The script looks back 7 days by default
- Try creating a test transfer in METRC

**Need help?**
- Read the full error message - it usually tells you exactly what's wrong
- Check SETUP.md for detailed troubleshooting
- Make sure all your API credentials are correct