import os
import logging
import streamlit as st
from PIL import Image
import io
from collections import Counter
from typing import Optional, Dict, Any, Union
from datetime import datetime
from roboflow import Roboflow
from dotenv import load_dotenv

# Cargar variables de entorno
load_dotenv()

# Configuración de logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Configuración de Roboflow
ROBOFLOW_API_KEY = os.getenv("ROBOFLOW_API_KEY", "heEHust0x8LCWpzRlGaA")
ROBOFLOW_MODEL = "plastic-recyclable-detection/2"
ROBOFLOW_SIZE = 416
CONFIDENCE_THRESHOLD = 0.40
OVERLAP_THRESHOLD = 30

# Inicializar el cliente de Roboflow
try:
    rf = Roboflow(api_key=ROBOFLOW_API_KEY)
    project = rf.workspace().project("plastic-recyclable-detection")
    model = project.version(1).model
    logger.info("Modelo de Roboflow inicializado correctamente")
except Exception as e:
    logger.error(f"Error al inicializar Roboflow: {str(e)}")
    model = None

def classify_waste(image_data: Union[bytes, Any]) -> Optional[Dict[str, Any]]:
    """
    Clasifica residuos usando Roboflow
    """
    try:
        if model is None:
            raise ValueError("Modelo no inicializado correctamente")

        # Validar tamaño de imagen
        if hasattr(image_data, 'size') and image_data.size > 10 * 1024 * 1024:  # 10MB
            raise ValueError("Imagen demasiado grande. Máximo 10MB permitido.")

        # Crear directorio temporal si no existe
        temp_dir = "temp_images"
        os.makedirs(temp_dir, exist_ok=True)
        
        # Guardar imagen temporalmente
        temp_image_path = os.path.join(temp_dir, f"temp_{datetime.now().strftime('%Y%m%d%H%M%S')}.jpg")
        
        if hasattr(image_data, 'read'):
            image = Image.open(image_data)
            image.save(temp_image_path)
        else:
            with open(temp_image_path, 'wb') as f:
                f.write(image_data)

        # Realizar predicción
        predictions = model.predict(
            temp_image_path,
            confidence=CONFIDENCE_THRESHOLD,
            overlap=OVERLAP_THRESHOLD
        ).json()

        # Procesar resultados
        if predictions and 'predictions' in predictions:
            conteo = Counter(pred['class'] for pred in predictions['predictions'])
            confianzas = {}
            
            for tipo in conteo.keys():
                confianzas_tipo = [
                    pred['confidence'] 
                    for pred in predictions['predictions'] 
                    if pred['class'] == tipo
                ]
                confianzas[tipo] = sum(confianzas_tipo) / len(confianzas_tipo)

            return {
                'total_botellas': len(predictions['predictions']),
                'conteo_por_tipo': dict(conteo),
                'confianza_promedio': confianzas,
                'predicciones': predictions['predictions']
            }
        else:
            return {
                'total_botellas': 0,
                'conteo_por_tipo': {},
                'confianza_promedio': {},
                'predicciones': []
            }

    except ValueError as e:
        logger.error(f"Error de validación: {str(e)}")
        return None
    except Exception as e:
        logger.error(f"Error inesperado en clasificación: {str(e)}")
        return None
    finally:
        # Limpiar archivos temporales
        if 'temp_image_path' in locals():
            try:
                os.remove(temp_image_path)
            except:
                pass

def mostrar_reconocimiento_residuos(username: str):
    st.write(f"Reconocimiento de residuos para el usuario: {username}")
    
    metodo_entrada = st.radio(
        "Selecciona cómo quieres subir tu imagen:",
        ["Tomar foto con la cámara", "Subir imagen desde el dispositivo"],
        horizontal=True
    )
    
    image_data = None
    
    if metodo_entrada == "Tomar foto con la cámara":
        st.write("### 📸 Usar la cámara")
        image_data = st.camera_input("Tomar una foto")
    else:
        st.write("### 📤 Subir una imagen")
        image_data = st.file_uploader("Elige una imagen...", type=['jpg', 'jpeg', 'png'])
    
    if image_data is not None:
        try:
            st.image(image_data, caption="Imagen a analizar", use_column_width=True)
            
            with st.spinner("🔍 Analizando imagen..."):
                results = classify_waste(image_data)
            
            if results and results['total_botellas'] > 0:
                st.success("✅ ¡Imagen analizada con éxito!")
                
                st.write("### 📊 Resultados del análisis")
                total_botellas = results['total_botellas']
                st.write(f"Total de botellas detectadas: {total_botellas}")
                
                impacto_co2 = calcular_impacto_co2(total_botellas)
                st.write("### 🌱 Impacto Ambiental")
                st.write(f"CO2 ahorrado: {impacto_co2:.2f} kg")
                
                st.write("### 🔍 Detalle por tipo")
                for tipo, cantidad in results['conteo_por_tipo'].items():
                    confianza = results['confianza_promedio'].get(tipo, 0) * 100
                    
                    st.write(f"- {tipo}: {cantidad} (Confianza: {confianza:.1f}%)")
                    
                    with st.expander(f"ℹ️ Más información sobre {tipo}"):
                        info = get_bottle_info(tipo)
                        st.write(f"**Nombre completo:** {info['nombre_completo']}")
                        st.write(f"**Tiempo de degradación:** {info['tiempo_degradacion']}")
                        st.write(f"**Valor de reciclaje:** {info['valor_reciclaje']}")
                        st.write("**Preparación para reciclaje:**")
                        for paso in info['preparacion']:
                            st.write(f"- {paso}")
            else:
                st.warning("⚠️ No se detectaron botellas en la imagen.")
                
        except Exception as e:
            st.error(f"❌ Error al procesar la imagen: {str(e)}")
            logger.error(f"Error en el procesamiento: {str(e)}")

def get_bottle_info(bottle_type: str) -> Dict[str, Any]:
    """
    Retorna información detallada sobre el tipo de botella
    """
    BOTTLE_INFO = {
        "PET": {
            "nombre_completo": "Tereftalato de polietileno",
            "usos_comunes": ["Botellas de bebidas", "Envases de alimentos"],
            "tiempo_degradacion": "500 años aproximadamente",
            "valor_reciclaje": "Alto",
            "preparacion": [
                "Retirar etiqueta",
                "Enjuagar",
                "Comprimir"
            ]
        },
        "HDPE": {
            "nombre_completo": "Polietileno de alta densidad",
            "usos_comunes": ["Botellas de leche", "Productos de limpieza"],
            "tiempo_degradacion": "450 años aproximadamente",
            "valor_reciclaje": "Alto",
            "preparacion": [
                "Vaciar completamente",
                "Enjuagar",
                "Quitar tapa"
            ]
        }
    }
    
    return BOTTLE_INFO.get(bottle_type.upper(), {
        "nombre_completo": "Tipo no identificado",
        "tiempo_degradacion": "Desconocido",
        "valor_reciclaje": "Desconocido",
        "preparacion": ["Consultar punto limpio local"]
    })

def calcular_impacto_co2(total_botellas: int) -> float:
    """
    Calcula el impacto en CO2 basado en el número de botellas recicladas
    """
    FACTOR_CO2_POR_BOTELLA = 0.5  # kg de CO2 por botella
    return total_botellas * FACTOR_CO2_POR_BOTELLA 