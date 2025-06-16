import pytest
from unittest.mock import MagicMock, patch, call
from datetime import date # Added for report tests

from app.views.admin import (
    show_admin_panel,
    show_admin_profile,
    mostrar_lista_usuarios,
    crear_usuario,
    actualizar_usuario,
    mostrar_reportes,
    PLASTIC_TYPE_NAMES, # Added for report tests
    # Helper functions if they need direct testing, though mostly tested via parent functions
    # validar_numero_telefono, # Usually tested via crear_usuario or similar
    # validar_rut,             # Usually tested via crear_usuario or similar
)
from app.views.auth import hash_password # Used in profile password change

# Mock database connection and streamlit elements are auto-used from conftest.py

def test_show_admin_panel(mock_st_session_state, mock_streamlit_elements):
    mock_st_session_state['user_type'] = "Administrador"
    mock_st_session_state['user_id'] = 1

    with patch('app.views.admin.mostrar_lista_usuarios') as mock_lista, \
         patch('app.views.admin.crear_usuario') as mock_crear, \
         patch('app.views.admin.actualizar_usuario') as mock_actualizar, \
         patch('app.views.admin.mostrar_reportes') as mock_reportes:
        show_admin_panel()
        mock_streamlit_elements['tabs'].assert_called_once_with([
            "📋 Lista de Usuarios", "➕ Crear Usuario", "🔄 Actualizar Usuario", "📊 Reportes"
        ])
        mock_lista.assert_called_once()
        mock_crear.assert_called_once()
        mock_actualizar.assert_called_once()
        mock_reportes.assert_called_once()

def test_show_admin_profile_loads_data(mock_st_session_state, mock_db_connection, mock_streamlit_elements):
    mock_conn, mock_cursor = mock_db_connection
    mock_st_session_state['user_id'] = 1
    mock_st_session_state['user_type'] = "Administrador"
    admin_data = {
        'nombre_administrador': 'Admin Test', 'rut_admin': '12345678-9',
        'correo_admin': 'admin@test.com', 'nombre_empresa': 'Test Corp',
        'numero_administrador': '+56900000000', 'direccion_administrador': '123 Admin St',
        'numero_licencia': 10
    }
    mock_cursor.fetchone.return_value = admin_data
    with patch('streamlit.form', MagicMock()) as mock_form_constructor:
        mock_form_instance = MagicMock()
        mock_form_instance.__enter__.return_value = None
        mock_form_instance.__exit__.return_value = (None, None, None)
        mock_form_constructor.return_value = mock_form_instance
        show_admin_profile()
    mock_streamlit_elements['title'].assert_called_with("👤 Mi Perfil de Administrador")
    mock_cursor.execute.assert_called_once_with(
        pytest.string_containing("SELECT a.*, e.nombre_empresa FROM administrador a"), (1,)
    )
    mock_streamlit_elements['write'].assert_any_call(f"**Nombre:** {admin_data['nombre_administrador']}")
    mock_streamlit_elements['info'].assert_any_call(f"Licencias disponibles: {admin_data['numero_licencia']}")

def test_show_admin_profile_change_password_success(mock_st_session_state, mock_db_connection, mock_streamlit_elements):
    mock_conn, mock_cursor = mock_db_connection
    mock_st_session_state['user_id'] = 1
    mock_st_session_state['user_type'] = "Administrador"
    mock_cursor.fetchone.side_effect = [
        {'nombre_administrador': 'Admin Test', 'rut_admin': '12345678-9', 'correo_admin': 'admin@test.com', 'nombre_empresa': 'Test Corp', 'numero_administrador': '+56900000000', 'direccion_administrador': '123 Admin St', 'numero_licencia': 10},
        {'id_administrador': 1}
    ]
    mock_streamlit_elements['form_submit_button'].side_effect = [True, False]
    mock_streamlit_elements['text_input'].side_effect = [
        'current_pass', 'new_pass123', 'new_pass123',
        '+56900000000', 'admin@test.com', '123 Admin St',
    ]
    with patch('app.views.admin.hash_password') as mock_hash:
        mock_hash.side_effect = lambda p: f"hashed_{p}"
        show_admin_profile()
    expected_hash_current = "hashed_current_pass"
    expected_hash_new = "hashed_new_pass123"
    assert mock_cursor.execute.call_count == 3
    mock_cursor.execute.assert_any_call(pytest.string_containing("SELECT id_administrador FROM administrador WHERE id_administrador = %s AND contrasena_admin = %s"),(1, expected_hash_current))
    mock_cursor.execute.assert_any_call(pytest.string_containing("UPDATE administrador SET contrasena_admin = %s WHERE id_administrador = %s"),(expected_hash_new, 1))
    mock_conn.commit.assert_called_once()
    mock_streamlit_elements['success'].assert_called_with("✅ Contraseña actualizada exitosamente")

