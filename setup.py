"""Install script for `starry_process`."""
import os
from setuptools import find_packages, setup

setup(
    name="delicatessen",
    author="online.tess.science 2020",
    author_email="rodluger@gmail.com",
    url="https://github.com/adrn/delicatessen",
    description="tess visualization webapp",
    long_description=open("README.md", "r").read(),
    long_description_content_type="text/markdown",
    license="MIT",
    packages=find_packages(),
    use_scm_version={
        "write_to": os.path.join("delicatessen", "delicatessen_version.py"),
        "write_to_template": '__version__ = "{version}"\n',
    },
    install_requires=[
        "setuptools_scm",
        "numpy>=1.13.0",
        "astropy>=4.0.1",
        "bokeh>=2.2.1",
        "requests>=2.22.0",
        "pandas>=0.25.1",
        "tess-point>=0.4.3",
        "pre-commit",
    ],
    setup_requires=["setuptools_scm"],
    scripts=["bin/deli"],
    include_package_data=True,
    zip_safe=False,
)
