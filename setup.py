# Copyright (C) 2018 Lukas Vrabec, <lvrabec@redhat.com>
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <https://www.gnu.org/licenses/>.

import setuptools
from setuptools.command.install import install
import os

from udica.version import version

with open("README.md", "r") as fh:
    long_description = fh.read()

setuptools.setup(
    name="udica",
    version=version,
    author="Lukas Vrabec",
    author_email="lvrabec@redhat.com",
    description="A tool for generating SELinux security policies for containers",
    license="GPLv3+",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/containers/udica",
    packages=["udica"],
    python_requires=">=3.4, <4",
    data_files=[
        ("/usr/share/licenses/udica", ["LICENSE"]),
        ("/usr/share/udica/ansible", ["udica/ansible/deploy-module.yml"]),
        ("/usr/share/udica/macros", ["udica/macros/confined_user_macros.cil"]),
    ],
    # scripts=["bin/udica"],
    entry_points={"console_scripts": ["udica=udica.__main__:main"]},
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: GNU General Public License v3 or later (GPLv3+)",
        "Operating System :: OS Independent",
    ],
)
