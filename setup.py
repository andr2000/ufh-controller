from distutils.core import setup

setup(
    name='ufh-controller',
    version='0.1',
    packages=['', 'table_logger'],
    url='https://github.com/andr2000/ufh-controller',
    license='GPLv2',
    author='Oleksandr Andrushchenko',
    author_email='andr2000@gmail.com',
    description='Customized underfloor heating controller',
    data_files=[
        ('/etc/default', ['etc/default/ufh-controller']),
        ('/etc/init.d', ['etc/init.d/ufh-controller']),
        ('/etc/ufh-controller', [
            'etc/ufh-controller/ufh-controller.conf',
            'etc/ufh-controller/schema.sql'
        ]),
    ]
)