def test_show_admin_profile_change_password_mismatch(mock_st_session_state, mock_db_connection, mock_streamlit_elements):
    mock_conn, mock_cursor = mock_db_connection
    mock_st_session_state['user_id'] = 1
    mock_st_session_state['user_type'] = "Administrador"
    mock_cursor.fetchone.return_value = {'nombre_administrador': 'Admin Test', 'rut_admin': '12345678-9', 'correo_admin': 'admin@test.com', 'nombre_empresa': 'Test Corp', 'numero_administrador': '+56900000000', 'direccion_administrador': '123 Admin St', 'numero_licencia': 10}
    mock_streamlit_elements['form_submit_button'].side_effect = [True, False]
    mock_streamlit_elements['text_input'].side_effect = ['current_pass', 'new_pass123', 'wrong_confirm_pass', '+56900000000', 'admin@test.com', '123 Admin St']
    show_admin_profile()
    mock_streamlit_elements['error'].assert_called_with("Las contraseñas nuevas no coinciden")
    mock_conn.commit.assert_not_called()

def test_show_admin_profile_change_password_current_incorrect(mock_st_session_state, mock_db_connection, mock_streamlit_elements):
    mock_conn, mock_cursor = mock_db_connection
    mock_st_session_state['user_id'] = 1
    mock_st_session_state['user_type'] = "Administrador"
    mock_cursor.fetchone.side_effect = [
        {'nombre_administrador': 'Admin Test', 'rut_admin': '12345678-9', 'correo_admin': 'admin@test.com', 'nombre_empresa': 'Test Corp', 'numero_administrador': '+56900000000', 'direccion_administrador': '123 Admin St', 'numero_licencia': 10}, None
    ]
    mock_streamlit_elements['form_submit_button'].side_effect = [True, False]
    mock_streamlit_elements['text_input'].side_effect = ['wrong_current_pass', 'new_pass123', 'new_pass123', '+56900000000', 'admin@test.com', '123 Admin St']
    with patch('app.views.admin.hash_password') as mock_hash:
        mock_hash.side_effect = lambda p: f"hashed_{p}"
        show_admin_profile()
    mock_streamlit_elements['error'].assert_called_with("❌ Contraseña actual incorrecta")
    mock_conn.commit.assert_not_called()

def test_show_admin_profile_update_info_success(mock_st_session_state, mock_db_connection, mock_streamlit_elements):
    mock_conn, mock_cursor = mock_db_connection
    mock_st_session_state['user_id'] = 1
    mock_st_session_state['user_type'] = "Administrador"
    initial_admin_data = {'nombre_administrador': 'Admin Old Name', 'rut_admin': '12345678-9', 'correo_admin': 'old_admin@test.com', 'nombre_empresa': 'Old Corp', 'numero_administrador': '+56911111111', 'direccion_administrador': '1 Old St', 'numero_licencia': 5}
    mock_cursor.fetchone.return_value = initial_admin_data
    mock_streamlit_elements['form_submit_button'].side_effect = [False, True]
    new_phone, new_email, new_address = "+56922222222", "new_admin@test.com", "2 New St"
    mock_streamlit_elements['text_input'].side_effect = ['dummy_current_pass', 'dummy_new_pass', 'dummy_confirm_pass', new_phone, new_email, new_address]
    show_admin_profile()
    mock_cursor.execute.assert_any_call(pytest.string_containing("UPDATE administrador SET numero_administrador = %s, correo_admin = %s, direccion_administrador = %s WHERE id_administrador = %s"),(new_phone, new_email, new_address, 1))
    mock_conn.commit.assert_called_once()
    mock_streamlit_elements['success'].assert_called_with("✅ Información actualizada exitosamente")
    mock_streamlit_elements['rerun'].assert_called_once()

