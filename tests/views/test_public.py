import pytest
from unittest.mock import MagicMock, patch
from app.views.public import (
    show_home,
    show_register,
    validar_rut_empresa,
    validar_email,
    validar_telefono,
    validar_datos_registro
)
# Note: Detailed tests for show_register (admin/company registration) are in test_auth.py
# as it's part of the initial system setup and authentication flow.

# Mock database connection and streamlit elements are auto-used from conftest.py

def test_show_home(mock_streamlit_elements):
    show_home()
    mock_streamlit_elements['title'].assert_called_with("Bienvenido a GreenIA")
    mock_streamlit_elements['subheader'].assert_called_with("Sistema de Gestión de Residuos Reciclables")
    mock_streamlit_elements['write'].assert_any_call("Únete a nuestra comunidad y contribuye al medio ambiente.")
    mock_streamlit_elements['markdown'].assert_any_call(pytest.string_containing("### 🏢 Para Empresas"))
    mock_streamlit_elements['markdown'].assert_any_call(pytest.string_containing("### 💚 Sobre Nosotros"))
    mock_streamlit_elements['markdown'].assert_any_call(pytest.string_containing("### ✨ ¿Por Qué Elegirnos?"))
    mock_streamlit_elements['markdown'].assert_any_call(pytest.string_containing("### 📞 Contacto"))


def test_show_register_runs(mock_streamlit_elements):
    mock_streamlit_elements['form_submit_button'].return_value = False
    show_register()
    mock_streamlit_elements['title'].assert_called_with("🏢 Comprar Licencia Anual")
    mock_streamlit_elements['form'].assert_called_once()


@pytest.mark.parametrize("rut, expected", [
    ("76.123.456-K", True),
    ("70.000.000-0", True),
    ("99.999.999-9", True),
    ("80.123.456-5", True),
    ("1.234.567-8", False),
    ("76123456K", True),
    ("76.123.456-k", True),
    ("12.345.678-9", False),
    ("76.123.45A-K", False),
    ("76.123.456-X", False),
    ("", False),
    (None, False)
])
def test_validar_rut_empresa(rut, expected):
    assert validar_rut_empresa(rut) == expected

@pytest.mark.parametrize("email, expected", [
    ("test@example.com", True),
    ("test.user@example.co.uk", True),
    ("test@localhost", True),
    ("test", False),
    ("test@.com", False),
    ("@example.com", False),
    ("test@example.", False),
    ("", False),
    (None, False)
])
def test_validar_email(email, expected):
    assert validar_email(email) == expected

@pytest.mark.parametrize("telefono, expected", [
    ("+56912345678", True),
    ("912345678", True),
    ("12345678", False),
    ("123456789012", False),
    ("+5691234567A", False),
    ("56912345678", True),
    ("", False),
    (None, False)
])
def test_validar_telefono(telefono, expected):
    assert validar_telefono(telefono) == expected


def test_validar_datos_registro_all_valid(mock_streamlit_elements):
    datos = {
        'rut_empresa': "76.123.456-K", # Changed from 'rut' to 'rut_empresa' to match show_register
        'correo_empresa': "test@example.com", # Changed from 'email' to 'correo_empresa'
        'telefono_empresa': "+56912345678", # Changed from 'telefono' to 'telefono_empresa'
        'nombre_legal': "Test Name", # Changed from 'nombre' to 'nombre_legal'
        'nombre_empresa': "Test Company", # Changed from 'empresa' to 'nombre_empresa'
        'direccion_empresa': "123 Test St" # Changed from 'direccion' to 'direccion_empresa'
    }
    # Patch individual validators as validar_datos_registro calls them
    with patch('app.views.public.validar_rut_empresa', return_value=True) as mock_val_rut, \
         patch('app.views.public.validar_email', return_value=True) as mock_val_email, \
         patch('app.views.public.validar_telefono', return_value=True) as mock_val_tel:
        errors = validar_datos_registro(
            datos['nombre_legal'], datos['rut_empresa'], datos['correo_empresa'],
            datos['nombre_empresa'], datos['telefono_empresa'], datos['direccion_empresa']
        )
    assert not errors
    mock_val_rut.assert_called_with(datos['rut_empresa'])
    mock_val_email.assert_called_with(datos['correo_empresa'])
    mock_val_tel.assert_called_with(datos['telefono_empresa'])


def test_validar_datos_registro_invalid_rut(mock_streamlit_elements):
    datos = {
        'rut_empresa': "invalid-rut", 'correo_empresa': "test@example.com", 'telefono_empresa': "+56912345678",
        'nombre_legal': "Test Name", 'nombre_empresa': "Test Company", 'direccion_empresa': "123 Test St"
    }
    with patch('app.views.public.validar_rut_empresa', return_value=False) as mock_val_rut, \
         patch('app.views.public.validar_email', return_value=True), \
         patch('app.views.public.validar_telefono', return_value=True):
        errors = validar_datos_registro(
            datos['nombre_legal'], datos['rut_empresa'], datos['correo_empresa'],
            datos['nombre_empresa'], datos['telefono_empresa'], datos['direccion_empresa']
        )
    assert "El RUT de empresa no es válido" in errors
    mock_val_rut.assert_called_with(datos['rut_empresa'])


def test_validar_datos_registro_short_name(mock_streamlit_elements):
    datos = {
        'rut_empresa': "76.123.456-K", 'correo_empresa': "test@example.com", 'telefono_empresa': "+56912345678",
        'nombre_legal': "T", 'nombre_empresa': "Test Company", 'direccion_empresa': "123 Test St"
    }
    with patch('app.views.public.validar_rut_empresa', return_value=True), \
         patch('app.views.public.validar_email', return_value=True), \
         patch('app.views.public.validar_telefono', return_value=True):
        errors = validar_datos_registro(
            datos['nombre_legal'], datos['rut_empresa'], datos['correo_empresa'],
            datos['nombre_empresa'], datos['telefono_empresa'], datos['direccion_empresa']
        )
    assert "El nombre del representante legal es demasiado corto" in errors # Specific message from function
    # Also test other required fields
    datos_missing_all = {'nombre_legal': "", 'rut_empresa': "", 'correo_empresa': "", 'nombre_empresa': "", 'telefono_empresa': "", 'direccion_empresa': ""}
    errors_all_missing = validar_datos_registro("", "", "", "", "", "")
    assert "El nombre del representante legal es obligatorio" in errors_all_missing
    assert "El RUT de empresa es obligatorio" in errors_all_missing
    assert "El correo electrónico de empresa es obligatorio" in errors_all_missing
    assert "El nombre de empresa es obligatorio" in errors_all_missing
    assert "El teléfono de empresa es obligatorio" in errors_all_missing
    assert "La dirección de empresa es obligatoria" in errors_all_missing

# Note on other validators in public.py:
# - validar_numero_telefono (different from validar_telefono)
# - validar_rut (different from validar_rut_empresa)
# These are not directly used by show_home or show_register in public.py.
# Tests for them are omitted here but should be added if they become used by public views.
