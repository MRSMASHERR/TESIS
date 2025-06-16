import pytest
from unittest.mock import MagicMock, patch
from app.views.user import (
    show_user_panel,
    show_user_home,
    show_recognition,
    show_user_profile,
    guardar_reconocimiento
)
# Mock database connection and streamlit elements are auto-used from conftest.py

def test_show_user_panel(mock_st_session_state, mock_streamlit_elements):
    mock_st_session_state['user_type'] = "Usuario"
    mock_st_session_state['user_id'] = 10
    mock_st_session_state['user_name'] = "Test User" # user_name is used in show_user_home

    with patch('app.views.user.show_user_home') as mock_home, \
         patch('app.views.user.show_recognition') as mock_recognition, \
         patch('app.views.user.show_user_profile') as mock_profile:

        show_user_panel()

        mock_streamlit_elements['tabs'].assert_called_once_with([
            "🏠 Inicio",
            "📸 Reconocimiento",
            "👤 Mi Perfil"
        ])

        mock_home.assert_called_once()
        mock_recognition.assert_called_once()
        mock_profile.assert_called_once()


def test_show_user_home_with_data(mock_st_session_state, mock_db_connection, mock_streamlit_elements):
    mock_conn, mock_cursor = mock_db_connection
    mock_st_session_state['user_id'] = 10
    mock_st_session_state['user_name'] = "TestUserName"

    stats_data = {'total_botellas': 100, 'total_co2': 50.0}
    activities_data = [
        {'fecha_reconocimiento': MagicMock(strftime=lambda fmt: "01/01/2023 10:00"), 'nombre_plastico': 'PET', 'cantidad_plastico': 10, 'cantidad_co2_plastico': 5.0},
        {'fecha_reconocimiento': MagicMock(strftime=lambda fmt: "02/01/2023 11:00"), 'nombre_plastico': 'HDPE', 'cantidad_plastico': 5, 'cantidad_co2_plastico': 2.5},
    ]
    mock_cursor.fetchone.return_value = stats_data
    mock_cursor.fetchall.return_value = activities_data

    show_user_home()

    mock_streamlit_elements['title'].assert_called_with("🏠 Inicio")
    mock_streamlit_elements['write'].assert_any_call(f"👋 Bienvenido, {mock_st_session_state['user_name']}")

    mock_streamlit_elements['write'].assert_any_call("Total Reciclado")
    mock_streamlit_elements['write'].assert_any_call("### 100 botellas")
    mock_streamlit_elements['write'].assert_any_call("Impacto CO2")
    mock_streamlit_elements['write'].assert_any_call("### 50.00 kg")

    assert mock_streamlit_elements['info'].call_count == 2
    mock_streamlit_elements['info'].assert_any_call(pytest.string_containing("📅 01/01/2023 10:00"))
    mock_streamlit_elements['info'].assert_any_call(pytest.string_containing("- Tipo: PET"))

def test_show_user_home_no_activities(mock_st_session_state, mock_db_connection, mock_streamlit_elements):
    mock_conn, mock_cursor = mock_db_connection
    mock_st_session_state['user_id'] = 10
    mock_st_session_state['user_name'] = "TestUserName"

    stats_data = {'total_botellas': 0, 'total_co2': 0.0}
    mock_cursor.fetchone.return_value = stats_data
    mock_cursor.fetchall.return_value = []

    show_user_home()
    mock_streamlit_elements['info'].assert_called_once_with("No hay reconocimientos registrados aún")


def test_show_recognition_calls_mostrar_reconocimiento(mock_st_session_state, mock_streamlit_elements):
    mock_st_session_state['user_name'] = "Test User Recogn" # Corrected: user_name for mostrar_reconocimiento_residuos
    mock_st_session_state['user_id'] = 11

    with patch('app.views.user.mostrar_reconocimiento_residuos') as mock_mostrar_rec:
        show_recognition()

    mock_streamlit_elements['title'].assert_called_with("📸 Reconocimiento")
    mock_mostrar_rec.assert_called_once_with(mock_st_session_state['user_name'])


