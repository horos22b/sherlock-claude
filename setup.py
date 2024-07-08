from setuptools import setup, find_packages

setup(
    name="SherlockClaude",
    version="1.0",
    packages=find_packages(where='lib'),
    package_dir={'': 'lib'},
    install_requires=[
        'requests',
        'python-dotenv'
    ],
    extras_require={
        'docs': ['Sphinx'],
    },
    entry_points={
        "console_scripts": [
            "sherlock_claude=lib.main:main",
        ],
    },
    author="Edward Peschko",
    author_email="ed.peschko@gmail.com",
    description="claude as a criminal investigator",
    long_description=open("README.md").read(),
    long_description_content_type="text/markdown",
    url="https://github.com/epeschko/sherlock.claude"
)
