CREATE TABLE innovacity.electricalFault_kafka (
    timestamp DATETIME64,
    value UInt8,
    latitude Float64,
    longitude Float64,
    ID_sensore String,
    cella String
) ENGINE = Kafka(
    'kafka:9092',
    'electrical_fault',
    'CG_Clickhouse_1',
    'JSONEachRow'
);


CREATE TABLE innovacity.electricalFault
(
    ID_sensore String,
    cella String,
    timestamp DATETIME64,
    value UInt8,
    latitude Float64,
    longitude Float64
)
ENGINE = MergeTree()
ORDER BY (ID_sensore, timestamp);


CREATE MATERIALIZED VIEW mv_electricalFault TO innovacity.electricalFault
AS SELECT * FROM innovacity.electricalFault_kafka;


--Da valutare se ha senso tenere nei valori binari
ALTER TABLE innovacity.electricalFault ADD PROJECTION elctF_sensor_cell_projection (SELECT * ORDER BY cella);

ALTER TABLE innovacity.electricalFault MATERIALIZE PROJECTION elctF_sensor_cell_projection;