def test_show_user_profile_loads_data(mock_st_session_state, mock_db_connection, mock_streamlit_elements):
    mock_conn, mock_cursor = mock_db_connection
    mock_st_session_state['user_id'] = 10
    # user.py:show_user_profile gets username and email from database based on user_id
    # So, we don't need to set 'username' or 'email' in session_state for loading,
    # but the mocked DB return for user details should provide them.

    user_details_data = {'nombre_usuario': "UserProfileTest", 'correo_user': "userprofile@test.com"}
    stats_data = {'total_reconocimientos': 50, 'total_botellas': 200, 'total_co2': 100.0}

    # First fetchone for user details, second for stats
    mock_cursor.fetchone.side_effect = [user_details_data, stats_data]

    with patch('streamlit.form', MagicMock()) as mock_form_constructor:
        mock_form_instance = MagicMock()
        mock_form_instance.__enter__.return_value = None
        mock_form_instance.__exit__.return_value = (None, None, None)
        mock_form_constructor.return_value = mock_form_instance
        show_user_profile()

    mock_streamlit_elements['title'].assert_called_with("👤 Mi Perfil")

    assert mock_cursor.execute.call_count == 2
    mock_cursor.execute.assert_any_call(
        pytest.string_containing("SELECT nombre_usuario, correo_user FROM usuario WHERE id_usuario = %s"), (10,)
    )
    mock_cursor.execute.assert_any_call(
        pytest.string_containing("SELECT COUNT(*) as total_reconocimientos"), (10,)
    )

    mock_streamlit_elements['write'].assert_any_call(f"**Usuario:** {user_details_data['nombre_usuario']}")
    mock_streamlit_elements['write'].assert_any_call(f"**Nivel:** Experto 🌳")
    mock_streamlit_elements['metric'].assert_any_call("Total Botellas", "200")
    mock_streamlit_elements['metric'].assert_any_call("Impacto CO2", "100.00 kg")


def test_show_user_profile_change_password_success(mock_st_session_state, mock_db_connection, mock_streamlit_elements):
    mock_conn, mock_cursor = mock_db_connection
    mock_st_session_state['user_id'] = 10

    user_details_data = {'nombre_usuario': "Test User", 'correo_user': "test@example.com"}
    stats_data = {'total_reconocimientos': 5, 'total_botellas': 5, 'total_co2': 2.5}
    current_password_data = {'contrasena_user': 'current_pass_plain'}

    mock_cursor.fetchone.side_effect = [user_details_data, stats_data, current_password_data]

    mock_streamlit_elements['form_submit_button'].return_value = True
    mock_streamlit_elements['text_input'].side_effect = [
        'current_pass_plain', 'new_pass123', 'new_pass123'
    ]

    show_user_profile()

    assert mock_cursor.execute.call_count == 3
    mock_cursor.execute.assert_any_call(
        pytest.string_containing("SELECT contrasena_user FROM usuario WHERE id_usuario = %s"), (10,)
    )
    mock_cursor.execute.assert_any_call(
        pytest.string_containing("UPDATE usuario SET contrasena_user = %s WHERE id_usuario = %s"),
        ('new_pass123', 10)
    )
    mock_conn.commit.assert_called_once()
    mock_streamlit_elements['success'].assert_called_with("¡Contraseña actualizada exitosamente!")


