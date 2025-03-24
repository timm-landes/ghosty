from setuptools import setup, find_packages

setup(
    name='ghosty',
    version='0.1.2',
    packages=find_packages(),
    install_requires=[
        'loguru>=0.7.0',
        'telnetlib3>=2.0.0',
        'asyncio>=3.4.3',
    ],
    author='Timm Landes, Dag Heinemann',
    author_email=['timm.landes@hot.uni-hannover.de', 'dag.heinemann@hot.uni-hannover.com'],
    description='Wrapper for the Table Stable Ltd. Ghost Software',
    long_description=open('README.md').read(),
    long_description_content_type='text/markdown',
    url='https://gitlab.uni-hannover.de/phytophotonics/ghosty',
    classifiers=[
        'Programming Language :: Python :: 3',
        'Operating System :: OS Independent',
    ],
    python_requires='>=3.6,<=3.12.9',
    license='MIT', 
)