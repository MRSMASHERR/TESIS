import pytest
from unittest.mock import MagicMock, patch
import psycopg2 # Added for specific database error mocking

from app.views.auth import show_login, hash_password
# Import show_register directly for the new tests
from app.views.public import show_register

# Test for hash_password
def test_hash_password():
    password = "testpassword123"
    hashed = hash_password(password)
    assert hashed is not None
    assert isinstance(hashed, str)
    assert hash_password(password) == hashed # Should be deterministic
    assert hash_password("anotherpassword") != hashed

# Tests for show_login
def test_show_login_valid_credentials_admin(mock_st_session_state, mock_db_connection, mock_streamlit_elements):
    mock_conn, mock_cursor = mock_db_connection

    mock_cursor.fetchone.return_value = {
        'id': 1, 'nombre': 'Admin User', 'email': 'admin@test.com',
        'tipo': 'Administrador', 'estado': True, 'fk_rol': 1
    }

    mock_streamlit_elements['form_submit_button'].return_value = True
    mock_streamlit_elements['text_input'].side_effect = ['admin@test.com', 'password123']

    show_login()

    assert mock_st_session_state.get('logged_in') is True
    assert mock_st_session_state.get('user_type') == 'Administrador'
    assert mock_st_session_state.get('user_id') == 1
    mock_streamlit_elements['success'].assert_called_once()
    mock_streamlit_elements['rerun'].assert_called_once()

def test_show_login_valid_credentials_user(mock_st_session_state, mock_db_connection, mock_streamlit_elements):
    mock_conn, mock_cursor = mock_db_connection

    mock_cursor.fetchone.side_effect = [
        None,
        {'id': 2, 'nombre': 'Test User', 'email': 'user@test.com', 'tipo': 'Usuario', 'estado': True, 'fk_rol': 2}
    ]

    mock_streamlit_elements['form_submit_button'].return_value = True
    mock_streamlit_elements['text_input'].side_effect = ['user@test.com', 'password123']

    show_login()

    assert mock_st_session_state.get('logged_in') is True
    assert mock_st_session_state.get('user_type') == 'Usuario'
    assert mock_st_session_state.get('user_id') == 2
    mock_streamlit_elements['success'].assert_called_once()
    mock_streamlit_elements['rerun'].assert_called_once()

def test_show_login_invalid_credentials(mock_st_session_state, mock_db_connection, mock_streamlit_elements):
    mock_conn, mock_cursor = mock_db_connection
    mock_cursor.fetchone.return_value = None

    mock_streamlit_elements['form_submit_button'].return_value = True
    mock_streamlit_elements['text_input'].side_effect = ['wrong@test.com', 'wrongpassword']

    show_login()

    assert mock_st_session_state.get('logged_in') is False
    mock_streamlit_elements['error'].assert_called_with(pytest.string_containing("Credenciales incorrectas"))

def test_show_login_inactive_user(mock_st_session_state, mock_db_connection, mock_streamlit_elements):
    mock_conn, mock_cursor = mock_db_connection
    mock_cursor.fetchone.return_value = {
        'id': 3, 'nombre': 'Inactive User', 'email': 'inactive@test.com',
        'tipo': 'Usuario', 'estado': False, 'fk_rol': 2
    }

    mock_streamlit_elements['form_submit_button'].return_value = True
    mock_streamlit_elements['text_input'].side_effect = ['inactive@test.com', 'password123']

    show_login()

    assert mock_st_session_state.get('logged_in') is False
    mock_streamlit_elements['error'].assert_called_with(pytest.string_containing("Usuario inactivo"))

def test_show_login_empty_fields(mock_st_session_state, mock_streamlit_elements):
    mock_streamlit_elements['form_submit_button'].return_value = True
    mock_streamlit_elements['text_input'].side_effect = ['', 'password123']
    show_login()
    mock_streamlit_elements['error'].assert_called_with("❌ Por favor complete todos los campos")

    mock_streamlit_elements['text_input'].side_effect = ['email@test.com', '']
    show_login()
    mock_streamlit_elements['error'].assert_called_with("❌ Por favor complete todos los campos")