def test_mostrar_lista_usuarios_success(mock_st_session_state, mock_db_connection, mock_streamlit_elements):
    mock_conn, mock_cursor = mock_db_connection
    mock_st_session_state['user_id'] = 1
    mock_cursor.fetchone.return_value = {'numero_licencia': 10}
    db_users = [
        {'id_usuario': 10, 'nombre_usuario': 'User One', 'rut_usuario': '111-1', 'correo_user': 'one@test.com', 'estado': True},
        {'id_usuario': 11, 'nombre_usuario': 'User Two', 'rut_usuario': '222-2', 'correo_user': 'two@test.com', 'estado': False},
    ]
    mock_cursor.fetchall.return_value = db_users
    mostrar_lista_usuarios()
    mock_streamlit_elements['subheader'].assert_called_with("Lista de Usuarios")
    assert mock_cursor.execute.call_count == 2
    mock_cursor.execute.assert_any_call(pytest.string_containing("SELECT numero_licencia FROM administrador WHERE id_administrador = %s"), (1,))
    mock_cursor.execute.assert_any_call(pytest.string_containing("SELECT id_usuario, nombre_usuario, rut_usuario, correo_user, estado FROM usuario WHERE fk_administrador = %s"), (1,))
    mock_streamlit_elements['dataframe'].assert_called_once()
    args, _ = mock_streamlit_elements['dataframe'].call_args
    df_arg = args[0]
    assert len(df_arg) == 2
    assert df_arg[0][0] == 'User One'; assert df_arg[0][3] == '🟢 Activo'
    assert df_arg[1][0] == 'User Two'; assert df_arg[1][3] == '🔴 Inactivo'
    mock_streamlit_elements['info'].assert_any_call("Licencias utilizadas: 1/10")
    mock_streamlit_elements['success'].assert_any_call("Licencias disponibles: 9")

def test_mostrar_lista_usuarios_no_users(mock_st_session_state, mock_db_connection, mock_streamlit_elements):
    mock_conn, mock_cursor = mock_db_connection
    mock_st_session_state['user_id'] = 1
    mock_cursor.fetchone.return_value = {'numero_licencia': 10}
    mock_cursor.fetchall.return_value = []
    mostrar_lista_usuarios()
    mock_streamlit_elements['info'].assert_any_call("No hay usuarios registrados")
    mock_streamlit_elements['success'].assert_any_call("Tienes 10 licencias disponibles")

def test_crear_usuario_success(mock_st_session_state, mock_db_connection, mock_streamlit_elements):
    mock_conn, mock_cursor = mock_db_connection
    mock_st_session_state['user_id'] = 1
    mock_cursor.fetchone.side_effect = [{'total_activos': 5}, {'count': 0}, {'numero_licencia': 10}]
    mock_streamlit_elements['form_submit_button'].return_value = True
    mock_streamlit_elements['text_input'].side_effect = ["New User Name", "newuser@test.com", "+56912345670", "12.345.678-0", "password123"]
    with patch('app.views.admin.validar_numero_telefono', return_value=True) as mock_val_tel, \
         patch('app.views.admin.validar_rut', return_value=True) as mock_val_rut, \
         patch('app.views.admin.hash_password', return_value="hashed_password") as mock_hash_pw, \
         patch('app.views.admin.enviar_correo_bienvenida', return_value=True) as mock_send_email:
        crear_usuario()
    mock_cursor.execute.assert_any_call(pytest.string_containing("INSERT INTO usuario"),("New User Name", "12.345.678-0", "newuser@test.com", "hashed_password", 1, True))
    mock_conn.commit.assert_called_once()
    mock_send_email.assert_called_once_with("newuser@test.com", "New User Name", "password123")
    mock_streamlit_elements['success'].assert_called_with(pytest.string_containing("Usuario creado exitosamente"))
    mock_streamlit_elements['rerun'].assert_called_once()

