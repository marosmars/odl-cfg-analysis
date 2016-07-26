from setuptools import setup


def readme():
    with open('README.rst') as f:
        return f.read()

setup(name='odl_cfg_analysis',
      version='0.1.1',
      description='Small utility visualizing ODLs config subsystem dependencies by parsing xml based config files',
      long_description=readme(),
      url='https://github.com/marosmars/odl-cfg-analysis',
      keywords='opendaylight configuration graph analysis',
      author='Maros Mars',
      author_email='maros.mars@gmail.com',
      license='Apache2',
      packages=['odl_cfg_analysis'],
      install_requires=[
          'graphviz',
      ],
      entry_points={
            'console_scripts': ['odl-cfg-analyze=odl_cfg_analysis.command_line:main'],
      },
      include_package_data=True,
      zip_safe=False)