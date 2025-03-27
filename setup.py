from setuptools import setup, find_packages

setup(
    name='qrgrading',
    version='0.0.1',
    packages=find_packages(where='src'),  # Specify src directory
    package_dir={'': 'src'},  # Tell setuptools that packages are under src
    install_requires=[
        'pyqt5',
        'pymupdf >= 1.18.17',
        'easyconfig2',
        'zxing-cpp',
        'gspread',
        'pydrive2',
        'opencv-python-headless',
        'pandas',
        'swikv4-minimal'
    ],
    author='Danilo Tardioli',
    author_email='dantard@unizar.es',
    description='A framwork for automatic grading of exams using QR codes',
    long_description=open('README.md').read(),
    long_description_content_type='text/markdown',
    url='https://github.com/dantard/qrgrading',
    classifiers=[
        'Programming Language :: Python :: 3',
        'License :: OSI Approved :: MIT License',
        'Operating System :: OS Independent',
    ],
    python_requires='>=3.10',
    entry_points={
        'console_scripts': [
            'qrscanner=qrgrading.qrscanner:main',
            'qrgrader=qrgrading.qrgrader:main',
            'qrsheets=qrgrading.qrsheets:main',
            'qrgenerator=qrgrading.qrgenerator:main',
            'qrworkspace=qrgrading.qrworkspace:main',
        ],
    },
    package_data={
        "qrgrading": ["latex/*"],
    },
    include_package_data=True,
)