def test_crear_usuario_licence_limit_reached(mock_st_session_state, mock_db_connection, mock_streamlit_elements):
    mock_conn, mock_cursor = mock_db_connection
    mock_st_session_state['user_id'] = 1
    mock_cursor.fetchone.side_effect = [{'total_activos': 10}, {'numero_licencia': 10}]
    crear_usuario()
    mock_streamlit_elements['warning'].assert_called_with("⚠️ Has alcanzado el límite de licencias activas (10). Desactiva algunos usuarios o adquiere más licencias para crear nuevos.")
    mock_streamlit_elements['form'].assert_not_called()

def test_crear_usuario_invalid_email(mock_st_session_state, mock_db_connection, mock_streamlit_elements):
    mock_conn, mock_cursor = mock_db_connection
    mock_st_session_state['user_id'] = 1
    mock_cursor.fetchone.side_effect = [{'total_activos': 5}, {'numero_licencia': 10}]
    mock_streamlit_elements['form_submit_button'].return_value = True
    mock_streamlit_elements['text_input'].side_effect = ["Test User", "invalidemail", "+56900000000", "11.111.111-1", "validPass1"]
    crear_usuario()
    mock_streamlit_elements['error'].assert_any_call("❌ El correo electrónico no es válido")

def test_crear_usuario_email_exists(mock_st_session_state, mock_db_connection, mock_streamlit_elements):
    mock_conn, mock_cursor = mock_db_connection
    mock_st_session_state['user_id'] = 1
    mock_cursor.fetchone.side_effect = [{'total_activos': 5}, {'count': 1}, {'numero_licencia': 10}]
    mock_streamlit_elements['form_submit_button'].return_value = True
    mock_streamlit_elements['text_input'].side_effect = ["Test User", "existing@test.com", "+56900000000", "11.111.111-1", "validPass1"]
    with patch('app.views.admin.validar_numero_telefono', return_value=True), \
         patch('app.views.admin.validar_rut', return_value=True):
        crear_usuario()
    mock_streamlit_elements['error'].assert_any_call("❌ Este correo electrónico ya está registrado")

def test_actualizar_usuario_form_loads_users(mock_st_session_state, mock_db_connection, mock_streamlit_elements):
    mock_conn, mock_cursor = mock_db_connection
    mock_st_session_state['user_id'] = 1
    users_data = [
        {'id_usuario': 1, 'nombre_usuario': 'User Alpha', 'correo_user': 'alpha@test.com', 'rut_usuario': '111-1', 'estado': True},
        {'id_usuario': 2, 'nombre_usuario': 'User Beta', 'correo_user': 'beta@test.com', 'rut_usuario': '222-2', 'estado': False}
    ]
    mock_cursor.fetchall.return_value = users_data
    with patch('app.views.admin.mostrar_formulario_actualizacion') as mock_mostrar_form:
        actualizar_usuario()
    mock_cursor.execute.assert_called_once_with(pytest.string_containing("SELECT id_usuario, nombre_usuario, correo_user, rut_usuario, estado FROM usuario WHERE fk_administrador = %s"), (1,))
    mock_streamlit_elements['selectbox'].assert_called_once()
    args, kwargs = mock_streamlit_elements['selectbox'].call_args
    assert kwargs['options'] == ["User Alpha (alpha@test.com)", "User Beta (beta@test.com)"]
    mock_mostrar_form.assert_called_once_with(users_data[0])

def test_actualizar_usuario_no_users(mock_st_session_state, mock_db_connection, mock_streamlit_elements):
    mock_conn, mock_cursor = mock_db_connection
    mock_st_session_state['user_id'] = 1
    mock_cursor.fetchall.return_value = []
    actualizar_usuario()
    mock_cursor.execute.assert_called_once_with(pytest.string_containing("SELECT id_usuario, nombre_usuario, correo_user, rut_usuario, estado FROM usuario WHERE fk_administrador = %s"), (1,))
    mock_streamlit_elements['info'].assert_called_with("No hay usuarios para actualizar")
    mock_streamlit_elements['selectbox'].assert_not_called()

