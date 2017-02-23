from setuptools import setup
from setuptools import find_packages

setup(name='nginxparser_eb',
      version='0.0.3',
      description='Nginx configuration Parser',
      author='Fatih Erikli',
      author_email='fatiherikli@gmail.com',
      url='https://github.com/EnigmaBridge/nginxparser',
      license=open('LICENSE').read(),
      long_description=open('README.rst').read(),
      classifiers=[
        'Development Status :: 3 - Alpha',
        'Intended Audience :: Developers',
        'Programming Language :: Python',
        'Programming Language :: Python :: 2',
        'Programming Language :: Python :: 2.6',
        'Programming Language :: Python :: 2.7',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.3',
        'Programming Language :: Python :: 3.4',
        'Programming Language :: Python :: 3.5',
        'Topic :: Internet :: WWW/HTTP'
      ],

      packages=find_packages(),
      include_package_data=True,
      install_requires=[
          'pyparsing>=1.5.5'
      ],
      extras_require={
            'dev': ['mockio']
      },
)


