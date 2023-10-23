from setuptools import setup, find_packages

setup(
    name="SDUploader",
    version="1.0.0",
    packages=find_packages(),
    install_requires=requirements,
    entry_points={
        'console_scripts': [
            'sduploader=main:main',  # Assuming main.py is the entry point of your program
        ],
    },
    include_package_data=True,
)