def test_show_user_profile_change_password_current_incorrect(mock_st_session_state, mock_db_connection, mock_streamlit_elements):
    mock_conn, mock_cursor = mock_db_connection
    mock_st_session_state['user_id'] = 10

    user_details_data = {'nombre_usuario': "Test User", 'correo_user': "test@example.com"}
    stats_data = {'total_reconocimientos': 5, 'total_botellas': 5, 'total_co2': 2.5}
    current_password_data = {'contrasena_user': 'correct_current_pass'}

    mock_cursor.fetchone.side_effect = [user_details_data, stats_data, current_password_data]

    mock_streamlit_elements['form_submit_button'].return_value = True
    mock_streamlit_elements['text_input'].side_effect = [
        'wrong_current_pass', 'new_pass123', 'new_pass123'
    ]

    show_user_profile()
    mock_streamlit_elements['error'].assert_called_with("La contraseña actual es incorrecta")
    mock_conn.commit.assert_not_called()


def test_show_user_profile_change_password_mismatch_new(mock_st_session_state, mock_db_connection, mock_streamlit_elements):
    mock_conn, mock_cursor = mock_db_connection
    mock_st_session_state['user_id'] = 10

    user_details_data = {'nombre_usuario': "Test User", 'correo_user': "test@example.com"}
    stats_data = {'total_reconocimientos': 5, 'total_botellas': 5, 'total_co2': 2.5}

    # Only user details and stats queries will run if validation fails early
    mock_cursor.fetchone.side_effect = [user_details_data, stats_data]

    mock_streamlit_elements['form_submit_button'].return_value = True
    mock_streamlit_elements['text_input'].side_effect = [
        'current_pass', 'new_pass123', 'mismatched_new_pass'
    ]

    show_user_profile()
    mock_streamlit_elements['error'].assert_called_with("Las contraseñas nuevas no coinciden")


def test_show_user_profile_change_password_too_short(mock_st_session_state, mock_db_connection, mock_streamlit_elements):
    mock_conn, mock_cursor = mock_db_connection
    mock_st_session_state['user_id'] = 10

    user_details_data = {'nombre_usuario': "Test User", 'correo_user': "test@example.com"}
    stats_data = {'total_reconocimientos': 5, 'total_botellas': 5, 'total_co2': 2.5}
    mock_cursor.fetchone.side_effect = [user_details_data, stats_data]

    mock_streamlit_elements['form_submit_button'].return_value = True
    mock_streamlit_elements['text_input'].side_effect = [
        'current_pass', 'short', 'short'
    ]

    show_user_profile()
    mock_streamlit_elements['error'].assert_called_with("La nueva contraseña debe tener al menos 8 caracteres")

def test_guardar_reconocimiento_success(mock_st_session_state, mock_db_connection):
    mock_conn, mock_cursor = mock_db_connection
    mock_st_session_state['user_id'] = 10
    mock_st_session_state['admin_id'] = 1 # As user.py's guardar_reconocimiento takes admin_id

    mock_cursor.fetchone.return_value = {'id_reconocimiento': 100}

    success, rec_id = guardar_reconocimiento(
        plastico_id=1, peso=0.5, cantidad=10, co2=0.25,
        usuario_id=mock_st_session_state['user_id'],
        admin_id=mock_st_session_state['admin_id']
    )

    assert success is True
    assert rec_id == 100
    mock_cursor.execute.assert_called_once_with(
        pytest.string_containing("INSERT INTO reconocimiento"),
        (1, 0.5, 10, 0.25, mock_st_session_state['user_id'], mock_st_session_state['admin_id'])
    )
    mock_conn.commit.assert_called_once()


def test_guardar_reconocimiento_db_error(mock_st_session_state, mock_db_connection, mock_streamlit_elements):
    mock_conn, mock_cursor = mock_db_connection
    mock_st_session_state['user_id'] = 10
    mock_st_session_state['admin_id'] = 1

    mock_cursor.execute.side_effect = Exception("DB Error")

    success, rec_id = guardar_reconocimiento(1, 0.5, 10, 0.25, 10, 1)

    assert success is False
    assert rec_id is None
    mock_conn.rollback.assert_called_once()
    mock_streamlit_elements['error'].assert_called_with("Error al guardar reconocimiento: DB Error")
