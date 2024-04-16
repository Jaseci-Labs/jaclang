from typing import Any


class ModelClass:
    def __init__(self):
        pass

    def __infer__(self, input: str, **kwargs) -> Any:
        """Infer the model."""
        raise NotImplementedError

    def __train_step__(self, input: Any, target: Any) -> dict:
        """Train the model."""
        raise NotImplementedError


def create_model(model, **kwargs):
    """Jac's Model CC feature."""
    if issubclass(model, ModelClass):
        return model(**kwargs)
    else:
        raise TypeError(f"Expected a ModelClass instance, got {type(model)}")
