import streamlit as st
import xml.etree.ElementTree as ET
from st_cytoscape import cytoscape
import uuid
import pandas as pd

def schema_to_cytoscape(schema):
    elements = []
    for entity in schema:
        elements.append({
            "data": {
                "id": entity,
                "label": entity
            }
        })
        for child in schema[entity]["children"]:
            elements.append({
                "data": {
                    "source": entity,
                    "target": child
                }
            })
    return elements


stylesheet = [
    {"selector": "node", "style": {"label": "data(id)", "width": 50, "height": 50}},
    {
        "selector": "edge",
        "style": {
            "width": 3,
            "curve-style": "bezier",
            "target-arrow-shape": "triangle",
        },
    },
]

def show_common_concept(schema):
    cytoscape_graph = schema_to_cytoscape(schema)
    with st.expander("Step 0: Show Common Concept"):
        graph_col, data_col = st.columns([2, 1])
        with graph_col:
            st.subheader("Common Concepts:")
            with st.empty():
                selected = cytoscape(
                    cytoscape_graph,
                    layout={"name": "breadthfirst"},
                    stylesheet=stylesheet,
                    height="250px",
                    selection_type="single",
                    user_zooming_enabled=False
                    #Generate

            )
        with data_col:
            st.subheader("Attributes:")
            if selected["nodes"]:
                selected_node = selected["nodes"][0]
                attr_df = pd.DataFrame(schema[selected_node]["attributes"], columns=["Attributes"])
                st.dataframe(attr_df)
            else:
                st.info("Click on the nodes to see its attributes")


# Function to parse the XML and build the roleclass structure
def parse_roleclass_libs(xml_content):
    root = ET.fromstring(xml_content)
    namespaces = {'caex': 'http://www.dke.de/CAEX'}
    roleclass_libs = {}

    for roleclass_lib in root.findall('.//caex:RoleClassLib', namespaces):
        lib_name = roleclass_lib.get('Name')
        roleclass_libs[lib_name] = {}

        for roleclass in roleclass_lib.findall('.//caex:RoleClass', namespaces):
            role_name = roleclass.get('Name')
            ref_base_path = roleclass.get('RefBaseClassPath')
            parent = ref_base_path.split('/')[-1] if ref_base_path else None
            attributes = [attr.get('Name') for attr in roleclass.findall('.//caex:Attribute', namespaces)]

            roleclass_libs[lib_name][role_name] = {
                "description": "",
                "attributes": attributes,
                "parent": parent
            }

    return roleclass_libs


# Function to establish children relationships
def establish_children(roleclass_libs):
    parent_to_children = {}
    for lib_name, roleclasses in roleclass_libs.items():
        for role_name, details in roleclasses.items():
            parent = details['parent']
            if parent:
                if parent not in parent_to_children:
                    parent_to_children[parent] = []
                parent_to_children[parent].append(role_name)

    for lib_name, roleclasses in roleclass_libs.items():
        for role_name, details in roleclasses.items():
            details['children'] = parent_to_children.get(role_name, [])

    return roleclass_libs


# Streamlit App
st.title("RoleClass Library Viewer")
st.write("Upload an XML file containing RoleClass libraries to view the parsed data.")

uploaded_file = st.file_uploader("Choose an XML file", type="aml")

if uploaded_file is not None:
    content = uploaded_file.read()
    parsed_data = parse_roleclass_libs(content)
    enriched_data = establish_children(parsed_data)

    # Dropdown to select RoleClass Libraries
    library_names = list(enriched_data.keys())
    selected_library = st.selectbox("Select a RoleClass Library", library_names)

    if selected_library:
        st.subheader(f"Details for Library: {selected_library}")
        st.json(enriched_data[selected_library], expanded=False)
        show_common_concept(enriched_data[selected_library])

