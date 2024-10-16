import streamlit as st
import json
import pandas as pd
import xml.etree.ElementTree as ET
from xml.dom.minidom import parseString
import dicttoxml
from streamlit_condition_tree import condition_tree, config_from_dataframe
from riddle_data import samples, sample_solutions
from st_cytoscape import cytoscape
from schemas import person_schema
from uuid import uuid4

schema = person_schema

#Import mappingmemory.png as image



# schema to cytoscape graph
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
cytoscape_graph = schema_to_cytoscape(schema)


# Convert sample data to XML
def dict_to_xml(data):
    def entity_func(parent):
        if parent is (None or ""):
            return 'entities'
        return 'entity'

    xml_data = dicttoxml.dicttoxml(data, custom_root='entities', attr_type=False, item_func=entity_func)
    dom = parseString(xml_data)
    return dom.toprettyxml(indent="  ")


def sidebar_init():
    # User selects the sample
    with st.sidebar:
        st.image("mapping_memory.png")
        st.subheader("Select a sample to work with:")
        sample_selection = st.selectbox(
            "Choose a sample:",
            list(samples.keys()),
            disabled=True
        )
        st.session_state["current_question"] = sample_selection
        back_btn_col, forward_btn_col = st.columns(2)
        #
        if back_btn_col.button(":arrow_backward:", use_container_width=True):
            st.session_state["current_question"] -= 1
        if forward_btn_col.button(":arrow_forward:", use_container_width=True):
            st.session_state["current_question"] += 1


def show_common_concept():
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


