import os
import sys

# Add the parent directory (ghost) to Python path so Sphinx can find config and src
sys.path.insert(0, os.path.abspath('..'))

# Add both config and src directories specifically
sys.path.insert(0, os.path.abspath('../config'))
sys.path.insert(0, os.path.abspath('../src'))


# Configuration file for the Sphinx documentation builder.
#
# For the full list of built-in configuration values, see the documentation:
# https://www.sphinx-doc.org/en/master/usage/configuration.html

# -- Project information -----------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#project-information

project = 'ghost'
copyright = '2025, phantom'
author = 'phantom'
release = '1.0'

# -- General configuration ---------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#general-configuration

extensions = [
    'sphinx.ext.autodoc',        # Auto-generate from docstrings
    'sphinx.ext.autosummary',    # Generate summaries and module indexes
    'sphinx.ext.viewcode',       # Include source code links
    'sphinx.ext.napoleon',       # Support for Google/NumPy docstrings
]

templates_path = ['_templates']
exclude_patterns = []



# -- Options for HTML output -------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#options-for-html-output

html_theme = 'sphinx_rtd_theme'
html_static_path = ['_static']

# Enable autosummary to generate stub files
autosummary_generate = True

autodoc_mock_imports = ['numpy', 'pandas', 'tensorflow']

# Configure autodoc behavior
autodoc_default_options = {
    'members': True,
    'member-order': 'bysource',
    'special-members': '__init__',
    'undoc-members': True,
    'exclude-members': '__weakref__'
}