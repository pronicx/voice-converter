from setuptools import setup, find_packages
import os

# Get the long description from the README file
here = os.path.abspath(os.path.dirname(__file__))
with open(os.path.join(here, "README.md"), encoding="utf-8") as f:
    long_description = f.read()

setup(
    name="voice-converter",
    version="1.0.0",
    packages=find_packages(),
    install_requires=[
        "elevenlabs",
        "pyaudio",
        "numpy",
    ],
    entry_points={
        'console_scripts': [
            'voice-converter=voice_converter.main:main',
        ],
    },
    author="pronicx",
    author_email="proniclabs@gmail.com",
    description="A desktop application that transforms your voice into various synthetic voices in real-time",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/pronicx/voice-converter",
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
    python_requires=">=3.7",
) 