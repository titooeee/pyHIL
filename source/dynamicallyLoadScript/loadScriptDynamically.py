import importlib.util
import sys
import os

def load_script(script_path, module_name):
    spec = importlib.util.spec_from_file_location(module_name, script_path)
    module = importlib.util.module_from_spec(spec)
    sys.modules[module_name] = module
    spec.loader.exec_module(module)
    return module

while True:
    script_path = input("Enter the path to the Python script (or 'exit' to quit): ")

    if script_path.lower() == 'exit':
        print("Exiting the script loader.")
        break

    if not os.path.exists(script_path):
        print("The file does not exist. Please provide a valid path.")
        continue

    module_name = input("Enter a name for the module: ")
    
    try:
        loaded_module = load_script(script_path, module_name)
        print(f"Module '{module_name}' loaded successfully.")
        loaded_module.greet("Titoo")
        result = loaded_module.add(3, 5)
        print(f"3 + 5 = {result}")

        person = loaded_module.Person("Titoo", 30)
        person.introduce()
                
        # Call a function from the loaded module (if applicable)
        # Example: loaded_module.some_function()
        
    except Exception as e:
        print(f"Failed to load module: {e}")
