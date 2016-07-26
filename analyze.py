import xml.etree.ElementTree as Et
import graphviz as gv
import re
import glob
from functools import reduce
from os import path


class OdlConfig:
    NAMESPACES = {"netconf": 'urn:ietf:params:xml:ns:netconf:base:1.0',
                  "config": 'urn:opendaylight:params:xml:ns:yang:controller:config'}
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

    def find_module(self, module_name, module_type=None):
        for module in self.modules:
            if module_type is None or module["module_type"] == module_type:
                if module["module_name"] == module_name:
                    return module

    @staticmethod
    def from_config_xml_dir(config_dir):
        if not path.isdir(config_dir):
            raise Exception("Not a directory: {}".format(config_dir))
        # parse all .xml files in folder (non-recursive) and reduce into a single instance
        return reduce(lambda a, b: a.merge(b),
                      [OdlConfig.from_config_xml(xml_file) for xml_file in glob.glob(path.join(config_dir, "*.xml"))])

    @staticmethod
    def from_config_xml(config_xml):
        if not path.isfile(config_xml):
            raise Exception("Not a file: {}".format(config_xml))

        # Workaround for ET stripping some namespaces
        events = ("start", "start-ns", "end-ns")
        namespace_mapping = {}
        namespaces = []
        root = None
        for event, elem in Et.iterparse(config_xml, events=events):
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
            module_type_element = OdlConfig.__get_child(module, "type")
            module_type_split = module_type_element.text.split(':', 1)

            dependencies = []
            for module_child in list(module):
                for nested_module_child in module_child.iter():
                    if OdlConfig.__is_dependency(nested_module_child):
                        typ = OdlConfig.__get_child(nested_module_child, "type")
                        typ_split = typ.text.split(':', 1)
                        nam = OdlConfig.__get_child(nested_module_child, "name")
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
            service_type_element = OdlConfig.__get_child(service, "type")
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
        if len(list(module_child)) != 2:
            return False

        if OdlConfig.__get_child(module_child, "type") is None:
            return False

        if OdlConfig.__get_child(module_child, "name") is None:
            return False
        return True

    @staticmethod
    def __get_child(element, tag):
        s = str(element)
        in_cfg_namespace = element.find("config:{}".format(tag), OdlConfig.NAMESPACES)
        # fallback is to use parent namespace
        return in_cfg_namespace if (in_cfg_namespace is not None) else element.find(
            "{}{}".format(s[s.index('{'):s.index('}') + 1], tag))


def get_module_name(module, graph_settings):
    module_node_text = ""
    if graph_settings["module_namespaces"]:
        module_node_text += "{" + (module["module_type_namespace"].replace(":", "_")) + "}"
    if graph_settings["module_types"]:
        module_node_text += "({})".format(module["module_type"])
    module_node_text += module["module_name"]
    return module_node_text


def get_service_name(service, graph_settings):
    service_node_text = ""
    if graph_settings["service_namespaces"]:
        service_node_text += "{" + (service["service_type_namespace"].replace(":", "_")) + "}"
    if graph_settings["service_types"]:
        service_node_text += "({})".format(service["service_type"])
    service_node_text += service["service_name"]
    return service_node_text

# TODO log
# TODO extract input arguments(fir, format, whether to include namespace or not)
# TODO add ability to color specific branch(es) depending on input e.g. certain module names
# config_locations = ["/home/mmarsale/hc-deps/01-netconf.xml", "/home/mmarsale/hc-deps/00-netty.xml"]
config_locations = ["/home/mmarsale/hc-deps/"]
modules_of_interest = ["interfaces-honeycomb-writer", "initializer-registry", "v3po-default"]
graph_settings = {"module_namespaces": False,
                  "module_types": True,
                  "service_namespaces": False,
                  "service_types": False}
graph_style_file = 'graph_style'
default_styles = eval(open(graph_style_file, 'r').read())
graph_format = 'jpeg'
graph_file = "dependencies"

print("Parsing files {}".format(config_locations))

aggregated = OdlConfig([], [])
for cfg_loc in config_locations:
    aggregated = aggregated.merge(OdlConfig.from_config_xml_dir(cfg_loc) if path.isdir(cfg_loc) else
                                  OdlConfig.from_config_xml(cfg_loc))
    print("Parsed {}".format(cfg_loc))


def extend_down(odl_config, module_of_interest):
    m = odl_config.find_module(module_name=module_of_interest)
    direct_deps = [module_of_interest]
    for dep in m["dependencies"]:
        s = odl_config.find_service(dep["dependency_type_namespace"], dep["dependency_type"], dep["dependency_name"])
        direct_deps.extend(extend_down(odl_config, s["module_name"]))
    return direct_deps

modules_of_interest = reduce(lambda a, b: a + b, [extend_down(aggregated, m) for m in modules_of_interest])
print("Highlighting modules: {}".format(modules_of_interest))

print("Creating graph at {}".format(graph_file))
g1 = gv.Digraph(format=graph_format, graph_attr=default_styles['graph'], node_attr=default_styles['nodes'], edge_attr=default_styles['edges'])

for module in aggregated.modules:
    # Apply interest style if should
    node_style = default_styles["nodes_of_interest"] if module["module_name"] in modules_of_interest else {}
    g1.node(get_module_name(module, graph_settings), _attributes=node_style)

    for dep in module["dependencies"]:
        service = aggregated.find_service(dep["dependency_type_namespace"],
                                          dep["dependency_type"],
                                          dep["dependency_name"])
        if service is None:
            # Cannot find dependency, create artificial one
            dependency_module = {"module_type_namespace": dep["dependency_type_namespace"],
                                 "module_type": dep["dependency_type"],
                                 "module_name": "UNKNOWN" + dep["dependency_name"]}
            service = {"service_type_namespace": dep["dependency_type_namespace"],
                       "service_type": dep["dependency_type"],
                       "service_name": "UNKNOWN" + dep["dependency_name"]}
        else:
            dependency_module = aggregated.find_module(service["module_name"],
                                                       service["module_type"])
        g1.edge(get_module_name(module, graph_settings), get_module_name(dependency_module, graph_settings),
                get_service_name(service, graph_settings))

filename = g1.render(filename=graph_file)
print("Graph at {} created successfully".format(graph_file))
