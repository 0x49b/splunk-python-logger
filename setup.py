from setuptools import setup
import pathlib

# The directory containig this file
HERE = pathlib.Path(__file__).parent

# The README File
README = (HERE / "readme.md").read_text()

setup(
    name='splunk_python_logger',
    version='1.1.0',
    license='MIT',
    description='A Python logging Handler to send events to SplunkEnterprise running the Splunk HTTP Event Collector.',
    long_description=README,
    long_description_content_type='text/markdown',
    author='Florian Thiévent',
    author_email='florian@lichtwellenreiter.org',
    url='https://github.com/lichtwellenreiter/splunk-python-logger',
    packages=['splunk_python_logger'],
    include_package_data =True,
    install_requires=['requests >= 2.6.0, < 3.0.0'],
    classifiers=[
        'Development Status :: 4 - Beta',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: MIT License',
        'Natural Language :: English',
        'Operating System :: POSIX :: Linux',
        'Operating System :: MacOS :: MacOS X',
        'Programming Language :: Python',
        'Programming Language :: Python :: 3.5',
        'Programming Language :: Python :: 3.6',
        'Programming Language :: Python :: 3.7',
        'Programming Language :: Python :: 3.8',
        'Topic :: System :: Logging'
    ]
)
