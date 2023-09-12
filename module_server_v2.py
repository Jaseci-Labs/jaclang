"""Server module for handling module operations in a FastAPI application."""

# Standard library imports
import importlib
import logging
import os
import pickle
import subprocess
import sys
import warnings

# Third-party imports
from fastapi import FastAPI, HTTPException, Request, Response

from pydantic import BaseModel

import uvicorn

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger(__name__)
app = FastAPI()


class AttributeValue(BaseModel):
    """Model for attribute value."""

    value: str


class FunctionExecution(BaseModel):
    """Model for function execution."""

    args: list = []
    kwargs: dict = {}


class DependencyData(BaseModel):
    """Model for dependency data."""

    module_name: str


module_name = os.environ.get("MODULE_NAME")
if not module_name:
    logger.critical("No module name provided")
    sys.exit(1)

try:
    module = importlib.import_module(module_name)
except ImportError:
    logger.error(f"Error importing module: {module_name}")
    sys.exit(1)


def safe_pickle_loads(data: str) -> any:
    """Safely unpickle the given data."""
    try:
        return pickle.loads(data)
    except Exception as e:
        logger.error(f"Error unpickling data: {e}")
        raise ValueError(f"Error unpickling data: {e}")


def safe_pickle_dumps(data: any) -> bytes:
    """Safely pickle the given data."""
    try:
        return pickle.dumps(data, protocol=5)
    except Exception as e:
        logger.error(f"Error pickling data: {e}")
        raise ValueError(f"Error pickling data: {e}")


def install_module(module_name: str) -> None:
    """Install the given module."""
    try:
        subprocess.check_call([sys.executable, "-m", "pip", "install", module_name])
        logger.info(f"Installed module: {module_name}")
    except Exception as e:
        logger.error(f"Failed to install module {module_name}: {e}")


@app.get("/health")
def health_check() -> dict:
    """Install the given module."""
    return {"status": "ok"}


@app.post("/install_dependency/")
def install_dependency(data: DependencyData) -> dict:
    """Install a module dependency."""
    module_name = data.module_name
    logger.info(f"Attempting to install module: {module_name}")
    try:
        install_module(module_name)
        return {"status": "success", "message": f"Installed {module_name}"}
    except Exception as e:
        logger.error(f"Failed to install module {module_name}: {str(e)}")
        return {
            "status": "error",
            "message": f"Error installing {module_name}: {str(e)}",
        }


@app.get("/{module_name}/__module_info__")
def get_module_info(module_name: str) -> dict:
    """Get information about a module."""
    logger.info(f"Fetching info for module: {module_name}")
    if module_name not in sys.modules:
        try:
            module_to_check = importlib.import_module(module_name)
        except ImportError:
            raise HTTPException(
                status_code=404, detail=f"Module {module_name} not found."
            )
    else:
        module_to_check = sys.modules[module_name]
    attributes = dir(module_to_check)
    info = {}
    for attr in attributes:
        attribute_value = getattr(module_to_check, attr)
        if callable(attribute_value):
            info[attr] = "function"
        elif isinstance(attribute_value, type):
            info[attr] = "class"
        else:
            info[attr] = "attribute"
    return {"result": info}


@app.get("/{module_name}/{attribute}")
def get_attribute(module_name: str, attribute: str) -> dict:
    """Get an attribute from a module."""
    logger.info(f"Fetching attribute {attribute} for module: {module_name}")
    if module_name not in sys.modules:
        try:
            module_to_check = importlib.import_module(module_name)
        except ImportError:
            raise HTTPException(
                status_code=404, detail=f"Module {module_name} not found."
            )
    else:
        module_to_check = sys.modules[module_name]

    attr = getattr(module_to_check, attribute, None)
    if not attr:
        raise HTTPException(
            status_code=404,
            detail=f"Attribute {attribute} not found in module {module_name}. Available attributes: {dir(module_to_check)}",
        )

    if callable(attr):
        logger.info(f"Server identified {attribute} as callable")
        return {"type": "function"}
    elif isinstance(attr, type(module_to_check)):
        return {"result": f"<module '{attribute}' from '{attr.__file__}'>"}
    else:
        return {"result": str(attr)}


@app.post("/{attribute}")
def set_attribute(attribute: str, data: AttributeValue) -> dict:
    """Set an attribute in a module."""
    logger.info(f"Setting attribute {attribute}")
    if not hasattr(module, attribute):
        raise HTTPException(status_code=404, detail="Attribute not found")

    setattr(module, attribute, data.value)
    return {"status": "success", "message": f"Set {attribute} to {data.value}"}


@app.post("/{module_name}/{attribute}/execute")
async def execute_function(request: Request, module_name: str, attribute: str) -> dict:
    """Execute a function in a module."""
    logger.info(f"Executing function {attribute} for module: {module_name}")
    body = await request.body()
    data = pickle.loads(body)

    if module_name not in sys.modules:
        try:
            module_to_check = importlib.import_module(module_name)
        except ImportError:
            raise HTTPException(
                status_code=404, detail=f"Module {module_name} not found."
            )
    else:
        module_to_check = sys.modules[module_name]

    func = getattr(module_to_check, attribute, None)
    if not func or not callable(func):
        raise HTTPException(
            status_code=404,
            detail=f"Function {attribute} not found in module {module_name}. Available attributes: {dir(module_to_check)}",
        )

    args = data.get("args", [])
    kwargs = data.get("kwargs", {})

    with warnings.catch_warnings(record=True) as w:
        warnings.simplefilter("always")
        try:
            result = func(*args, **kwargs)
            if hasattr(result, "item") and callable(result.item):
                try:
                    scalar_value = result.item()
                    return {"result": scalar_value}
                except Exception:
                    pass
            if isinstance(result, (int, float, str)):
                return {"result": result}
            if not isinstance(result, dict):
                result = {"result": result}
            serialized_result = safe_pickle_dumps(result)
            if w:
                missing_modules = []
                for warn in w:
                    if "No module named" in str(warn.message):
                        missing_module = str(warn.message).split("'")[1]
                        missing_modules.append(missing_module)
                if missing_modules:
                    logger.warning(
                        f"Missing modules detected: {', '.join(missing_modules)}"
                    )
                    return {
                        "status": "error",
                        "message": "Missing module dependencies.",
                        "missing_modules": missing_modules,
                    }
                else:
                    return Response(
                        content=serialized_result, media_type="application/octet-stream"
                    )
            else:
                # Return the pickled result as a streaming response
                return Response(
                    content=serialized_result, media_type="application/octet-stream"
                )

        except Exception as e:
            logger.exception("An error occurred while processing the request.")

            return {"error": f"Error executing function {attribute}: {str(e)}"}


if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
