import multiprocessing
import importlib

def target_process(module_name:str, pipe):
  module = importlib.import_module(module_name)
  print("Sub process", module_name)
  while True:
      # Wait for a function name and args to call
      func_name, args = pipe.recv()
      # Get the function from the target module based on the received name
      func = getattr(module, func_name)
      # Call the function and send the result back through the pipe
      result = func(*args)
      pipe.send(result)