def test_mostrar_formulario_actualizacion_submits_update(mock_st_session_state, mock_db_connection, mock_streamlit_elements):
    from app.views.admin import mostrar_formulario_actualizacion
    mock_conn, mock_cursor = mock_db_connection
    mock_st_session_state['user_id'] = 1
    current_user_data = {'id_usuario': 1, 'nombre_usuario': 'Old Name', 'correo_user': 'old@test.com', 'rut_usuario': '111-1', 'estado': True}
    mock_streamlit_elements['form_submit_button'].return_value = True
    mock_streamlit_elements['text_input'].side_effect = ["New Name", "new@test.com", "222-2", "newpassword123"]
    mock_streamlit_elements['checkbox'].return_value = False
    with patch('app.views.admin.hash_password', return_value="hashed_newpassword123") as mock_hash:
        mostrar_formulario_actualizacion(current_user_data)
    mock_cursor.execute.assert_called_once_with(pytest.string_containing("UPDATE usuario SET nombre_usuario = %s, correo_user = %s, rut_usuario = %s, estado = %s, contrasena_user = %s WHERE id_usuario = %s"),("New Name", "new@test.com", "222-2", False, "hashed_newpassword123", 1))
    mock_conn.commit.assert_called_once()
    mock_streamlit_elements['success'].assert_called_with("✅ Usuario actualizado exitosamente")
    mock_streamlit_elements['rerun'].assert_called_once()

def test_mostrar_formulario_actualizacion_submits_update_no_password_change(mock_st_session_state, mock_db_connection, mock_streamlit_elements):
    from app.views.admin import mostrar_formulario_actualizacion
    mock_conn, mock_cursor = mock_db_connection
    mock_st_session_state['user_id'] = 1
    current_user_data = {'id_usuario': 1, 'nombre_usuario': 'Old Name', 'correo_user': 'old@test.com', 'rut_usuario': '111-1', 'estado': True}
    mock_streamlit_elements['form_submit_button'].return_value = True
    mock_streamlit_elements['text_input'].side_effect = ["New Name", "new@test.com", "222-2", ""]
    mock_streamlit_elements['checkbox'].return_value = True
    with patch('app.views.admin.hash_password') as mock_hash:
        mostrar_formulario_actualizacion(current_user_data)
    mock_hash.assert_not_called()
    mock_cursor.execute.assert_called_once_with(pytest.string_containing("UPDATE usuario SET nombre_usuario = %s, correo_user = %s, rut_usuario = %s, estado = %s WHERE id_usuario = %s"),("New Name", "new@test.com", "222-2", True, 1))
    mock_conn.commit.assert_called_once()
    mock_streamlit_elements['success'].assert_called_with("✅ Usuario actualizado exitosamente")
    mock_streamlit_elements['rerun'].assert_called_once()

# Tests for mostrar_reportes and its sub-functions
def test_mostrar_reportes_shows_options_and_calls_sub_report(mock_st_session_state, mock_streamlit_elements):
    mock_st_session_state['user_id'] = 1
    mock_streamlit_elements['date_input'].side_effect = [date(2023, 1, 1), date(2023, 1, 31)]
    mock_streamlit_elements['selectbox'].return_value = "Actividad de Usuarios"
    with patch('app.views.admin.mostrar_reporte_actividad') as mock_actividad, \
         patch('app.views.admin.mostrar_reporte_impacto') as mock_impacto, \
         patch('app.views.admin.mostrar_reporte_general') as mock_general:
        mostrar_reportes()
    mock_streamlit_elements['subheader'].assert_called_with("📊 Reportes y Estadísticas")
    mock_streamlit_elements['selectbox'].assert_called_with("Seleccione el tipo de reporte", ["Actividad de Usuarios", "Impacto Ambiental", "Resumen General"])
    mock_actividad.assert_called_once_with(date(2023, 1, 1), date(2023, 1, 31))
    mock_impacto.assert_not_called()
    mock_general.assert_not_called()

    mock_streamlit_elements['selectbox'].return_value = "Impacto Ambiental" # Reset side effect for selectbox
    # Reset date_input side effect as it's consumed
    mock_streamlit_elements['date_input'].side_effect = [date(2023, 1, 1), date(2023, 1, 31)]
    with patch('app.views.admin.mostrar_reporte_actividad') as mock_actividad, \
         patch('app.views.admin.mostrar_reporte_impacto') as mock_impacto, \
         patch('app.views.admin.mostrar_reporte_general') as mock_general:
        mostrar_reportes()
    mock_impacto.assert_called_once_with(date(2023, 1, 1), date(2023, 1, 31))

    mock_streamlit_elements['selectbox'].return_value = "Resumen General"
    mock_streamlit_elements['date_input'].side_effect = [date(2023, 1, 1), date(2023, 1, 31)]
    with patch('app.views.admin.mostrar_reporte_actividad') as mock_actividad, \
         patch('app.views.admin.mostrar_reporte_impacto') as mock_impacto, \
         patch('app.views.admin.mostrar_reporte_general') as mock_general:
        mostrar_reportes()
    mock_general.assert_called_once_with(date(2023, 1, 1), date(2023, 1, 31))

