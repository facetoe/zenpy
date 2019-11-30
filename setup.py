from setuptools import setup
import setuptools

setup(
    name='zenpy',
    packages=setuptools.find_packages(),
    version='2.0.13',
    description='Python wrapper for the Zendesk API',
    license='GPLv3',
    author='Face Toe',
    author_email='facetoe@facetoe.com.au',
    url='https://github.com/facetoe/zenpy',
    download_url='https://github.com/facetoe/zenpy/releases/tag/2.0.13',
    install_requires=[
        'requests>=2.14.2',
        'python-dateutil>=2.7.5',
        'cachetools>=3.1.0',
        'pytz>=2018.9',
        'future>=0.17.1'
    ],
    keywords=['zendesk', 'api', 'wrapper'],
    classifiers=[
        'Development Status :: 5 - Production/Stable',
        'Intended Audience :: Developers',
        'Intended Audience :: Information Technology',
        'Intended Audience :: System Administrators',
        'Programming Language :: Python :: 2',
        'Programming Language :: Python :: 2.7',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.5',
        'Programming Language :: Python :: 3.6',
        'Programming Language :: Python :: 3.7',
        'License :: OSI Approved :: GNU General Public License v3 (GPLv3)',
        'Natural Language :: English',
    ],
)
