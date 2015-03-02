# Copyright 2015 tsuru-unit-agent authors. All rights reserved.
# Use of this source code is governed by a BSD-style
# license that can be found in the LICENSE file.

from setuptools import setup, find_packages
from tsuru_unit_agent import __version__

setup(
    name="tsuru-unit-agent",
    url="https://github.com/tsuru/tsuru-unit-agent",
    version=__version__,
    packages=find_packages(),
    description="Tsuru unit agent.",
    author="tsuru",
    author_email="tsuru@corp.globo.com",
    include_package_data=True,
    install_requires=["requests", "PyYAML", "honcho==0.5.0"],
    entry_points={
        'console_scripts': [
            'tsuru_unit_agent = tsuru_unit_agent.main:main',
        ],
    },
)
