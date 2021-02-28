import setuptools
from distutils.core import setup

with open("README.md", "r") as fh:
    long_description = fh.read()

setup(
    name='df1py3',
    version='1.0a28',
    packages=setuptools.find_packages(),
    url='https://github.com/reyanvaldes/Df1',
    license='MIT License',
    author='Jerther,rvaldes',
    author_email='jtheriault@metalsartigan.com, rvaldes@itgtec.com',
    description='A basic DF1 implementation in Python3',
    long_description=long_description,
    long_description_content_type="text/markdown",
)
