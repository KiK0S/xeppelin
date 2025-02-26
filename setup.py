from setuptools import setup, find_packages

setup(
    name='xeppelin',
    version='0.1.2',
    packages=find_packages(),
    include_package_data=True,
    install_requires=[
        'pandas',
        'matplotlib',
        'numpy',
    ],
    entry_points={
        'console_scripts': [
            'xeppelin=xeppelin.xeppelin:main',
        ],
    },
    package_data={
        'xeppelin': ['xeppelin.sh'],
    },
    author='Konstantin Amelichev',
    author_email='kostya.amelichev@gmail.com',
    description='Xeppelin Contest Watcher',
    long_description=open('README.md').read(),
    long_description_content_type='text/markdown',
    url='https://github.com/kik0s/xeppelin',
    classifiers=[
        'Programming Language :: Python :: 3',
        'License :: OSI Approved :: MIT License',
        'Operating System :: OS Independent',
    ],
    python_requires='>=3.6',
) 