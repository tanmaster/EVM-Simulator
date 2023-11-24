#!/usr/bin/env python
# -*- coding: utf-8 -*-
from setuptools import (
    setup,
    find_packages,
)

extras_require = {}


with open('./README.md') as readme:
    long_description = readme.read()


setup(
    name='EVM-Simulator',
    # *IMPORTANT*: Don't manually change the version here. Use `make bump`, as described in readme
    version='0.1.0-alpha.0',
    long_description=long_description,
    long_description_content_type='text/markdown',
    author='Tan Yücel',
    author_email='tanyuecel@hotmail.com',
    url='https://github.com/tanmaster/EVM-Simulator',
    include_package_data=True,
    install_requires=[
        "eth-utils>=1,<2",
        "py-evm==0.3.0a5",
        "PyQt5==5.13.1",
        "eth-abi==4.2.0",
        "pysha3==1.0.2",
        "pytest>=4.4.0",
    ],
    python_requires='>=3.6, <4',
    license="MIT",
    zip_safe=False,
    keywords='ethereum',
    packages=find_packages(exclude=["tests", "tests.*"]),
    classifiers=[
        'Development Status :: 3 - Alpha',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: MIT License',
        'Natural Language :: English',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.6',
        'Programming Language :: Python :: 3.7',
        'Programming Language :: Python :: Implementation :: PyPy',
    ],
)
