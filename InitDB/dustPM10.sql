-- Definizione della tabella "dustPM10_kafka" per l'input dei dati provenienti da Kafka
CREATE TABLE innovacity.dustPM10_kafka (
    timestamp DATETIME64,
    value Float32,
    latitude Float64,
    longitude Float64,
    ID_sensore String,
    cella String
) ENGINE = Kafka(
    'kafka:9092',
    'dust_level_PM10',
    'CG_Clickhouse_1',
    'JSONEachRow'
);


CREATE TABLE innovacity.dustPM10
(
    ID_sensore String,
    cella String,
    timestamp DATETIME64,
    value Float32,
    latitude Float64,
    longitude Float64
)
ENGINE = MergeTree()
ORDER BY (ID_sensore, timestamp);


CREATE MATERIALIZED VIEW mv_dustPM10 TO innovacity.dustPM10
AS SELECT * FROM innovacity.dustPM10_kafka;

ALTER TABLE innovacity.dustPM10 ADD PROJECTION dust_sensor_cell_projection (SELECT * ORDER BY cella);

ALTER TABLE innovacity.dustPM10 MATERIALIZE PROJECTION dust_sensor_cell_projection;