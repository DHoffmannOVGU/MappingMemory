import streamlit as st
import json
import pandas as pd
import xml.etree.ElementTree as ET
from xml.dom.minidom import parseString
import dicttoxml
from streamlit_condition_tree import condition_tree, config_from_dataframe

# Define the schemas
schemas = {
    "entity": {
        "description": "A general entity with no specific type.",
    },
    "person": {
        "description": "A person, can be a pupil or teacher.",
    },
    "pupil": {
        "description": "A person who is a pupil.",
    },
    "teacher": {
        "description": "A person who is a teacher.",
    },
    "pet": {
        "description": "An entity that is a pet.",
    }
}

# Sample Data
samples = {
    1: [
        {
            "name": "John Doe",
            "type": "person",
            "age": 25,
            "role": ""
        },
        {
            "name": "Jane Doe",
            "type": "person",
            "age": 30,
            "role": "teacher"
        }
    ],
    2: [
        {
            "name": "Max",
            "type": "pet",
            "species": "dog",
            "age": 5
        },
        {
            "name": "Bella",
            "type": "pet",
            "species": "cat",
            "age": 3
        }
    ]
}

sample_metadata = {
    1: {
        "description": "Sample data with information about pupils and teachers.",
        "schema_example1": "person",
        "schema_rule1": "type == 'person'",
        "schema_example2": "teacher",
        "schema_rule2": "role == 'teacher'"
    },
    2: {
        "description": "Sample data with information about pets.",
        "schema_example1": "pet",
        "schema_rule1": "type == 'pet'",
        "schema_example2": "dog",
        "schema_rule2": "species == 'dog'"
    }
}

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
        st.subheader("Select a sample to work with:")
        sample_selection = st.selectbox(
            "Choose a sample:",
            list(samples.keys())
        )
        st.session_state["current_question"] = sample_selection

        st.title("Schema Selection")
        st.write("Select the appropriate schema for the JSON data:")
        st.write(list(schemas.keys()))


def main():
    st.title("Mapping Memory Game")

    # Get the selected sample
    selected_sample = samples[st.session_state["current_question"]]

    # Convert the selected sample to different formats
    xml_data = dict_to_xml(selected_sample)
    df = pd.DataFrame(selected_sample)

    # Display the selected sample data
    st.header(f"Sample Data: {st.session_state["current_question"]}")
    json_tab, xml_tab, df_tab = st.tabs(["JSON", "XML", "CSV/Excel"])

    with json_tab:
        st.json(selected_sample)

    with xml_tab:
        st.code(xml_data, language='xml')

    with df_tab:
        st.dataframe(df, use_container_width=True)

    sample1_col, sample2_col = st.columns(2)
    # User selects the appropriate schema
    selected_schema_1 = sample1_col.selectbox(
        "Select the appropriate schema for the first entry:",
        list(schemas.keys())
    )
    selected_schema_2 = sample2_col.selectbox(
        "Select the appropriate schema for the second entry:",
        list(schemas.keys())
    )

    # Add logic for user feedback
    if st.button("Validate", use_container_width=True, type="primary"):
        # Get the solution schema
        solution_schema1 = sample_metadata[st.session_state["current_question"]]["schema_example1"]
        solution_schema2 = sample_metadata[st.session_state["current_question"]]["schema_example2"]
        # Check if the user selected the correct schema
        if selected_schema_1 == solution_schema1 and selected_schema_2 == solution_schema2:
            st.success("Correct! You have successfully matched the schemas.")
            st.session_state["current_score"] += 1
        else:
            st.error("Incorrect! Please try again.")


    # Basic field configuration from dataframe
    config = config_from_dataframe(df)

    # Condition tree
    query_string = condition_tree(config, min_height=200, always_show_buttons=True, placeholder="Click the buttons top right to build query")
    st.write(query_string)

    # Filtered dataframe
    filtered_df = df.query(query_string)
    st.dataframe(filtered_df, use_container_width=True)


def rule_matcher():
    pass


session_states = {
    "current_question": 0,
    "current_score": 0,
    "game_over": False,
}

if __name__ == "__main__":
    for session_state in session_states:
        if session_state not in st.session_state:
            st.session_state[session_state] = session_states[session_state]

    sidebar_init()
    main()
    rule_matcher()