def test_show_login_invalid_email_format(mock_st_session_state, mock_streamlit_elements):
    mock_streamlit_elements['form_submit_button'].return_value = True
    mock_streamlit_elements['text_input'].side_effect = ['invalidemail', 'password123']

    show_login()
    mock_streamlit_elements['error'].assert_called_with("❌ Formato de correo electrónico inválido")

def test_show_login_password_too_short(mock_st_session_state, mock_streamlit_elements):
    mock_streamlit_elements['form_submit_button'].return_value = True
    mock_streamlit_elements['text_input'].side_effect = ['email@test.com', 'short']

    show_login()
    mock_streamlit_elements['error'].assert_called_with("❌ La contraseña debe tener al menos 8 caracteres")


# Tests for show_register (from app.views.public)
def test_show_admin_register_form_success(mock_st_session_state, mock_db_connection, mock_streamlit_elements):
    mock_conn, mock_cursor = mock_db_connection
    mock_cursor.fetchone.return_value = {'id': 1}

    mock_streamlit_elements['form_submit_button'].return_value = True
    mock_streamlit_elements['text_input'].side_effect = [
        "Test Legal Rep", "12.345.678-K", "admin_reg@test.com",
        "Test Company Inc.", "+56912345678", "123 Test St",
        "newpassword123", "newpassword123"
    ]
    with patch('app.views.public.validar_rut') as mock_validar_rut, \
         patch('app.views.public.validar_email') as mock_validar_email, \
         patch('app.views.public.validar_telefono') as mock_validar_telefono:

        mock_validar_rut.return_value = True
        mock_validar_email.return_value = True
        mock_validar_telefono.return_value = True

        with patch('app.views.public.hash_password', side_effect=lambda p: f"hashed_{p}") as mock_hash_pw, \
             patch('app.views.auth.enviar_correo_bienvenida') as mock_send_email:
            mock_send_email.return_value = True

            show_register() # Calling the directly imported show_register

    mock_streamlit_elements['success'].assert_called_with("✅ ¡Compra Exitosa!")
    mock_conn.commit.assert_called_once()
    # mock_streamlit_elements['rerun'].assert_called_once() # Check if show_register calls rerun

def test_show_admin_register_form_password_mismatch(mock_st_session_state, mock_streamlit_elements):
    mock_streamlit_elements['form_submit_button'].return_value = True
    mock_streamlit_elements['text_input'].side_effect = [
        "Test Legal Rep", "12.345.678-K", "admin_reg@test.com",
        "Test Company Inc.", "+56912345678", "123 Test St",
        "newpassword123", "mismatchedpassword"
    ]
    with patch('app.views.public.validar_rut', return_value=True), \
         patch('app.views.public.validar_email', return_value=True), \
         patch('app.views.public.validar_telefono', return_value=True):
        show_register()

    mock_streamlit_elements['error'].assert_any_call("❌ Las contraseñas no coinciden")


def test_show_admin_register_form_missing_fields(mock_st_session_state, mock_streamlit_elements):
    mock_streamlit_elements['form_submit_button'].return_value = True
    mock_streamlit_elements['text_input'].side_effect = [
        "", "12.345.678-K", "admin_reg@test.com",
        "Test Company Inc.", "+56912345678", "123 Test St",
        "newpassword123", "newpassword123"
    ]
    show_register()
    mock_streamlit_elements['error'].assert_any_call("❌ Todos los campos son obligatorios")

