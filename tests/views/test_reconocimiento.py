import pytest
from unittest.mock import MagicMock, patch, mock_open
import os
from PIL import Image # Will be mocked where image processing is not the focus
import io
import logging # For logger patching

from app.views.reconocimiento import (
    classify_waste,
    guardar_reconocimiento,
    mostrar_reconocimiento_residuos,
    get_bottle_info,
    calcular_impacto_co2,
    PLASTIC_TYPE_MAPPING,
    ROBOFLOW_API_KEY,
    model as roboflow_model
)
from app.views.reconocimiento import logger as reconocimiento_logger

# Mock database connection and streamlit elements are auto-used from conftest.py

def test_roboflow_model_initialized():
    assert roboflow_model is not None, "Roboflow model failed to initialize"
    assert ROBOFLOW_API_KEY is not None, "ROBOFLOW_API_KEY is not set"
    assert ROBOFLOW_API_KEY != "YOUR_ROBOFLOW_API_KEY", "Default ROBOFLOW_API_KEY is still set"


@patch('app.views.reconocimiento.model')
def test_classify_waste_success(mock_roboflow_model_instance, mock_db_connection, mock_st_session_state, tmp_path):
    mock_conn, mock_cursor = mock_db_connection
    mock_st_session_state['user_id'] = 1
    mock_st_session_state['admin_id'] = 100 # classify_waste uses st.session_state.get('admin_id')

    mock_prediction_json = {
        "predictions": [
            {"class": "PET Plastic", "confidence": 0.9}, # Mapped to 'PET'
            {"class": "HDPE Plastic", "confidence": 0.8},# Mapped to 'HDPE'
            {"class": "PET Plastic", "confidence": 0.85}, # Mapped to 'PET'
        ]
    }
    # Mock the chain: model.predict().json()
    mock_predict_obj = MagicMock()
    mock_predict_obj.json.return_value = mock_prediction_json
    mock_roboflow_model_instance.predict.return_value = mock_predict_obj

    def mock_fetchone_side_effect(*args, **kwargs):
        sql_query = args[0]
        param_value = args[1][0]
        if param_value == PLASTIC_TYPE_MAPPING["PET Plastic"]: # 'PET'
            return {'id_plastico': 1, 'valor_co2': 0.5} # Example valor_co2
        elif param_value == PLASTIC_TYPE_MAPPING["HDPE Plastic"]: # 'HDPE'
            return {'id_plastico': 2, 'valor_co2': 0.4}
        return {'id_plastico': 99, 'valor_co2': 0.1} # For OTHER
    mock_cursor.fetchone.side_effect = mock_fetchone_side_effect

    dummy_image_content = b"fake image data"

    # Mock os.makedirs, os.remove, open, and PIL.Image.open
    with patch('os.makedirs', MagicMock()) as mock_makedirs, \
         patch('os.remove', MagicMock()) as mock_remove, \
         patch('builtins.open', new_callable=mock_open) as mock_file_open, \
         patch('PIL.Image.open', MagicMock(return_value=MagicMock(format='JPEG'))) as mock_pil_open:

        results = classify_waste(dummy_image_content)

    assert results is not None
    assert results['total_botellas'] == 3
    assert results['conteo_por_tipo']['PET Plastic'] == 2
    assert results['conteo_por_tipo']['HDPE Plastic'] == 1

    # classify_waste itself inserts recognitions one by one.
    # PET: tipo_plastico_db = 'PET', id_plastico=1, cantidad=2, co2_calculado_unitario=0.5, peso_total = 2 * 0.02 = 0.04
    #      co2_total_calculado = 2 * 0.5 = 1.0
    # HDPE: tipo_plastico_db = 'HDPE', id_plastico=2, cantidad=1, co2_calculado_unitario=0.4, peso_total = 1 * 0.02 = 0.02
    #       co2_total_calculado = 1 * 0.4 = 0.4
    # Note: classify_waste uses PESO_BOTELLA (0.02 kg) and calls calcular_impacto_co2 with quantity.
    # calcular_impacto_co2(cantidad) uses FACTOR_EMISION_CO2 (0.5)
    # So, co2 for PET (2 bottles) = 2 * 0.5 = 1.0
    # So, co2 for HDPE (1 bottle) = 1 * 0.5 = 0.5 (Not 0.4 from valor_co2 in DB as calcular_impacto_co2 is simpler)

    mock_cursor.execute.assert_any_call(
        pytest.string_containing("INSERT INTO reconocimiento"),
        (1, 0.04, 2, 1.0, mock_st_session_state['user_id'], mock_st_session_state.get('admin_id'))
    )
    mock_cursor.execute.assert_any_call(
        pytest.string_containing("INSERT INTO reconocimiento"),
        (2, 0.02, 1, 0.5, mock_st_session_state['user_id'], mock_st_session_state.get('admin_id'))
    )
    assert mock_conn.commit.call_count == 2 # Called after each successful insert in classify_waste


