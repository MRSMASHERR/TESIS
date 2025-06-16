import pytest
from unittest.mock import MagicMock, patch, call
from datetime import datetime, timedelta
from app.views.recovery import (
    show_recovery_page,
    show_reset_password_form,
    procesar_recuperacion,
    verificar_token,
    actualizar_password,
    enviar_correo_reset,
    # Assuming BASE_URL and EMAIL_CONFIG are top-level in recovery.py for patching if needed
    # For enviar_correo_reset test, EMAIL_CONFIG will be patched.
)
from app.views.auth import hash_password as app_hash_password # Used for consistency

# Mock database connection and streamlit elements are auto-used from conftest.py

def test_show_recovery_page_no_token(mock_streamlit_elements, mock_st_session_state):
    mock_streamlit_elements['query_params'].get = MagicMock(return_value=None)
    mock_streamlit_elements['form_submit_button'].return_value = False

    with patch('app.views.recovery.procesar_recuperacion') as mock_procesar:
        show_recovery_page()

    mock_streamlit_elements['title'].assert_called_with("🔑 Recuperación de Contraseña")
    mock_streamlit_elements['text_input'].assert_called_with("Ingresa tu correo electrónico")
    mock_streamlit_elements['form_submit_button'].assert_called_with("Recuperar Contraseña")
    mock_procesar.assert_not_called()


def test_show_recovery_page_with_valid_token(mock_streamlit_elements, mock_st_session_state):
    valid_token = "valid_token_123"
    mock_streamlit_elements['query_params'].get = MagicMock(return_value=valid_token)

    with patch('app.views.recovery.show_reset_password_form') as mock_show_reset_form:
        show_recovery_page()

    mock_show_reset_form.assert_called_once_with(valid_token)


def test_show_recovery_page_email_submit_success(mock_streamlit_elements, mock_st_session_state):
    mock_streamlit_elements['query_params'].get = MagicMock(return_value=None)
    mock_streamlit_elements['form_submit_button'].return_value = True
    mock_streamlit_elements['text_input'].return_value = "user@example.com"

    with patch('app.views.recovery.procesar_recuperacion', return_value=True) as mock_procesar:
        show_recovery_page()

    mock_procesar.assert_called_once_with("user@example.com")
    mock_streamlit_elements['success'].assert_called_with(pytest.string_containing("Se ha enviado un correo con las instrucciones"))


def test_show_recovery_page_email_submit_failure(mock_streamlit_elements, mock_st_session_state):
    mock_streamlit_elements['query_params'].get = MagicMock(return_value=None)
    mock_streamlit_elements['form_submit_button'].return_value = True
    mock_streamlit_elements['text_input'].return_value = "nonexistent@example.com"

    with patch('app.views.recovery.procesar_recuperacion', return_value=False) as mock_procesar:
        show_recovery_page()

    mock_procesar.assert_called_once_with("nonexistent@example.com")
    mock_streamlit_elements['error'].assert_called_with(pytest.string_containing("No se encontró una cuenta con ese correo"))


def test_show_reset_password_form_valid_token_submit_success(mock_db_connection, mock_streamlit_elements, mock_st_session_state):
    mock_conn, mock_cursor = mock_db_connection
    valid_token = "valid_token_abc"

    mock_streamlit_elements['form_submit_button'].return_value = True
    mock_streamlit_elements['text_input'].side_effect = ["newStrongPass123", "newStrongPass123"]

    with patch('app.views.recovery.verificar_token', return_value=True) as mock_verificar, \
         patch('app.views.recovery.actualizar_password', return_value=True) as mock_actualizar:
        show_reset_password_form(valid_token)

    mock_verificar.assert_called_once_with(valid_token)
    mock_actualizar.assert_called_once_with(valid_token, "newStrongPass123")
    mock_streamlit_elements['success'].assert_called_with(pytest.string_containing("Contraseña actualizada exitosamente"))
    assert mock_st_session_state.get('show_login') is True


def test_show_reset_password_form_invalid_token(mock_streamlit_elements, mock_st_session_state):
    invalid_token = "invalid_token_xyz"
    with patch('app.views.recovery.verificar_token', return_value=False) as mock_verificar:
        show_reset_password_form(invalid_token)

    mock_verificar.assert_called_once_with(invalid_token)
    mock_streamlit_elements['error'].assert_called_with(pytest.string_containing("El enlace de recuperación no es válido o ha expirado"))
    mock_streamlit_elements['form_submit_button'].assert_not_called()


@pytest.mark.parametrize("user_type_found", ["administrador", "usuario"])
def test_procesar_recuperacion_user_found_email_sent(mock_db_connection, user_type_found, mock_st_session_state):
    mock_conn, mock_cursor = mock_db_connection
    email_to_test = "found@example.com"
    user_data = {'id': 1, 'nombre': 'Test User', 'email': email_to_test} # Removed 'tipo' as it's not used by procesar_recuperacion directly

    if user_type_found == "administrador":
        mock_cursor.fetchone.side_effect = [user_data, None]
    else:
        mock_cursor.fetchone.side_effect = [None, user_data]

    with patch('app.views.recovery.enviar_correo_reset', return_value=True) as mock_enviar_correo:
        result = procesar_recuperacion(email_to_test)

    assert result is True
    execute_calls = mock_cursor.execute.call_args_list
    assert any("INSERT INTO reset_tokens" in str(call_args) for call_args in execute_calls)
    mock_conn.commit.assert_called_once()
    mock_enviar_correo.assert_called_once()
    assert mock_enviar_correo.call_args[0][0] == email_to_test


