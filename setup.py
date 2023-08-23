#!/usr/bin/env python3

import setuptools
import superkabuki

with open("README.md", "r") as fh:
    readme = fh.read()

setuptools.setup(
    name="superkabuki",
    version=superkabuki.version(),
    author="Adrian of Doom",
    author_email="spam@iodisco.com",
    description="superkabuki is SCTE-35 Packet injection for the people",
    long_description=readme,
    long_description_content_type="text/markdown",
    url="https://github.com/futzu/superkabuki",
    py_modules=["superkabuki"],
    scripts=["bin/superkabuki"],
    platforms="all",
    install_requires=[
        "threefive >= 2.4.1",
        "new_reader >= 0.1.7",
        "iframes >= 0.0.7",
    ],
    classifiers=[
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
        "Programming Language :: Python :: 3.6",
        "Programming Language :: Python :: Implementation :: PyPy",
        "Programming Language :: Python :: Implementation :: CPython",
    ],
    python_requires=">=3.6",
)
