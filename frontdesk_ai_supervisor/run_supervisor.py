import os
import subprocess
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from supervisor.app import app

if __name__ == '__main__':
    # run Flask app directly
    app.run(host='0.0.0.0', port=int(os.environ.get('SUPERVISOR_PORT', 5000)), debug=True)
