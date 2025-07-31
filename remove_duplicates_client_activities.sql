-- Script SQL para eliminar duplicados en la tabla client_activities
-- Este script mantiene solo el registro más antiguo (ID más bajo) para cada combinación de client_id y activity_name

-- Paso 1: Consulta para verificar duplicados antes de eliminar
-- Ejecuta esta consulta primero para ver cuántos duplicados hay
SELECT 
    client_id,
    activity_name,
    COUNT(*) as cantidad_duplicados,
    GROUP_CONCAT(id) as ids_duplicados
FROM client_activities 
GROUP BY client_id, activity_name 
HAVING COUNT(*) > 1
ORDER BY client_id, activity_name;

-- Paso 2: Eliminar duplicados manteniendo solo el registro con ID más pequeño
-- IMPORTANTE: Haz un backup de la base de datos antes de ejecutar este DELETE

DELETE FROM client_activities 
WHERE id NOT IN (
    SELECT MIN(id) 
    FROM client_activities 
    GROUP BY client_id, activity_name
);

-- Paso 3: Verificar que ya no hay duplicados (debe devolver 0 filas)
SELECT 
    client_id,
    activity_name,
    COUNT(*) as cantidad_duplicados
FROM client_activities 
GROUP BY client_id, activity_name 
HAVING COUNT(*) > 1
ORDER BY client_id, activity_name;

-- Paso 4: Agregar constraint único para evitar futuros duplicados (opcional)
-- Nota: Solo ejecuta esto si quieres prevenir duplicados en el futuro
-- CREATE UNIQUE INDEX idx_client_activity_unique ON client_activities (client_id, activity_name);

-- Paso 5: Consulta final para verificar el estado de la tabla
SELECT 
    COUNT(*) as total_registros,
    COUNT(DISTINCT client_id || '_' || activity_name) as combinaciones_unicas
FROM client_activities;
