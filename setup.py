from setuptools import find_packages, setup
from typing import List

def get_requirements(filepath):
    requirements = []
    with open(filepath) as f:
        requirements = f.readlines()
        requirements = [req.replace("\n", "") for req in requirements]
        if '-e .' in requirements:
            requirements.remove('-e .')
    return requirements

setup(
    name='mlproject',
    version='0.0.1',
    author='Rohit',
    author_email='rohitrnc5458@gmail.com',
    packages=find_packages(),
    install_requires=get_requirements('requirements.txt')
)