@patch('app.views.reconocimiento.model')
def test_classify_waste_no_predictions(mock_roboflow_model_instance, mock_db_connection, mock_st_session_state, tmp_path):
    mock_conn, mock_cursor = mock_db_connection
    mock_predict_obj = MagicMock()
    mock_predict_obj.json.return_value = {"predictions": []}
    mock_roboflow_model_instance.predict.return_value = mock_predict_obj

    with patch('os.makedirs', MagicMock()), patch('os.remove', MagicMock()), \
         patch('builtins.open', new_callable=mock_open), \
         patch('PIL.Image.open', MagicMock(return_value=MagicMock(format='JPEG'))):
        results = classify_waste(b"dummy_image_data")

    assert results['total_botellas'] == 0
    assert not results['conteo_por_tipo']
    # No db inserts if no predictions, so no execute calls for INSERT
    # mock_cursor.execute might be called for SELECT id_plastico if logic tries to map empty predictions
    # Based on current code, if predictions_list is empty, it returns early.
    for call_arg in mock_cursor.execute.call_args_list:
        assert "INSERT INTO reconocimiento" not in str(call_arg[0][0])
    mock_conn.commit.assert_not_called()


@patch('app.views.reconocimiento.model')
def test_classify_waste_image_too_large(mock_roboflow_model_instance, mock_st_session_state):
    mock_image_bytes = b"data" * (11 * 1024 * 1024 // 4) # Create 11MB of data

    with patch.object(reconocimiento_logger, 'error') as mock_log_error:
        results = classify_waste(mock_image_bytes)

    assert results is None
    mock_log_error.assert_called_once_with(pytest.string_containing("Error de validación: Imagen demasiado grande"))


def test_guardar_reconocimiento_success(mock_db_connection, mock_st_session_state):
    mock_conn, mock_cursor = mock_db_connection
    user_id_for_test = 123
    mock_st_session_state['user_id'] = user_id_for_test

    results_from_classify = {
        'total_botellas': 3, # Not directly used by this guardar_reconocimiento
        'conteo_por_tipo': {'PET Plastic': 2, 'HDPE Plastic': 1},
        'confianza_promedio': {'PET Plastic': 0.9, 'HDPE Plastic': 0.8} # Not used
    }

    def mock_db_lookup_side_effect(*args, **kwargs):
        sql_query = args[0]
        param_value = args[1][0]
        if param_value == PLASTIC_TYPE_MAPPING['PET Plastic']:
            return {'id_plastico': 1, 'valor_co2': 0.5, 'peso_promedio': 0.025} # Example values
        elif param_value == PLASTIC_TYPE_MAPPING['HDPE Plastic']:
            return {'id_plastico': 2, 'valor_co2': 0.4, 'peso_promedio': 0.030}
        return None
    mock_cursor.fetchone.side_effect = mock_db_lookup_side_effect

    success = guardar_reconocimiento(results_from_classify, user_id_for_test)

    assert success is True
    # PET: fk_plastico=1, cantidad=2, peso_total=2*0.025=0.05, co2_total=2*0.5=1.0
    # HDPE: fk_plastico=2, cantidad=1, peso_total=1*0.030=0.03, co2_total=1*0.4=0.4
    mock_cursor.execute.assert_any_call(
        pytest.string_containing("INSERT INTO reconocimiento"),
        (1, 0.05, 2, 1.0, user_id_for_test) # Note: admin_id is not in this version of guardar_reconocimiento
    )
    mock_cursor.execute.assert_any_call(
        pytest.string_containing("INSERT INTO reconocimiento"),
        (2, 0.03, 1, 0.4, user_id_for_test)
    )
    mock_conn.commit.assert_called_once()


def test_guardar_reconocimiento_unknown_plastic_type(mock_db_connection, mock_st_session_state, mock_streamlit_elements):
    mock_conn, mock_cursor = mock_db_connection
    user_id_for_test = 123
    mock_st_session_state['user_id'] = user_id_for_test

    results_from_classify = {'conteo_por_tipo': {'Unknown Plastic': 1}}
    mock_cursor.fetchone.return_value = None

    success = guardar_reconocimiento(results_from_classify, user_id_for_test)

    assert success is True
    # PLASTIC_TYPE_MAPPING.get('Unknown Plastic', 'OTHER') -> 'OTHER'
    # The code then tries to SELECT for 'OTHER'. Let's assume 'OTHER' also returns None.
    mock_streamlit_elements['error'].assert_called_with("Tipo de plástico no encontrado en la base de datos: OTHER")

    insert_called = False
    for call_obj in mock_cursor.execute.call_args_list:
        if "INSERT INTO reconocimiento" in str(call_obj[0][0]):
            insert_called = True; break
    assert not insert_called
    mock_conn.commit.assert_not_called() # No successful inserts, so no commit


@patch('app.views.reconocimiento.classify_waste')
@patch('app.views.reconocimiento.guardar_reconocimiento')
def test_mostrar_reconocimiento_residuos_upload_success(mock_guardar, mock_classify, mock_streamlit_elements, mock_st_session_state):
    mock_st_session_state['user_id'] = 1
    mock_st_session_state['user_name'] = "test_user_for_rec"

    mock_streamlit_elements['radio'].return_value = "Subir imagen desde el dispositivo"
    mock_image_data = MagicMock(spec=io.BytesIO) # More specific mock for uploaded file
    mock_image_data.getvalue.return_value = b"uploaded_image_bytes"
    mock_image_data.name = "test.jpg" # Add name attribute
    mock_image_data.size = 1000 # Add size attribute
    mock_streamlit_elements['file_uploader'].return_value = mock_image_data

    classify_results = {'total_botellas': 1, 'conteo_por_tipo': {'PET Plastic': 1}, 'detalles': [{'tipo': 'PET', 'cantidad': 1, 'co2_ahorrado': 0.5}]}
    mock_classify.return_value = classify_results
    mock_guardar.return_value = True

    mostrar_reconocimiento_residuos("test_user_for_rec")

    mock_streamlit_elements['file_uploader'].assert_called_once()
    # mock_streamlit_elements['image'].assert_called_once_with(mock_image_data, caption="Imagen a analizar", use_container_width=True) # This is tricky if getvalue() is consumed
    mock_classify.assert_called_once_with(mock_image_data) # classify_waste now takes the UploadedFile object
    mock_streamlit_elements['success'].assert_any_call("✅ ¡Imagen analizada con éxito!")
    mock_guardar.assert_called_once_with(classify_results, 1)
    mock_streamlit_elements['success'].assert_any_call("✅ Datos guardados correctamente")
    mock_streamlit_elements['write'].assert_any_call(pytest.string_containing("CO2 ahorrado:"))


@patch('app.views.reconocimiento.classify_waste')
def test_mostrar_reconocimiento_residuos_no_bottles_detected(mock_classify, mock_streamlit_elements, mock_st_session_state):
    mock_st_session_state['user_id'] = 1
    mock_st_session_state['user_name'] = "test_user_for_rec"

    mock_streamlit_elements['radio'].return_value = "Tomar foto con la cámara"
    mock_camera_image_data = MagicMock(spec=io.BytesIO)
    mock_camera_image_data.getvalue.return_value = b"camera_image_bytes"
    mock_camera_image_data.name = "camera_photo.jpg"
    mock_camera_image_data.size = 1000
    mock_streamlit_elements['camera_input'].return_value = mock_camera_image_data

    mock_classify.return_value = {'total_botellas': 0, 'conteo_por_tipo': {}, 'detalles': []}

    mostrar_reconocimiento_residuos("test_user_for_rec")

    mock_classify.assert_called_once_with(mock_camera_image_data)
    mock_streamlit_elements['warning'].assert_called_with("⚠️ No se detectaron botellas en la imagen")


def test_get_bottle_info():
    pet_info = get_bottle_info("PET")
    assert pet_info['nombre_completo'] == "Tereftalato de polietileno"
    unknown_info = get_bottle_info("XYZ") # Should map to 'OTHER' category
    assert unknown_info['nombre_completo'] == "Tipo no identificado"

def test_calcular_impacto_co2():
    assert calcular_impacto_co2(0) == 0.0
    assert calcular_impacto_co2(1) == 0.5
    assert calcular_impacto_co2(10) == 5.0