def test_mostrar_reporte_actividad_with_data(mock_st_session_state, mock_db_connection, mock_streamlit_elements):
    from app.views.admin import mostrar_reporte_actividad
    mock_conn, mock_cursor = mock_db_connection
    mock_st_session_state['user_id'] = 1
    report_data = [
        {'nombre_usuario': 'User A', 'total_reconocimientos': 10, 'total_plastico': 5.5, 'impacto_total': 2.75},
        {'nombre_usuario': 'User B', 'total_reconocimientos': 5, 'total_plastico': 2.0, 'impacto_total': 1.0},
    ]
    mock_cursor.fetchall.return_value = report_data
    with patch('pandas.DataFrame') as mock_pd_dataframe:
        mock_df_instance = MagicMock()
        mock_pd_dataframe.return_value = mock_df_instance
        mock_df_instance.to_csv.return_value = "csv_data_mock"
        mostrar_reporte_actividad(date(2023,1,1), date(2023,1,31))
    mock_cursor.execute.assert_called_once_with(pytest.string_containing("SELECT u.nombre_usuario, COUNT(r.id_reconocimiento) as total_reconocimientos"),(date(2023,1,1), date(2023,1,31), 1))
    mock_streamlit_elements['metric'].assert_any_call("Total Usuarios Activos", 2)
    mock_streamlit_elements['metric'].assert_any_call("Total Plástico Reciclado", "7.50 kg")
    mock_streamlit_elements['metric'].assert_any_call("Impacto CO2 Total", "3.75 kg")
    mock_streamlit_elements['bar_chart'].assert_called_once()
    mock_streamlit_elements['dataframe'].assert_called_once()
    mock_streamlit_elements['download_button'].assert_called_once()

def test_mostrar_reporte_actividad_no_data(mock_st_session_state, mock_db_connection, mock_streamlit_elements):
    from app.views.admin import mostrar_reporte_actividad
    mock_conn, mock_cursor = mock_db_connection
    mock_st_session_state['user_id'] = 1
    mock_cursor.fetchall.return_value = []
    mostrar_reporte_actividad(date(2023,1,1), date(2023,1,31))
    mock_streamlit_elements['info'].assert_called_with("No hay datos para el período seleccionado")
    mock_streamlit_elements['metric'].assert_not_called()

