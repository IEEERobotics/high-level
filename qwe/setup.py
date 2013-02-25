from distutils.core import setup

setup(
    name='qwe',
    version='0.1.0dev',
    author='NCSU IEEE Ground Robotics Team',
    author_email='ncsuhardware@googlegroups.com',
    packages=['vision', 'sensors', 'comm', 'localizer', 'mapping', 'action', 'navigation', 'planning'],
    scripts=[],
    url='https://github.com/NCSUhardware/high-level',
    license='LICENSE.txt',
    description='IEEE SECon 2013 robot code',
    long_description=open('README.txt').read(),
    install_requires=[],
)
