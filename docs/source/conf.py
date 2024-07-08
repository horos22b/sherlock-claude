# Configuration file for the Sphinx documentation builder.

import os
import sys
sys.path.insert(0, os.path.abspath('../../scripts'))
sys.path.insert(0, os.path.abspath('../../lib'))

# -- Project information -----------------------------------------------------
project = 'Sherlock Claude'
copyright = '2024, Edward Peschko'
author = 'Edward Peschko'

# The full version, including alpha/beta/rc tags
release = '0.1'

# Add any Sphinx extension module names here, as strings
extensions = [
    'sphinx.ext.autodoc',
    'sphinx.ext.napoleon',
    'sphinx.ext.viewcode',
    'sphinx_rtd_theme',
]

templates_path = ['_templates']
exclude_patterns = []

# Use Read the Docs theme
html_theme = 'sphinx_rtd_theme'

# Add any paths that contain custom static files (such as style sheets) here
html_static_path = ['_static']

# Custom CSS file
html_css_files = [
    'custom.css',
]

# Theme options
html_theme_options = {
    'navigation_depth': 4,
    'collapse_navigation': False,
    'sticky_navigation': True,
    'includehidden': True,
    'titles_only': False,
}

# Extension configuration
autodoc_mock_imports = ["requests", "dotenv"]
