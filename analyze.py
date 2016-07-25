import xml.etree.ElementTree as Et
import graphviz as gv
import re
import glob
from functools import reduce
from os import path


class OdlConfig:
    NAMESPACES = {'netconf': 'urn:ietf:params:xml:ns:netconf:base:1.0',
                  'config': 'urn:opendaylight:params:xml:ns:yang:controller:config'}
    MODULE_PATH = "configuration/netconf:data/config:modules/config:module"
    SERVICE_PATH = "configuration/netconf:data/config:services/config:service"

    def __init__(self, modules, services):
        self.modules = modules
        self.services = services

    def __str__(self):
        return "OdlConfig[modules={}, services={}]".format(self.modules, self.services)

    def merge(self, other):
        m = []
        m.extend(self.modules)
        m.extend(other.modules)
        s = []
        s.extend(self.services)
        s.extend(other.services)
        return OdlConfig(m, s)

    def find_service(self, service_type_namespace, service_type, service_name):
        for service in self.services:
            if service["service_type_namespace"] == service_type_namespace and service[
                    "service_type"] == service_type and service["service_name"] == service_name:
                return service

    @staticmethod
    def from_config_xml(configxml):
        events = ("start", "start-ns", "end-ns")

        # Workaround for ET stripping some namespaces
        namespace_mapping = {}
        namespaces = []
        root = None
        for event, elem in Et.iterparse(configxml, events=events):
            if event == "start-ns":
                namespaces.append(elem)
            elif event == "start":
                namespace_mapping[elem] = dict(namespaces)
                namespaces = []
                # Find root while we are here
                if elem.tag == "snapshot":
                    root = elem

        # Empty
        if root is None:
            return OdlConfig([], [])

        modules_elements = root.findall(OdlConfig.MODULE_PATH, OdlConfig.NAMESPACES)
        modules = OdlConfig.__parse_modules(modules_elements, namespace_mapping)
        services_elements = root.findall(OdlConfig.SERVICE_PATH, OdlConfig.NAMESPACES)
        services = OdlConfig.__parse_services(services_elements, namespace_mapping)

        if not modules and not services:
            return OdlConfig([], [])
        return OdlConfig(modules, services)

    @staticmethod
    def __parse_modules(modules_elements, namespace_mapping):
        modules = []
        for module in modules_elements:
            module_type_element = module.find("config:type", OdlConfig.NAMESPACES)
            module_type_split = module_type_element.text.split(':', 1)

            dependencies = []
            for module_child in list(module):
                for nested_module_child in module_child.iter():
                    if OdlConfig.__is_dependency(nested_module_child):
                        typ = nested_module_child.find("config:type", OdlConfig.NAMESPACES)
                        typ_split = typ.text.split(':', 1)
                        nam = nested_module_child.find("config:name", OdlConfig.NAMESPACES)
                        dependencies.append({"dependency_type_namespace": namespace_mapping[typ][typ_split[0].strip()],
                                             "dependency_type": typ_split[1].strip(),
                                             "dependency_name": nam.text.strip()})

            modules.append(
                {"module_type_namespace": namespace_mapping[module_type_element][module_type_split[0].strip()],
                 "module_type": module_type_split[1].strip(),
                 "module_name": module.find("config:name", OdlConfig.NAMESPACES).text.strip(),
                 "dependencies": dependencies})

        return modules

    @staticmethod
    def __parse_services(services_mapping, namespace_mapping):
        services = []
        for service in services_mapping:
            service_type_element = service.find("config:type", OdlConfig.NAMESPACES)
            service_type_split = service_type_element.text.split(':', 1)

            for instance in service.findall("config:instance", OdlConfig.NAMESPACES):
                provider = instance.find("config:provider", OdlConfig.NAMESPACES).text.strip()
                regex = re.search("/modules/module\[type='(.+)'\]\[name='(.+)'\]", provider)

                services.append(
                    {"service_type_namespace": namespace_mapping[service_type_element][service_type_split[0].strip()],
                     "service_type": service_type_split[1].strip(),
                     "service_name": instance.find("config:name", OdlConfig.NAMESPACES).text.strip(),
                     "module_type": regex.group(1),
                     "module_name": regex.group(2)})

        return services

    @staticmethod
    def __is_dependency(module_child):
        return len(list(module_child)) == 2 and (
            module_child.find("config:type", OdlConfig.NAMESPACES) is not None) and (
                   module_child.find("config:name", OdlConfig.NAMESPACES) is not None)


def parse_configs_from_dir(config_dir):
    path.isdir(config_dir)
    return [OdlConfig.from_config_xml(xml_file) for xml_file in glob.glob(path.join(config_dir, "*.xml"))]


config_dir = "/home/mmarsale/hc-deps/"
cfgs = reduce(lambda a, b: a.merge(b), parse_configs_from_dir(config_dir))
g1 = gv.Digraph(format='svg')
for module in cfgs.modules:
    g1.node(module["module_name"])
    for dep in module['dependencies']:
        service = cfgs.find_service(dep["dependency_type_namespace"], dep["dependency_type"], dep["dependency_name"])
        g1.edge(module['module_name'], service['module_name'], service['service_name'])
filename = g1.render(filename=path.join(config_dir, "dependencies.svg"))
