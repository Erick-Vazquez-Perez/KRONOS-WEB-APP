"""
Interfaz para gestión de días festivos
"""
import streamlit as st
import json
from datetime import datetime, date
from anomaly_detector import HOLIDAYS

def manage_holidays_interface():
    """Interfaz para gestionar días festivos"""
    st.subheader("Gestión de Días Festivos")
    
    # Selector de año
    current_year = datetime.now().year
    years = list(range(current_year - 1, current_year + 3))
    selected_year = st.selectbox("Seleccionar año:", years, index=1)
    
    # Mostrar festivos existentes
    st.markdown("### Festivos configurados")
    
    if selected_year in HOLIDAYS:
        existing_holidays = HOLIDAYS[selected_year]
        
        if existing_holidays:
            for i, (holiday_date, description) in enumerate(existing_holidays):
                col1, col2, col3 = st.columns([2, 3, 1])
                
                with col1:
                    st.text(holiday_date)
                
                with col2:
                    st.text(description)
                
                with col3:
                    if st.button("Eliminar", key=f"delete_{i}_{selected_year}"):
                        # Aquí se implementaría la eliminación
                        st.warning("Funcionalidad de eliminación pendiente de implementar")
        else:
            st.info("No hay festivos configurados para este año")
    else:
        st.info("No hay festivos configurados para este año")
    
    # Agregar nuevo festivo
    st.markdown("### Agregar nuevo festivo")
    
    col1, col2 = st.columns(2)
    
    with col1:
        new_date = st.date_input(
            "Fecha del festivo:",
            min_value=date(selected_year, 1, 1),
            max_value=date(selected_year, 12, 31),
            value=date(selected_year, 1, 1)
        )
    
    with col2:
        new_description = st.text_input("Descripción del festivo:")
    
    if st.button("Agregar festivo"):
        if new_description.strip():
            st.success(f"Festivo agregado: {new_date.strftime('%Y-%m-%d')} - {new_description}")
            st.info("Nota: Esta funcionalidad requiere reiniciar la aplicación para verse reflejada en el código.")
            
            # Mostrar el código que se debería agregar
            st.code(f'("{new_date.strftime("%Y-%m-%d")}", "{new_description}"),')
            st.caption("Agrega esta línea al archivo anomaly_detector.py en la sección HOLIDAYS del año correspondiente")
        else:
            st.error("Por favor, ingresa una descripción para el festivo")
    
    # Información adicional
    with st.expander("Información sobre festivos"):
        st.markdown("""
        **¿Cómo funciona la detección de festivos?**
        
        1. **Configuración manual**: Los festivos se configuran manualmente en el código
        2. **Detección automática**: El sistema detecta automáticamente cuando las fechas de albaranado de los clientes caen en días festivos
        3. **Alertas**: Se muestran alertas para todos los clientes cuyas fechas de albaranado coincidan con festivos
        
        **Tipos de festivos detectados:**
        - Festivos nacionales (Año Nuevo, Día del Trabajo, etc.)
        - Festivos locales configurados manualmente
        - Puentes y días no laborables específicos
        
        **Recomendaciones:**
        - Revisa regularmente las fechas de albaranado que caen en festivos
        - Considera reprogramar entregas cuando sea necesario
        - Coordina con proveedores para fechas alternativas
        """)

def show_current_month_analysis():
    """Muestra análisis detallado del mes actual"""
    from anomaly_detector import get_incomplete_weeks_info, get_holidays_for_month
    
    current_date = datetime.now()
    current_year = current_date.year
    current_month = current_date.month
    current_month_name = current_date.strftime('%B')
    
    st.subheader(f"Análisis de {current_month_name} {current_year}")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("#### Información del mes")
        
        # Información de semanas incompletas
        week_info = get_incomplete_weeks_info(current_year, current_month)
        
        if week_info['affected_weekdays']:
            st.warning(f"**Semanas incompletas detectadas**")
            st.write(f"Días que pueden verse afectados: {', '.join(week_info['affected_weekdays'])}")
            
            if week_info['first_week_present']:
                st.write(f"Primera semana solo tiene: {', '.join(week_info['first_week_present'])}")
            
            if week_info['last_week_present']:
                st.write(f"Última semana solo tiene: {', '.join(week_info['last_week_present'])}")
                
            st.caption("Los días en semanas incompletas pueden tener menos oportunidades para cumplir frecuencias semanales.")
        else:
            st.success("No hay semanas incompletas este mes")
    
    with col2:
        st.markdown("#### Festivos del mes")
        
        holidays = get_holidays_for_month(current_year, current_month)
        
        if holidays:
            st.warning(f"**{len(holidays)} festivo(s) detectado(s)**")
            for holiday_date, description in holidays:
                st.write(f"{holiday_date.strftime('%d/%m/%Y')} - {description}")
        else:
            st.success("No hay festivos configurados este mes")
    
    # Recomendaciones
    st.markdown("#### Recomendaciones")
    
    recommendations = []
    
    if week_info['affected_weekdays']:
        affected_days = ', '.join(week_info['affected_weekdays'])
        recommendations.append(f"Revisar clientes con frecuencias de {affected_days} por semanas incompletas")
    
    if holidays:
        holiday_dates = [h[0].strftime('%d/%m') for h in holidays]
        recommendations.append(f"Verificar albaranados programados para {', '.join(holiday_dates)}")
    
    if not recommendations:
        recommendations.append("No se detectaron problemas potenciales para este mes")
    
    for i, rec in enumerate(recommendations, 1):
        st.write(f"{i}. {rec}")

if __name__ == "__main__":
    # Ejemplo de uso
    manage_holidays_interface()
    st.markdown("---")
    show_current_month_analysis()
