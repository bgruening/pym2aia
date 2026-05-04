import setuptools
from setuptools import find_namespace_packages
from wheel.bdist_wheel import bdist_wheel
import pathlib
import os

with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

VERSION = "0.6.0"

class bdist_wheel_plat(bdist_wheel):
    """Emit a platform-specific wheel tag based on the bundled binaries."""

    def get_tag(self):
        python, abi, _ = super().get_tag()
        bin_dir = pathlib.Path("src/m2aia/bin")
        if any(bin_dir.glob("*.so*")):
            tag = "manylinux_2_39_x86_64"
        elif any(bin_dir.glob("*.dll")):
            tag = "win_amd64"
        else:
            tag = "any"
        return python, abi, tag


setuptools.setup(
    name="m2aia",
    version=VERSION,
    cmdclass={"bdist_wheel": bdist_wheel_plat},
    author="Jonas Cordes",
    author_email="j.cordes@th-mannheim.de",
    description="Provide interfaces for M²aia v2026.05",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://m2aia.github.io/m2aia",
    project_urls={
        "Bug Tracker": "https://github.com/m2aia/pym2aia/issues",
    },
    classifiers=[
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.12",
        "License :: OSI Approved :: BSD License",
        "Operating System :: POSIX :: Linux",
        "Operating System :: Microsoft :: Windows",
        "Topic :: Scientific/Engineering :: Image Processing :: Mass Spectrometry Imaging",
        "Development Status :: 4 - Beta",
    ],
    packages=find_namespace_packages(where='src'),
    package_dir={"": "src"},
    # include_package_data=True,
    package_data={
        "m2aia.bin": ["*"],
        },
    python_requires=">=3.8",
    install_requires=[
          'wheel',
          'numpy',
          'SimpleITK',
          'wget'
      ],
    
)
