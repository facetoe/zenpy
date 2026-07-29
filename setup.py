from setuptools import setup
import setuptools
from pathlib import Path

this_directory = Path(__file__).parent
long_description = (this_directory / "README.md").read_text()
setup(
    name='zenpy',
    packages=setuptools.find_packages(),
    version='2.0.57',
    description='Python wrapper for the Zendesk API',
    long_description=long_description,
    long_description_content_type='text/markdown',
    license='GPLv3',
    license_files = ('LICENSE'),
    author='Face Toe',
    author_email='facetoe@facetoe.com.au',
    url='https://github.com/facetoe/zenpy',
    download_url='https://github.com/facetoe/zenpy/releases/tag/2.0.57',
    install_requires=[
        'requests>=2.14.2',
        'python-dateutil>=2.7.5',
        'cachetools>=3.1.0',
        'pytz>=2018.9',
        'six>=1.14.0',
        'requests_oauth2client>=1.8.0',
    ],
    python_requires='>=3.9',
    keywords=['zendesk', 'api', 'wrapper'],
    classifiers=[
        'Development Status :: 5 - Production/Stable',
        'Intended Audience :: Developers',
        'Intended Audience :: Information Technology',
        'Intended Audience :: System Administrators',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.9',
        'Programming Language :: Python :: 3.10',
        'Programming Language :: Python :: 3.11',
        'Programming Language :: Python :: 3.12',
        'Programming Language :: Python :: 3.13',
        'License :: OSI Approved :: GNU General Public License v3 (GPLv3)',
        'Natural Language :: English',
    ],
)
