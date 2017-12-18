from setuptools import setup
import setuptools

setup(
    name='zenpy',
    packages=setuptools.find_packages(),
    version='1.2.5',
    description='Python wrapper for the Zendesk API',
    license='GPLv3',
    author='Face Toe',
    author_email='facetoe@facetoe.com.au',
    url='https://github.com/facetoe/zenpy',
    download_url='https://github.com/facetoe/zenpy/releases/tag/1.2.5',
    install_requires=[
        'requests>=2.7.0',
        'python-dateutil>=2.4.0',
        'cachetools>=1.0.3',
        'pytz>=2017.3',
        'future>=0.16.0'
    ],
    keywords=['zendesk', 'api', 'wrapper'],
    classifiers=[
        'Development Status :: 5 - Production/Stable',
        'Intended Audience :: Developers',
        'Programming Language :: Python :: 2',
        'Programming Language :: Python :: 3',
        'License :: OSI Approved :: GNU General Public License v3 (GPLv3)'
    ],
)
