# METRC → Asana Integration

Automatically creates Asana tasks when new transfers are inbound to your METRC facility.

## Setup

### 1. Install Dependencies

```bash
pip install -r requirements.txt
```

### 2. Get Your Credentials

#### METRC
- You already have your User API Key: `r94vrDWi2CVsT2qYERqGHHc2oMjb5rC5XsgvunC8tE7fUADa`
- Get your facility license number from METRC

#### Asana
- Generate a Personal Access Token (PAT):
  1. Go to https://app.asana.com/0/my-apps
  2. Click "Create new token"
  3. Give it a name like "METRC Integration"
  4. Copy the token (starts with `1/...`)

### 3. Test API Connections

First, let's make sure we can connect to both APIs:

```bash
python test_apis.py
```

This will:
- Test your METRC connection and show recent incoming transfers
- Test your Asana connection and show your workspaces/projects
- Create a test task in Asana

### 4. Configure and Run

Once testing is successful, we'll create the main integration script that:
- Polls METRC every X minutes for new incoming transfers
- Tracks which transfers we've already processed
- Creates formatted Asana tasks with transfer details

## Project Structure

```
dc-metrc-inbound/
├── test_apis.py              # Test API connections
├── main.py                   # Main integration script (to be created)
├── requirements.txt          # Python dependencies
├── config.example.json       # Example config (for reference)
├── .gitignore               # Keeps credentials out of git
└── README.md                # This file
```

## Next Steps

1. Get your Asana Personal Access Token
2. Get your METRC license number
3. Run the test script to verify everything works
4. Build the main integration script