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
from database import get_db_connection
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
CONFIDENCE_THRESHOLD = 0.25
OVERLAP_THRESHOLD = 0.45

# Inicializar el cliente de Roboflow
try:
    rf = Roboflow(api_key=ROBOFLOW_API_KEY)
    project = rf.workspace().project("plastic-recyclable-detection")
    model = project.version(2).model
    logger.info("Modelo de Roboflow inicializado correctamente")
except Exception as e:
    logger.error(f"Error al inicializar Roboflow: {str(e)}")
    model = None

def classify_waste(image_data: Union[bytes, Any]) -> Optional[Dict[str, Any]]:
    """
    Clasifica residuos usando Roboflow y guarda en PostgreSQL
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

        # Agregar logging adicional
        logger.info(f"Procesando imagen temporal: {temp_image_path}")
        
        # Realizar predicción
        predictions = model.predict(
            temp_image_path,
            confidence=CONFIDENCE_THRESHOLD,
            overlap=OVERLAP_THRESHOLD
        ).json()
        
        # Agregar logging de resultados
        logger.info(f"Predicciones recibidas: {predictions}")

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

            # Guardar en PostgreSQL
            conn = get_db_connection()
            if conn:
                try:
                    cur = conn.cursor()
                    for tipo, cantidad in conteo.items():
                        cur.execute("""
                            SELECT id_plastico 
                            FROM plastico 
                            WHERE nombre_plastico = %s
                        """, (tipo,))
                        resultado = cur.fetchone()
                        
                        if resultado:
                            plastico_id = resultado['id_plastico']
                            co2_ahorrado = calcular_impacto_co2(cantidad)
                            
                            cur.execute("""
                                INSERT INTO reconocimiento (
                                    fk_plastico,
                                    cantidad_plastico,
                                    cantidad_co2_plastico,
                                    fecha_reconocimiento,
                                    fk_usuario,
                                    fk_administrador
                                ) VALUES (%s, %s, %s, CURRENT_TIMESTAMP, %s, %s)
                            """, (
                                plastico_id,
                                cantidad,
                                co2_ahorrado,
                                st.session_state.user_id,
                                st.session_state.get('admin_id', None)
                            ))
                    
                    conn.commit()
                except Exception as e:
                    logger.error(f"Error guardando en base de datos: {str(e)}")
                    conn.rollback()
                finally:
                    conn.close()

            return {
                'total_botellas': len(predictions['predictions']),
                'conteo_por_tipo': dict(conteo),
                'confianza_promedio': confianzas
            }
        else:
            return {
                'total_botellas': 0,
                'conteo_por_tipo': {},
                'confianza_promedio': {}
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

# Diccionario para mapear los nombres del modelo a los nombres de la base de datos
PLASTIC_TYPE_MAPPING = {
    'HDPE Plastic': 'HDPE',
    'Single-layer Plastic': 'LDPE',
    'PET Plastic': 'PET',
    'Multi-layer Plastic': 'OTHER',
    'PVC Plastic': 'PVC',
    'PP Plastic': 'PP',
    'PS Plastic': 'PS'
}

def guardar_reconocimiento(results, user_id):
    logger.info(f"Intentando guardar reconocimiento para usuario {user_id}")
    logger.info(f"Resultados a guardar: {results}")
    
    if not user_id:
        logger.error("Error: user_id no está definido")
        return False
        
    conn = get_db_connection()
    if conn:
        try:
            cur = conn.cursor()
            for tipo, cantidad in results['conteo_por_tipo'].items():
                # Convertir el tipo de plástico al formato de la base de datos
                tipo_bd = PLASTIC_TYPE_MAPPING.get(tipo, 'OTHER')
                
                # Obtener el tipo de plástico y su valor de CO2
                cur.execute("""
                    SELECT id_plastico, valor_co2 
                    FROM plastico 
                    WHERE nombre_plastico = %s
                """, (tipo_bd,))
                
                plastico_result = cur.fetchone()
                
                if plastico_result:
                    plastico_id = plastico_result['id_plastico']
                    valor_co2 = plastico_result['valor_co2']
                    peso_plastico = cantidad * 0.03  # 30g por botella
                    co2_ahorrado = cantidad * valor_co2
                    
                    logger.info(f"""
                        Insertando reconocimiento:
                        - tipo_original: {tipo}
                        - tipo_bd: {tipo_bd}
                        - plastico_id: {plastico_id}
                        - peso_plastico: {peso_plastico}
                        - cantidad: {cantidad}
                        - co2_ahorrado: {co2_ahorrado}
                        - user_id: {user_id}
                    """)
                    
                    cur.execute("""
                        INSERT INTO reconocimiento (
                            fk_plastico,
                            peso_plastico,
                            cantidad_plastico,
                            cantidad_co2_plastico,
                            fecha_reconocimiento,
                            fk_usuario
                        ) VALUES (%s, %s, %s, %s, CURRENT_TIMESTAMP, %s)
                    """, (
                        plastico_id,
                        peso_plastico,
                        cantidad,
                        co2_ahorrado,
                        user_id
                    ))
                    
                else:
                    logger.error(f"No se encontró el tipo de plástico en BD: {tipo_bd} (original: {tipo})")
                    st.error(f"Tipo de plástico no encontrado: {tipo_bd}")
                    
            conn.commit()
            logger.info("Commit realizado exitosamente")
            return True
            
        except Exception as e:
            conn.rollback()
            logger.error(f"Error al guardar reconocimiento: {str(e)}")
            st.error(f"Error al guardar reconocimiento: {str(e)}")
            return False
        finally:
            conn.close()
            logger.info("Conexión cerrada")
    else:
        logger.error("No se pudo establecer conexión con la base de datos")
        st.error("Error de conexión con la base de datos")
    return False

def mostrar_reconocimiento_residuos(username: str):
    st.write(f"Reconocimiento de residuos para el usuario: {username}")
    
    metodo_entrada = st.radio(
        "Selecciona cómo quieres subir tu imagen:",
        ["Tomar foto con la cámara", "Subir imagen desde el dispositivo"],
        horizontal=True
    )
    
    image_data = None
    
    if metodo_entrada == "Tomar foto con la cámara":
        image_data = st.camera_input("Tomar una foto")
    else:
        image_data = st.file_uploader("Elige una imagen...", type=['jpg', 'jpeg', 'png'])
    
    if image_data is not None:
        try:
            st.image(image_data, caption="Imagen a analizar", use_container_width=True)
            
            with st.spinner("🔍 Analizando imagen..."):
                results = classify_waste(image_data)
            
            if results and results['total_botellas'] > 0:
                st.success("✅ ¡Imagen analizada con éxito!")
                
                st.write("### 📊 Resultados del análisis")
                st.write(f"Total de botellas detectadas: {results['total_botellas']}")
                
                for tipo, cantidad in results['conteo_por_tipo'].items():
                    st.write(f"- {tipo}: {cantidad}")
                
                # Guardar resultados en la base de datos
                if guardar_reconocimiento(results, st.session_state.user_id):
                    st.success("✅ Datos guardados correctamente")
                    
                    # Calcular impacto ambiental
                    total_co2 = sum(cantidad * 0.5 for cantidad in results['conteo_por_tipo'].values())
                    st.write("### 🌱 Impacto Ambiental")
                    st.write(f"CO2 ahorrado: {total_co2:.2f} kg")
                else:
                    st.error("❌ Error al guardar los datos")
            else:
                st.warning("⚠️ No se detectaron botellas en la imagen")
                
        except Exception as e:
            st.error(f"❌ Error al procesar la imagen: {str(e)}")

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