def test_procesar_recuperacion_user_not_found(mock_db_connection, mock_st_session_state):
    mock_conn, mock_cursor = mock_db_connection
    mock_cursor.fetchone.return_value = None

    result = procesar_recuperacion("notfound@example.com")
    assert result is False
    mock_conn.commit.assert_not_called()


def test_procesar_recuperacion_email_send_fails(mock_db_connection, mock_st_session_state):
    mock_conn, mock_cursor = mock_db_connection
    user_data = {'id': 1, 'nombre': 'Test User', 'email': 'test@example.com'}
    mock_cursor.fetchone.side_effect = [None, user_data]

    with patch('app.views.recovery.enviar_correo_reset', return_value=False) as mock_enviar_correo:
        result = procesar_recuperacion("test@example.com")

    assert result is False
    mock_conn.commit.assert_called_once()


def test_verificar_token_valid(mock_db_connection, mock_st_session_state):
    mock_conn, mock_cursor = mock_db_connection
    # Simulate token found and not expired (DB query in recovery.py handles expiration check)
    mock_cursor.fetchone.return_value = {'token': 'valid_token', 'fecha_expiracion': datetime.now() + timedelta(hours=1)}
    assert verificar_token("valid_token") is True

def test_verificar_token_invalid_or_expired(mock_db_connection, mock_st_session_state):
    mock_conn, mock_cursor = mock_db_connection
    mock_cursor.fetchone.return_value = None
    assert verificar_token("invalid_token") is False


@pytest.mark.parametrize("user_type", ["administrador", "usuario"])
def test_actualizar_password_success(mock_db_connection, user_type, mock_st_session_state):
    mock_conn, mock_cursor = mock_db_connection
    token_info = {'email': 'user@example.com', 'tipo_usuario': user_type}
    mock_cursor.fetchone.return_value = token_info

    new_password_plain = "newSecurePassword123"
    # Use app_hash_password (from auth.py) if recovery.py's hash_password is the same or not present
    # The prompt patches 'app.views.recovery.hash_password', so we assume it exists.
    hashed_new_password = "hashed_" + new_password_plain

    with patch('app.views.recovery.hash_password', return_value=hashed_new_password) as mock_hash:
        result = actualizar_password("valid_token", new_password_plain)

    assert result is True
    mock_hash.assert_called_once_with(new_password_plain)

    update_query_found = False
    correct_table_updated = False
    delete_token_query_found = False

    for call_args in mock_cursor.execute.call_args_list:
        sql = call_args[0][0]
        params = call_args[0][1]
        if "UPDATE administrador SET contrasena_admin = %s WHERE correo_admin = %s" in sql and user_type == "administrador":
            correct_table_updated = True
            assert params == (hashed_new_password, token_info['email'])
        elif "UPDATE usuario SET contrasena_user = %s WHERE correo_user = %s" in sql and user_type == "usuario":
            correct_table_updated = True
            assert params == (hashed_new_password, token_info['email'])
        elif "DELETE FROM reset_tokens WHERE token = %s" in sql: # Changed from UPDATE to DELETE
            assert params == ("valid_token",)
            delete_token_query_found = True

    assert correct_table_updated
    assert delete_token_query_found # Check if token deletion query was executed
    mock_conn.commit.assert_called_once()


def test_actualizar_password_token_not_found(mock_db_connection, mock_st_session_state):
    mock_conn, mock_cursor = mock_db_connection
    mock_cursor.fetchone.return_value = None

    result = actualizar_password("invalid_token", "newPass")
    assert result is False
    mock_conn.commit.assert_not_called()

def test_enviar_correo_reset_structure(mock_st_session_state):
    # Patch EMAIL_CONFIG used by enviar_correo_reset
    mock_email_config = {
        'sender_email': "testsender@example.com",
        'sender_password': "testpassword",
        'smtp_server': "smtp.example.com",
        'smtp_port': 587
    }
    with patch('app.views.recovery.EMAIL_CONFIG', mock_email_config), \
         patch('smtplib.SMTP') as mock_smtp:

        instance = mock_smtp.return_value
        enviar_correo_reset("receiver@example.com", "Test Receiver", "test_token_123")

        mock_smtp.assert_called_with(mock_email_config['smtp_server'], mock_email_config['smtp_port'])
        instance.starttls.assert_called_once()
        instance.login.assert_called_once_with(mock_email_config['sender_email'], mock_email_config['sender_password'])
        instance.sendmail.assert_called_once()
        instance.quit.assert_called_once()

        args, _ = instance.sendmail.call_args
        assert args[0] == mock_email_config['sender_email']
        assert args[1] == "receiver@example.com"
        assert "Recuperación de Contraseña - GreenIA" in args[2]
        assert "test_token_123" in args[2]
        assert "Hola Test Receiver" in args[2]