def test_mostrar_reporte_impacto_with_data(mock_st_session_state, mock_db_connection, mock_streamlit_elements):
    from app.views.admin import mostrar_reporte_impacto
    mock_conn, mock_cursor = mock_db_connection
    mock_st_session_state['user_id'] = 1
    report_data = [
        {'fk_plastico': '1', 'total_reconocimientos': 20, 'total_plastico': 10.0, 'impacto_total': 5.0},
        {'fk_plastico': '2', 'total_reconocimientos': 15, 'total_plastico': 7.5, 'impacto_total': 3.75},
    ]
    mock_cursor.fetchall.return_value = report_data
    with patch('pandas.DataFrame') as mock_pd_dataframe, patch('plotly.express.pie') as mock_px_pie:
        mock_df_instance = MagicMock()
        def df_side_effect(data, columns=None): # Adjusted to match expected pandas.DataFrame call
            for row in data:
                row['tipo_plastico'] = PLASTIC_TYPE_NAMES.get(str(row['fk_plastico']))
            mock_df_instance.empty = not bool(data) # Simulate empty attribute for df.empty check
            return mock_df_instance
        mock_pd_dataframe.side_effect = df_side_effect
        mock_df_instance.to_csv.return_value = "csv_data_mock"
        mock_px_pie.return_value = MagicMock()
        mostrar_reporte_impacto(date(2023,1,1), date(2023,1,31))
    mock_cursor.execute.assert_called_once_with(pytest.string_containing("SELECT r.fk_plastico, COUNT(*) as total_reconocimientos"),(date(2023,1,1), date(2023,1,31), 1))
    mock_streamlit_elements['metric'].assert_any_call("Total Plástico Reciclado", "17.50 kg")
    mock_streamlit_elements['metric'].assert_any_call("Impacto CO2 Total", "8.75 kg")
    mock_px_pie.assert_called_once()
    mock_streamlit_elements['plotly_chart'].assert_called_once()
    mock_streamlit_elements['dataframe'].assert_called_once()
    mock_streamlit_elements['download_button'].assert_called_once()

def test_mostrar_reporte_general_with_data(mock_st_session_state, mock_db_connection, mock_streamlit_elements):
    from app.views.admin import mostrar_reporte_general
    mock_conn, mock_cursor = mock_db_connection
    mock_st_session_state['user_id'] = 1
    stats_data = {'total_usuarios': 5, 'total_reconocimientos': 100, 'total_plastico': 50.75, 'impacto_total': 25.375}
    tendencias_data = [{'fecha': date(2023,1,1), 'total_plastico': 10.0, 'impacto_total': 5.0}, {'fecha': date(2023,1,2), 'total_plastico': 12.0, 'impacto_total': 6.0}]
    mock_cursor.fetchone.return_value = stats_data
    mock_cursor.fetchall.return_value = tendencias_data
    with patch('pandas.DataFrame') as mock_pd_dataframe, patch('plotly.express.line') as mock_px_line:
        mock_df_instance = MagicMock()
        mock_pd_dataframe.return_value = mock_df_instance
        mock_px_line.return_value = MagicMock()
        mostrar_reporte_general(date(2023,1,1), date(2023,1,31))
    assert mock_cursor.execute.call_count == 2
    mock_cursor.execute.assert_any_call(pytest.string_containing("SELECT COUNT(DISTINCT u.id_usuario) as total_usuarios"),(1, date(2023,1,1), date(2023,1,31)))
    mock_cursor.execute.assert_any_call(pytest.string_containing("SELECT DATE_TRUNC('day', r.fecha_reconocimiento) as fecha"),(1, date(2023,1,1), date(2023,1,31)))
    mock_streamlit_elements['metric'].assert_any_call("Total Usuarios", 5)
    mock_streamlit_elements['metric'].assert_any_call("Total Reconocimientos", 100)
    mock_streamlit_elements['metric'].assert_any_call("Total Plástico Reciclado", "50.75 kg")
    mock_streamlit_elements['metric'].assert_any_call("Impacto CO2 Total", "25.38 kg")
    mock_streamlit_elements['metric'].assert_any_call("1000 botellas", "70% completado", delta="70%", delta_color="normal")
    mock_streamlit_elements['metric'].assert_any_call("500 kg", "85% completado", delta="85%", delta_color="normal")
    mock_px_line.assert_called_once()
    mock_streamlit_elements['plotly_chart'].assert_called_once()

def test_mostrar_reporte_general_no_tendencias_data(mock_st_session_state, mock_db_connection, mock_streamlit_elements):
    from app.views.admin import mostrar_reporte_general
    mock_conn, mock_cursor = mock_db_connection
    mock_st_session_state['user_id'] = 1
    stats_data = {'total_usuarios': 0, 'total_reconocimientos': 0, 'total_plastico': 0.0, 'impacto_total': 0.0}
    mock_cursor.fetchone.return_value = stats_data
    mock_cursor.fetchall.return_value = []
    mostrar_reporte_general(date(2023,1,1), date(2023,1,31))
    mock_streamlit_elements['info'].assert_called_with("No hay datos suficientes para mostrar tendencias")
