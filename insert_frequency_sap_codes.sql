-- Script para insertar o actualizar frecuencias con códigos SAP
-- Este script asegura que todas las frecuencias tengan su código SAP correspondiente

-- Actualizar frecuencias existentes con códigos SAP
UPDATE frequency_templates SET calendario_sap_code = '16' WHERE name = '2do Lunes del mes';
UPDATE frequency_templates SET calendario_sap_code = 'M7' WHERE name = '1er y 3er Lunes del mes';
UPDATE frequency_templates SET calendario_sap_code = '17' WHERE name = '1er Viernes del mes';
UPDATE frequency_templates SET calendario_sap_code = '18' WHERE name = '1er y 3er Jueves del mes';
UPDATE frequency_templates SET calendario_sap_code = '19' WHERE name = '3er Lunes del mes';
UPDATE frequency_templates SET calendario_sap_code = '20' WHERE name = '2do Martes del mes';
UPDATE frequency_templates SET calendario_sap_code = 'ME' WHERE name = '2do y 4to Miércoles del mes';
UPDATE frequency_templates SET calendario_sap_code = 'MD' WHERE name = '1er y 3er Miércoles del mes';
UPDATE frequency_templates SET calendario_sap_code = '21' WHERE name = '3er Martes del mes';
UPDATE frequency_templates SET calendario_sap_code = '22' WHERE name = '2do y 4to Jueves del mes';
UPDATE frequency_templates SET calendario_sap_code = '23' WHERE name = '1er Miércoles del mes';
UPDATE frequency_templates SET calendario_sap_code = '24' WHERE name = '2do y 4to Lunes del mes';
UPDATE frequency_templates SET calendario_sap_code = 'M9' WHERE name = 'Martes de cada semana';
UPDATE frequency_templates SET calendario_sap_code = '25' WHERE name = '3er Miércoles del mes';
UPDATE frequency_templates SET calendario_sap_code = '26' WHERE name = '3er Jueves del mes';
UPDATE frequency_templates SET calendario_sap_code = '27' WHERE name = '4to Jueves del mes';
UPDATE frequency_templates SET calendario_sap_code = '28' WHERE name = '2do Miércoles del mes';
UPDATE frequency_templates SET calendario_sap_code = '29' WHERE name = '1er Martes del mes';
UPDATE frequency_templates SET calendario_sap_code = 'M8' WHERE name = 'Lunes de cada semana';
UPDATE frequency_templates SET calendario_sap_code = '30' WHERE name = '2do Viernes del mes';
UPDATE frequency_templates SET calendario_sap_code = 'MB' WHERE name = '1er y 3er Martes del mes';
UPDATE frequency_templates SET calendario_sap_code = '31' WHERE name = '4to Viernes del mes';
UPDATE frequency_templates SET calendario_sap_code = '32' WHERE name = '1er 2do y 3er Lunes del mes';
UPDATE frequency_templates SET calendario_sap_code = '33' WHERE name = '3er Viernes del mes';
UPDATE frequency_templates SET calendario_sap_code = '34' WHERE name = '1er y 2do Lunes del mes';
UPDATE frequency_templates SET calendario_sap_code = 'M3' WHERE name = 'Miércoles de cada semana';
UPDATE frequency_templates SET calendario_sap_code = 'M4' WHERE name = 'Jueves de cada semana';
UPDATE frequency_templates SET calendario_sap_code = '35' WHERE name = '1er Lunes del mes';

