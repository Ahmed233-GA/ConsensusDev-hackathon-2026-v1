import os
import sys
# Add project root to sys.path so that 'qa_runner' package can be imported in tests
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), ""))
if project_root not in sys.path:
    sys.path.insert(0, project_root)
