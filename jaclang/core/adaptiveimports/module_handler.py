"""Server module for handling module operations in a FastAPI application."""

# Standard library imports
import importlib
import importlib.util
import logging
import os
import pickle
import subprocess
import sys
import threading
import uuid
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

install_tasks = {}


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


class InstallModule(BaseModel):
    """Model for module installation."""

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


# def install_module(module_name: str) -> None:
#     """Install the given module."""
#     try:
#         subprocess.check_call([sys.executable, "-m", "pip", "install", module_name])
#         logger.info(f"Installed module: {module_name}")
#     except Exception as e:
#         logger.error(f"Failed to install module {module_name}: {e}")


@app.get("/health")
def health_check() -> dict:
    """Install the given module."""
    return {"status": "ok"}


@app.post("/install_module/")
def install_module(module_name: InstallModule) -> dict:
    """Install the given module."""
    print(f"Received request to install module: {module_name}")  # Add logging
    task_id = str(uuid.uuid4())
    install_tasks[task_id] = "in-progress"
    threading.Thread(
        target=background_install, args=(module_name.module_name, task_id)
    ).start()
    return {"task_id": task_id}


def reload_module(module_name: str) -> None:
    """Reload the given module if it's already imported. If not, it imports the module."""  # noqa
    if module_name in sys.modules:
        importlib.reload(sys.modules[module_name])
    else:
        importlib.import_module(module_name)


def background_install(module_name: str, task_id: str) -> None:
    """Install the given module in a background thread."""
    logger.info(f"Installing module {module_name} in background thread")
    try:
        # Install the module
        subprocess.check_call([sys.executable, "-m", "pip", "install", module_name])

        # Attempt a dynamic import
        spec = importlib.util.find_spec(module_name)
        if spec is not None:
            module = importlib.util.module_from_spec(spec)
            sys.modules[module_name] = module
            spec.loader.exec_module(module)

        # Post-installation steps
        if "transformers" in sys.modules:
            from transformers import BertModel

            BertModel.from_pretrained("bert-base-uncased")

        install_tasks[task_id] = "completed"

        # Restart the server
        os.execv(sys.executable, ["python"] + sys.argv)

    except Exception as e:
        install_tasks[task_id] = f"error: {str(e)}"


@app.get("/install_status/{task_id}/")
def install_status(task_id: str) -> dict:
    """Get the status of the given module installation task."""
    return {"status": install_tasks.get(task_id, "not-found")}


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

    # Split the module_name to get potential class name
    parts = module_name.rsplit(".", 1)
    if len(parts) == 2:
        module_name, class_name = parts
    else:
        class_name = None

    if module_name not in sys.modules:
        try:
            module_to_check = importlib.import_module(module_name)
        except ImportError:
            raise HTTPException(
                status_code=404, detail=f"Module {module_name} not found."
            )
    else:
        module_to_check = sys.modules[module_name]

    try:
        if class_name:
            class_to_check = getattr(module_to_check, class_name, None)
            if not class_to_check:
                raise HTTPException(
                    status_code=404,
                    detail=f"Class {class_name} not found in module {module_name}.",
                )
            attr = getattr(class_to_check, attribute, None)
        else:
            attr = getattr(module_to_check, attribute, None)
    except ImportError as e:
        return {"status": "error", "message": str(e)}
    if not attr:
        raise HTTPException(
            status_code=404,
            detail=f"Attribute {attribute} not found in module {module_name}. Available attributes: {dir(module_to_check)}",  # noqa
        )

    if callable(attr):
        if isinstance(attr, (staticmethod, classmethod)):
            logger.info(f"Server identified {attribute} as a class method")
            return {"type": "class_method"}
        elif isinstance(attr, type):
            logger.info(f"Server identified {attribute} as a class")
            return {"type": "class"}
        else:
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
    """Execute a function or class method in a module."""
    logger.info(
        f"Executing function or class method {attribute} for module: {module_name}"
    )
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

    callable_obj = getattr(module_to_check, attribute, None)
    if not callable_obj or not callable(callable_obj):
        raise HTTPException(
            status_code=404,
            detail=f"Function or class method {attribute} not found in module {module_name}. Available attributes: {dir(module_to_check)}",  # noqa
        )

    args = data.get("args", [])
    kwargs = data.get("kwargs", {})

    with warnings.catch_warnings(record=True) as w:
        warnings.simplefilter("always")
        try:
            result = callable_obj(*args, **kwargs)
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
                return Response(
                    content=serialized_result, media_type="application/octet-stream"
                )

        except Exception as e:
            logger.exception("An error occurred while processing the request.")
            return {
                "error": f"Error executing function or class method {attribute}: {str(e)}"  # noqa
            }


if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