-- Insertar frecuencias que no existen con sus respectivos códigos SAP
INSERT OR IGNORE INTO frequency_templates (name, frequency_type, frequency_config, description, calendario_sap_code)
VALUES 
    ('2do Lunes del mes', 'monthly', '{"nth": 2, "day": "monday"}', 'Segundo lunes de cada mes', '16'),
    ('1er y 3er Lunes del mes', 'monthly', '{"nth": [1,3], "day": "monday"}', 'Primer y tercer lunes de cada mes', 'M7'),
    ('1er Viernes del mes', 'monthly', '{"nth": 1, "day": "friday"}', 'Primer viernes de cada mes', '17'),
    ('1er y 3er Jueves del mes', 'monthly', '{"nth": [1,3], "day": "thursday"}', 'Primer y tercer jueves de cada mes', '18'),
    ('3er Lunes del mes', 'monthly', '{"nth": 3, "day": "monday"}', 'Tercer lunes de cada mes', '19'),
    ('2do Martes del mes', 'monthly', '{"nth": 2, "day": "tuesday"}', 'Segundo martes de cada mes', '20'),
    ('2do y 4to Miércoles del mes', 'monthly', '{"nth": [2,4], "day": "wednesday"}', 'Segundo y cuarto miércoles de cada mes', 'ME'),
    ('1er y 3er Miércoles del mes', 'monthly', '{"nth": [1,3], "day": "wednesday"}', 'Primer y tercer miércoles de cada mes', 'MD'),
    ('3er Martes del mes', 'monthly', '{"nth": 3, "day": "tuesday"}', 'Tercer martes de cada mes', '21'),
    ('2do y 4to Jueves del mes', 'monthly', '{"nth": [2,4], "day": "thursday"}', 'Segundo y cuarto jueves de cada mes', '22'),
    ('1er Miércoles del mes', 'monthly', '{"nth": 1, "day": "wednesday"}', 'Primer miércoles de cada mes', '23'),
    ('2do y 4to Lunes del mes', 'monthly', '{"nth": [2,4], "day": "monday"}', 'Segundo y cuarto lunes de cada mes', '24'),
    ('Martes de cada semana', 'weekly', '{"day": "tuesday"}', 'Todos los martes', 'M9'),
    ('3er Miércoles del mes', 'monthly', '{"nth": 3, "day": "wednesday"}', 'Tercer miércoles de cada mes', '25'),
    ('3er Jueves del mes', 'monthly', '{"nth": 3, "day": "thursday"}', 'Tercer jueves de cada mes', '26'),
    ('4to Jueves del mes', 'monthly', '{"nth": 4, "day": "thursday"}', 'Cuarto jueves de cada mes', '27'),
    ('2do Miércoles del mes', 'monthly', '{"nth": 2, "day": "wednesday"}', 'Segundo miércoles de cada mes', '28'),
    ('1er Martes del mes', 'monthly', '{"nth": 1, "day": "tuesday"}', 'Primer martes de cada mes', '29'),
    ('Lunes de cada semana', 'weekly', '{"day": "monday"}', 'Todos los lunes', 'M8'),
    ('2do Viernes del mes', 'monthly', '{"nth": 2, "day": "friday"}', 'Segundo viernes de cada mes', '30'),
    ('1er y 3er Martes del mes', 'monthly', '{"nth": [1,3], "day": "tuesday"}', 'Primer y tercer martes de cada mes', 'MB'),
    ('4to Viernes del mes', 'monthly', '{"nth": 4, "day": "friday"}', 'Cuarto viernes de cada mes', '31'),
    ('1er 2do y 3er Lunes del mes', 'monthly', '{"nth": [1,2,3], "day": "monday"}', 'Primer, segundo y tercer lunes de cada mes', '32'),
    ('3er Viernes del mes', 'monthly', '{"nth": 3, "day": "friday"}', 'Tercer viernes de cada mes', '33'),
    ('1er y 2do Lunes del mes', 'monthly', '{"nth": [1,2], "day": "monday"}', 'Primer y segundo lunes de cada mes', '34'),
    ('Miércoles de cada semana', 'weekly', '{"day": "wednesday"}', 'Todos los miércoles', 'M3'),
    ('Jueves de cada semana', 'weekly', '{"day": "thursday"}', 'Todos los jueves', 'M4'),
    ('1er Lunes del mes', 'monthly', '{"nth": 1, "day": "monday"}', 'Primer lunes de cada mes', '35');

-- Verificar el resultado
SELECT name, calendario_sap_code FROM frequency_templates ORDER BY name;