def test_show_admin_register_form_invalid_rut(mock_st_session_state, mock_streamlit_elements):
    mock_streamlit_elements['form_submit_button'].return_value = True
    mock_streamlit_elements['text_input'].side_effect = [
        "Test Legal Rep", "invalid-rut", "admin_reg@test.com",
        "Test Company Inc.", "+56912345678", "123 Test St",
        "newpassword123", "newpassword123"
    ]
    with patch('app.views.public.validar_rut') as mock_validar_rut, \
         patch('app.views.public.validar_email', return_value=True), \
         patch('app.views.public.validar_telefono', return_value=True):
        mock_validar_rut.return_value = False
        show_register()
    mock_streamlit_elements['error'].assert_any_call("❌ El formato del RUT no es válido")

def test_show_admin_register_form_email_exists(mock_st_session_state, mock_db_connection, mock_streamlit_elements):
    mock_conn, mock_cursor = mock_db_connection
    mock_cursor.fetchone.return_value = {'id': 1}

    mock_streamlit_elements['form_submit_button'].return_value = True
    mock_streamlit_elements['text_input'].side_effect = [
        "Test Legal Rep", "12.345.678-K", "existing@test.com",
        "Test Company Inc.", "+56912345678", "123 Test St",
        "newpassword123", "newpassword123"
    ]
    with patch('app.views.public.validar_rut', return_value=True), \
         patch('app.views.public.validar_email', return_value=True), \
         patch('app.views.public.validar_telefono', return_value=True):
        show_register()

    mock_streamlit_elements['error'].assert_called_with("❌ Este email ya está registrado")


def test_show_admin_register_form_db_error_on_insert(mock_st_session_state, mock_db_connection, mock_streamlit_elements):
    mock_conn, mock_cursor = mock_db_connection

    # Configure execute side effect for more precise control
    original_execute = mock_cursor.execute
    def execute_side_effect(query, params=None):
        if "SELECT id FROM usuarios WHERE email = %s" in query:
            # Simulate email check: if params match the new user's email, return None (email not found)
            if params and params[0] == "new_user@test.com":
                return None
        elif "INSERT INTO usuarios" in query:
            # Simulate error on user insert
            raise psycopg2.Error("Simulated database insert error for usuarios")
        elif "INSERT INTO empresa" in query: # Or whatever the second insert is
             raise psycopg2.Error("Simulated database insert error for empresa")
        # Fallback to original execute for other queries if any
        return original_execute(query, params)

    # This setup is a bit more complex. A simpler way for this specific test might be:
    # 1. Email check: mock_cursor.fetchone.return_value = None
    # 2. First INSERT (usuarios): mock_cursor.execute.side_effect = psycopg2.Error("...")
    # Let's try to make the mock_cursor.execute side_effect more targeted.

    # Scenario: Email check passes (fetchone returns None). Then INSERT fails.
    mock_cursor.fetchone.return_value = None # For the initial "SELECT id FROM usuarios WHERE email = %s"

    # Then, the execute for INSERT fails. We need to ensure it's the INSERT.
    # The function public.show_register makes multiple execute calls.
    # 1. INSERT into empresa
    # 2. INSERT into usuarios
    # Let's assume the error happens on the first INSERT (empresa) for this test.
    # If it happens on the second, the logic would be mock_cursor.execute.side_effect = [None, psycopg2.Error(...)]

    mock_cursor.execute.side_effect = psycopg2.Error("Simulated database insert error")


    mock_streamlit_elements['form_submit_button'].return_value = True
    mock_streamlit_elements['text_input'].side_effect = [
        "Test Legal Rep", "12.345.678-K", "new_user@test.com",
        "Test Company Inc.", "+56912345678", "123 Test St",
        "newpassword123", "newpassword123"
    ]

    with patch('app.views.public.validar_rut', return_value=True), \
         patch('app.views.public.validar_email', return_value=True), \
         patch('app.views.public.validar_telefono', return_value=True), \
         patch('app.views.public.hash_password', side_effect=lambda p: f"hashed_{p}"):
        show_register()

    mock_conn.rollback.assert_called_once()
    mock_streamlit_elements['error'].assert_any_call(pytest.string_containing("Error en el proceso de registro"))
