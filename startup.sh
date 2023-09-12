#!/bin/bash
module_name=$MODULE_TO_INSTALL
export MODULE_NAME=$module_name
# Check if the module is importable in Python
python -c "import $module_name" 2>/dev/null

# If the module is not importable, try to install it
if [ $? -ne 0 ]; then
    pip install $module_name || echo "Failed to install $module_name. It might be a built-in module or not available on PyPI."
fi

# Start the server
uvicorn module_server_v2:app --host 0.0.0.0 --port 8000
