import os

# Disable Phoenix export during tests before application modules are imported.
os.environ.setdefault("PHOENIX_ENABLED", "false")
