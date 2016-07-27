ODL config subsystem dependency analysis tool
---------------------------------------------

Installation:
------------
easy_install odl-cfg-analysis

pip3 install odl_cfg_analysis

CLI Usage:
----------

odl-cfg-analyze --paths-to-analyze /home/projects/hc-deps/ --highlight-modules initializer-registry

Note: The paths-to-analyze can be a list of xml files or folders containing such files (non-recursively searched) or any combination of them. Ideal is to run the analysis on ODL's karaf distribution folder: etc/opendaylight/karaf where all configs used in the distribution are stored (after first run)

Sample output:
--------------
Sample output: https://jira.fd.io/secure/attachment/10602/dependencies.jpeg