def main():
    st.title("Mapping Memory")
    show_common_concept()

    # Get the selected sample
    selected_sample = samples[st.session_state["current_question"]]

    with st.expander("Step 1: Investigate Raw data", expanded=False):
        # Convert the selected sample to different formats
        xml_data = dict_to_xml(selected_sample)
        df = pd.DataFrame(selected_sample)

        # Display the selected sample data
        # st.header(f'Sample Data: {st.session_state["current_question"]}')
        xml_tab, json_tab, df_tab = st.tabs(["Data as XML", "Simplified to JSON", "Even simpler as Excel"])

        with xml_tab:
            st.code(xml_data, language='xml')

        with json_tab:
            st.json(selected_sample)

        with df_tab:
            st.dataframe(df, use_container_width=True)

    with st.expander("Step 2: Match Schema", expanded=False):
        from schemas import person_schema
        schema = person_schema
        sample1_col, sample2_col, sample3_col = st.columns(3)
        # User selects the appropriate schema
        selected_schema_1 = sample1_col.selectbox(
            "Select the appropriate schema for the first entry:",
            list(schema.keys())
        )
        selected_schema_2 = sample2_col.selectbox(
            "Select the appropriate schema for the second entry:",
            list(schema.keys())
        )
        selected_schema_3 = sample3_col.selectbox(
            "Select the appropriate schema for the third entry:",
            list(schema.keys())
        )
        found_schemas = [selected_schema_1, selected_schema_2, selected_schema_3]
        # Delete Duplicates

        found_schemas = list(dict.fromkeys(found_schemas))
        st.session_state["found_schemas"] = found_schemas

        # Add logic for user feedback
        if st.button("Validate", use_container_width=True, type="primary"):
            # Get the solution schema
            current_schema_solutions = list(sample_solutions[st.session_state["current_question"]].keys())
            column_list = st.columns(len(st.session_state["found_schemas"]))

            # Check if the user selected the correct schema
            for i, selected_solution in enumerate(st.session_state["found_schemas"]):
                if current_schema_solutions[i] == selected_solution:
                    column_list[i].success(f"Correct schema for Entry {i + 1}")
                else:
                    column_list[i].error(f"Incorrect schema for Entry {i + 1}")

    with st.expander("Step 3: Build the Mapping Rules", expanded=False):
        selected_schema = st.selectbox(
            "Select the concept for which you want to derive the rule:",
            st.session_state["found_schemas"])
        st.subheader("Concept Rule Builder")
        # Display the query builder
        # Basic field configuration from dataframe
        config = config_from_dataframe(df)

        # Condition tree
        query_string = condition_tree(config, min_height=250, always_show_buttons=True,
                                      placeholder='Click  "Add Rule" top right to build the mapping rule')
        st.write(query_string)
        current_schema_solutions = sample_solutions[st.session_state["current_question"]]
        if st.button("Try Query", type="primary", use_container_width=True):
            # Filtered dataframe
            st.session_state.schema_rules[selected_schema] = query_string

        column_list = st.columns(len(st.session_state["found_schemas"]))

        #st.write(st.session_state["found_schemas"])


        for i, schema in enumerate(st.session_state["found_schemas"]):
            if schema not in st.session_state["schema_rules"]:
                column_list[i].info(f"No rule yet for {schema}")
            elif st.session_state["schema_rules"][schema] in current_schema_solutions.get(schema).get("rule"):
                column_list[i].success(f"Correct rule for {schema}")
            else:
                column_list[i].error(f"Incorrect rule for {schema}")

    with st.expander("Step 4: Match common concept to data", expanded=False):
        selected_schema_2 = st.selectbox(
            "Select the appropriate schema for the data:",
            st.session_state["found_schemas"])
        try:
            filtered_df = df.query(st.session_state["schema_rules"].get(selected_schema_2))
        except:
            filtered_df = df
        cleaned_df = filtered_df.dropna(axis=1, how='all')
        st.dataframe(cleaned_df, use_container_width=True)
        data_attribute_list = cleaned_df.columns
        schema_attribute_list = person_schema[selected_schema_2]["attributes"]
        #Define a new df with 2 columns: first the schema attributes with its entries, then the data attributes with its entries
        matched_data = {"Concept Data": schema_attribute_list, "Data Attr": [""] * len(schema_attribute_list)}
        df = pd.DataFrame(data=matched_data)
        mapped_df = st.data_editor(df,
                       use_container_width=True,
                       column_config={
                            "Data Attr": st.column_config.SelectboxColumn(
                            label = "Choose the appropriate mapping",
                            help="Choose the appropriate mapping",
                            options=data_attribute_list,
                            ),
                       },
                       disabled=["Concept Data"]
                       )

        if st.button("Validate Mapping", use_container_width=True, type="primary"):
            # Get the solution schema
            current_schema_solutions = sample_solutions[st.session_state["current_question"]]
            # Derive mapping dict from columns
            mapping = dict(zip(mapped_df["Concept Data"], mapped_df["Data Attr"]))
            #Compare dicts
            st.session_state["schema_attribute_rules"][selected_schema_2] = mapping
            #st.write(st.session_state["schema_attribute_rules"][selected_schema_2])
            attribute_mapping_solution =    current_schema_solutions.get(selected_schema_2).get("attributes")
            # st.write(attribute_mapping_solution)


        column_list = st.columns(len(st.session_state["found_schemas"]))
        st.session_state.matched_entries = 0
        for i, schema in enumerate(st.session_state["found_schemas"]):
            try:
                attribute_mapping_solution = current_schema_solutions.get(schema).get("attributes")
                if schema not in st.session_state["schema_attribute_rules"]:
                    column_list[i].info(f"No rule yet for {schema}")
                    st.session_state.matched_entries += 0
                elif st.session_state["schema_attribute_rules"][schema] == attribute_mapping_solution:
                    column_list[i].success(f"Correct rule for {schema}")
                    st.session_state.matched_entries += 1
                else:
                    column_list[i].error(f"Incorrect rule for {schema}")
                    st.session_state.matched_entries -=1
            except:
                column_list[i].error(f"Incorrect rule for {schema}")
                st.session_state.matched_entries -= 1

    if st.button("Click to see if you completed the level", use_container_width=True):
        if st.session_state.matched_entries == 3:
            st.balloons()

    with st.expander("Step 5: Export the Data", expanded=False):
        pass



session_states = {
    "current_question": 1,
    "current_score": 0,
    "game_over": False,
    "schema_rules": {},
    "schema_attribute_rules": {},
    "found_schemas": [],
    "matched_entries": 0

}

if __name__ == "__main__":
    st.set_page_config(page_title="Mapping Memory", page_icon="🧠")
    for session_state in session_states:
        if session_state not in st.session_state:
            st.session_state[session_state] = session_states[session_state]
    sidebar_init()
    main()
