# Configuration for League Match Recorder

import os

# N8N Webhook URL for match data.
# Set this via an environment variable instead of hardcoding it here, e.g.:
#   export N8N_WEBHOOK_URL="http://your-n8n-host/webhook/your-id"
N8N_WEBHOOK_URL = os.environ.get("N8N_WEBHOOK_URL")
