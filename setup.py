from setuptools import setup, find_packages
from codecs import open
from os import path

here = path.abspath(path.dirname(__file__))

# Get the long description from the README file
with open(path.join(here, 'README.rst'), encoding='utf-8') as f:
    long_description = f.read()

setup(
    name='traffic_light',
    version='0.0.0',
    description='Traffic Ligth PDF generator',
    long_description=long_description,
    url='https://github.com/pypa/MY_URL',
    author='Sergey Komarov',
    author_email='sergey@savonix.com',
    license='MIT',
    classifiers=[
        'Development Status :: 3 - Alpha',
        'Intended Audience :: Savonix.com',
        'Topic :: Software Development :: Build Tools',
        'License :: OSI Approved :: MIT License',
        'Programming Language :: Python :: 2.7',
    ],
    keywords='pdf html convertor',
    packages=find_packages(),
    install_requires=[
        'watchdog',
        'libsass',
        'weasyprint',
        'html5lib==1.0b10',
        'Jinja2',
        'Babel',
        'flask'
    ],
    entry_points={
        'console_scripts': [
            'compiler=watcher:run',
        ],
    },
)
