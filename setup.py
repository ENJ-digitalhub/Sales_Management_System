
from setuptools import setup, find_packages

setup(
    name='sales_management_system_backend',
    version='0.1.0',
    packages=find_packages(where='backend'),
    package_dir={'': 'backend'},
    include_package_data=True,
    install_requires=[
        'Flask==3.0.3',
        'SQLAlchemy==2.0.30',
        'Flask-Cors==4.0.1',
        'python-dotenv==1.0.1',
        'PyJWT==2.8.0',
        'Werkzeug==3.0.3',
        'passlib==1.7.4',
        'bcrypt==4.1.3',
        'idna==3.7',
        'greenlet==3.0.3',
        'Mako==1.3.2',
        'MarkupSafe==2.1.5',
        'packaging==24.0',
        'typing_extensions==4.12.2',
        'zope.interface==6.4',
        'SQLAlchemy-Utils==0.41.2',
        'alembic==1.13.1',
        'psycopg2-binary==2.9.9',
    ],
    extras_require={
        'dev': [
            'pytest==9.1.1',
            'pytest-flask==1.3.0',
        ]
    },
    entry_points={
        'console_scripts': [
            'sms-cli=cli.cli:main',
        ],
    },
    author='ENJ DigitalHub',
    author_email='info@enj-digitalhub.com',
    description='Backend for the Sales Management System',
    long_description=open('README.md').read(),
    long_description_content_type='text/markdown',
    url='https://github.com/ENJ-digitalhub/Sales_Management_System',
    classifiers=[
        'Programming Language :: Python :: 3',
        'License :: OSI Approved :: MIT License',
        'Operating System :: OS Independent',
    ],
    python_requires='>=3.9',
)
