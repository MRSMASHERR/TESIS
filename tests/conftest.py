import pytest
import streamlit as st
from unittest.mock import MagicMock, patch

@pytest.fixture
def mock_db_connection():
    """Fixture to mock the database connection."""
    mock_conn = MagicMock()
    mock_cursor = MagicMock()
    mock_conn.cursor.return_value = mock_cursor
    mock_cursor.fetchone.return_value = None  # Default to no result
    mock_cursor.fetchall.return_value = []    # Default to no results

    # You can customize default return values for specific tests if needed
    # e.g., mock_cursor.fetchone.return_value = {'id': 1, 'name': 'Test User'}

    return mock_conn, mock_cursor

@pytest.fixture(autouse=True)
def mock_st_session_state():
    """Fixture to mock Streamlit's session state."""
    # Using a dictionary to simulate st.session_state
    # Streamlit's SessionState is a dict-like object
    session_state_dict = {}

    with patch('streamlit.session_state', session_state_dict):
        with patch('app.database.get_db_connection') as mock_get_db:
            # Ensure get_db_connection is also patched globally for views
            # that might import it directly
            mock_conn, _ = mock_db_connection() # We only need the conn part here for get_db_connection
            mock_get_db.return_value = mock_conn
            yield session_state_dict


@pytest.fixture
def mock_streamlit_elements():
    """Mocks common Streamlit UI elements to prevent errors during tests."""
    with patch('streamlit.title') as mock_title, \
         patch('streamlit.subheader') as mock_subheader, \
         patch('streamlit.write') as mock_write, \
         patch('streamlit.text_input') as mock_text_input, \
         patch('streamlit.form') as mock_form, \
         patch('streamlit.form_submit_button') as mock_form_submit_button, \
         patch('streamlit.error') as mock_error, \
         patch('streamlit.success') as mock_success, \
         patch('streamlit.warning') as mock_warning, \
         patch('streamlit.info') as mock_info, \
         patch('streamlit.tabs') as mock_tabs, \
         patch('streamlit.rerun') as mock_rerun, \
         patch('streamlit.expander') as mock_expander, \
         patch('streamlit.markdown') as mock_markdown, \
         patch('streamlit.selectbox') as mock_selectbox, \
         patch('streamlit.checkbox') as mock_checkbox, \
         patch('streamlit.date_input') as mock_date_input, \
         patch('streamlit.metric') as mock_metric, \
         patch('streamlit.bar_chart') as mock_bar_chart, \
         patch('streamlit.dataframe') as mock_dataframe, \
         patch('streamlit.plotly_chart') as mock_plotly_chart, \
         patch('streamlit.download_button') as mock_download_button, \
         patch('streamlit.camera_input') as mock_camera_input, \
         patch('streamlit.file_uploader') as mock_file_uploader, \
         patch('streamlit.image') as mock_image, \
         patch('streamlit.spinner') as mock_spinner, \
         patch('streamlit.radio') as mock_radio, \
         patch('streamlit.button') as mock_button, \
         patch('streamlit.set_page_config') as mock_set_page_config, \
         patch('streamlit.query_params') as mock_query_params:

        # Mock st.form to return a context manager
        mock_form.return_value.__enter__.return_value = None
        mock_form.return_value.__exit__.return_value = None

        mock_expander.return_value.__enter__.return_value = None
        mock_expander.return_value.__exit__.return_value = None

        mock_spinner.return_value.__enter__.return_value = None
        mock_spinner.return_value.__exit__.return_value = None

        # Mock st.tabs to return a list of mock tab objects
        mock_tab = MagicMock()
        mock_tab.__enter__.return_value = None
        mock_tab.__exit__.return_value = None
        mock_tabs.return_value = [mock_tab, mock_tab, mock_tab, mock_tab] # Adjust number as needed

        # Mock st.query_params to behave like a dictionary
        mock_query_params_dict = {}
        mock_query_params.get = mock_query_params_dict.get
        mock_query_params.clear = mock_query_params_dict.clear
        # If direct attribute access is used (e.g., st.query_params.token):
        # You might need to mock specific attributes if your code uses them:
        # from unittest.mock import PropertyMock
        # type(mock_query_params).token = PropertyMock(return_value=None)
        # However, .get() is more common.

        yield {
            "title": mock_title,
            "subheader": mock_subheader,
            "write": mock_write,
            "text_input": mock_text_input,
            "form": mock_form,
            "form_submit_button": mock_form_submit_button,
            "error": mock_error,
            "success": mock_success,
            "warning": mock_warning,
            "info": mock_info,
            "tabs": mock_tabs,
            "rerun": mock_rerun,
            "expander": mock_expander,
            "markdown": mock_markdown,
            "selectbox": mock_selectbox,
            "checkbox": mock_checkbox,
            "date_input": mock_date_input,
            "metric": mock_metric,
            "bar_chart": mock_bar_chart,
            "dataframe": mock_dataframe,
            "plotly_chart": mock_plotly_chart,
            "download_button": mock_download_button,
            "camera_input": mock_camera_input,
            "file_uploader": mock_file_uploader,
            "image": mock_image,
            "spinner": mock_spinner,
            "radio": mock_radio,
            "button": mock_button,
            "set_page_config": mock_set_page_config,
            "query_params": mock_query_params
        }

# It's important that app.database.get_db_connection is patched
# for all tests that interact with view functions.
# The mock_st_session_state fixture already does this,
# but if you have tests that don't use session_state but still call db,
# you might need a separate autouse fixture or apply the patch directly.
