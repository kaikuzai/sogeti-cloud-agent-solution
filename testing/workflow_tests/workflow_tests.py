import sys
from pathlib import Path

# Ensure the project root is on sys.path when this test is run from the
# `testing` directory. This makes the top-level `tools` package importable.
sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from agent_framework.devui import serve
from agent_framework.observability import setup_observability
from workflows.fetch_resource_groups_wf import fetch_resource_groups_workflow

def main():
    # Enable observability to see workflow execution details and output
    setup_observability(enable_sensitive_data=True)
    
    # Create your workflow
    workflow = fetch_resource_groups_workflow()
    
    serve(entities=[workflow], port=8080, auto_open=False)

if __name__ == '__main__':
    main()