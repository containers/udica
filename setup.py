import setuptools
from setuptools.command.install import install
import os

import semanage

class PostInstallCommand(install):

    def run(self):
        install.run(self)
        
        os.chdir("./udica/templates")
        templates = os.listdir("./")

        handle = semanage.semanage_handle_create()
        semanage.semanage_connect(handle)

        for template in templates:
            semanage.semanage_module_install_file(handle, template)

        semanage.semanage_commit(handle)

with open("README.md", "r") as fh:
    long_description = fh.read()

setuptools.setup(
    name="udica",
    version="0.0.1",
    author="Lukas Vrabec",
    author_email="lvrabec@redhat.com",
    description="A tool for generating SELinux security policies for containers",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://gitlab.cee.redhat.com/lvrabec/udica",
    packages=["udica"],
    # scripts=["bin/udica"],
    entry_points = {
        'console_scripts': ['udica=udica:main'],
    },
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: GNU General Public License v3 or later (GPLv3+)",
        "Operating System :: OS Independent",
    ],
    cmdclass={
        "install": PostInstallCommand,
        }
)

