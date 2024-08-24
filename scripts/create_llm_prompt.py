import inspect

import splink.comparison_level_library as cll
import splink.comparison_library as cl
import splink.exploratory as exploratory  # Importing the exploratory module
from splink import (  # Include block_on import
    DuckDBAPI,
    Linker,
    block_on,
    blocking_analysis,
    splink_datasets,
)
from splink.internals.settings_creator import SettingsCreator

# Mock objects for instantiation, replace with real ones if available
mock_settings = SettingsCreator(
    link_type="dedupe_only"
)  # or pass a real settings object
mock_db_api = DuckDBAPI()  # or pass a real database API subclass instance

# Instantiate the Linker object
linker = Linker(
    input_table_or_tables=splink_datasets.fake_1000,  # replace with real input
    settings=mock_settings,
    db_api=mock_db_api,
)

# List of Linker submodules to extract docstrings from
submodules = [
    "inference",
    "training",
    "visualisations",
    "clustering",
    "evaluation",
    "table_management",
    "misc",
]


# Function to extract all public methods from the specified submodules of the Linker class instance
def extract_method_docstrings(linker_instance, submodule_list):
    docstrings = {}
    for submodule_name in submodule_list:
        submodule_obj = getattr(linker_instance, submodule_name)
        for name, member in inspect.getmembers(submodule_obj):
            if callable(member) and not name.startswith("_"):  # Ignore private methods
                full_method_name = (
                    f"{linker_instance.__class__.__name__}.{submodule_name}.{name}"
                )
                docstring = inspect.getdoc(member)
                docstrings[full_method_name] = (
                    docstring if docstring else "No docstring available"
                )
    return docstrings


# Function to extract docstrings from the __init__ methods of all public classes in a module
def extract_class_docstrings_from_module(module):
    docstrings = {}
    for name, obj in inspect.getmembers(module, inspect.isclass):
        if not name.startswith("_"):  # Ignore private classes
            init_docstring = inspect.getdoc(obj.__init__)
            docstrings[name] = (
                init_docstring if init_docstring else "No docstring available"
            )
    return docstrings


# Function to extract docstrings from specified functions in a module
def extract_function_docstrings(module, function_names):
    docstrings = {}
    for func_name in function_names:
        func_obj = getattr(module, func_name, None)
        if callable(func_obj):
            docstring = inspect.getdoc(func_obj)
            docstrings[func_name] = docstring if docstring else "No docstring available"
    return docstrings


# Saving the docstrings to a text file
def save_docstrings(docstrings, filename="docstrings.txt"):
    with open(filename, "w", encoding="utf-8") as file:
        for method_path, docstring in docstrings.items():
            file.write(f"{method_path}:\n")
            file.write(f"{docstring}\n\n")


# Main execution
if __name__ == "__main__":
    # Extract docstrings for all public methods in specified Linker submodules
    linker_docstrings = extract_method_docstrings(linker, submodules)

    # Extract docstrings for all public classes in comparison_library
    comparison_docstrings = extract_class_docstrings_from_module(cl)

    # Extract docstrings for all public classes in comparison_level_library
    comparison_level_docstrings = extract_class_docstrings_from_module(cll)

    # Extract docstrings for specified functions in the exploratory module
    exploratory_functions = ["completeness_chart", "profile_columns"]
    exploratory_docstrings = extract_function_docstrings(
        exploratory, exploratory_functions
    )

    # Extract docstring for block_on function
    block_on_docstring = {"block_on": inspect.getdoc(block_on)}

    # Combine all sets of docstrings
    all_docstrings = {
        **linker_docstrings,
        **comparison_docstrings,
        **comparison_level_docstrings,
        **exploratory_docstrings,
        **block_on_docstring,  # Include block_on docstring
    }

    # Save to file
    save_docstrings(all_docstrings, "docstrings.txt")
    print("Docstrings extracted and saved to docstrings.txt")
