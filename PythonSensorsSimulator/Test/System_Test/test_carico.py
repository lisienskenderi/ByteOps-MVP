# pylint: skip-file
import os
from datetime import datetime
import asyncio
import pytest
import clickhouse_connect

from ...Model.Simulators.Coordinate import Coordinate
from ...Model.Simulators.Misurazione import Misurazione
from ...Model.Writers.KafkaWriter import KafkaWriter
from ...Model.Writers.kafkaAdapter.KafkaConfluentAdapter import KafkaConfluentAdapter
from ...Model.Writers.CompositeWriter import CompositeWriter
from ...Model.Writers.ListWriter import ListWriter
from ...Model.Simulators.SensorTypes import SensorTypes

from ...Model.Simulators.SensorFactory import SensorFactory
from ...Model.SimulatorExecutorFactory import SimulatorExecutorFactory
from ...Model.AdapterMisurazione import AdapterMisurazione

KAFKA_HOST = os.environ.get("KAFKA_HOST", "kafka")
KAFKA_PORT = os.environ.get("KAFKA_PORT", "9092")
test_topic = "test"
table_to_test = "test"

@pytest.fixture(scope='module')
def clickhouse_client():
    client = clickhouse_connect.get_client(host='clickhouse', port=8123, database="innovacity")
    yield client
    client.close()

@pytest.fixture(scope='module')
def kafka_writer():
    adapter_kafka = KafkaConfluentAdapter(test_topic, KAFKA_HOST, KAFKA_PORT)
    kafka_writer = KafkaWriter(adapter_kafka)
    yield kafka_writer

@pytest.mark.asyncio
async def test_multiple_misurazioni(clickhouse_client,kafka_writer):
    try:
        num_messages = 10000  # Number of messages to send
        starting_value = 0
        timestamps = []
        for i in range(num_messages):
            timestamp = datetime.now()
            timestamps.append(timestamp)
            misurazione = AdapterMisurazione(
                            Misurazione(timestamp, starting_value + i, "Temperature", Coordinate(45.39214, 11.859271), "id_t_carico", "T_carico_cell"))
            kafka_writer.write(misurazione)
        kafka_writer.flush_kafka_producer()
        
        query = f"SELECT * FROM innovacity.{table_to_test} where ID_sensore ='id_t_carico' and timestamp >= '{timestamps[0]}'  ORDER BY (timestamp,value) DESC LIMIT {num_messages}"
        result = clickhouse_client.query(query)
        iter = 0
        max_seconds_to_wait = 10
        intervallo_sleep = 0.5
        while (len(result.result_rows) < num_messages) and (iter * intervallo_sleep < max_seconds_to_wait):
            await asyncio.sleep(intervallo_sleep)
            result = clickhouse_client.query(query)
            iter += 1
        #print(len(result.result_rows))
        #print(result.result_rows)
        for i in range(num_messages):
            assert (starting_value + num_messages - 1 -i) == float(result.result_rows[i][3])
            assert timestamps[num_messages -1 -i] == result.result_rows[i][2]
    except Exception as e:
        pytest.fail(f"Failed to send and consume data: {e}")

@pytest.mark.asyncio
async def test_RV1(clickhouse_client):
    KAFKA_HOST = "kafka"
    KAFKA_PORT = "9092"
    try:
        list_measure = ListWriter()
        temp_writers = CompositeWriter().add_kafkaConfluent_writer("temperature", KAFKA_HOST, KAFKA_PORT).add_list_writer(list_measure)
        umd_writers = CompositeWriter().add_kafkaConfluent_writer("humidity", KAFKA_HOST, KAFKA_PORT).add_list_writer(list_measure)
        chS_writers = CompositeWriter().add_kafkaConfluent_writer("chargingStation", KAFKA_HOST, KAFKA_PORT).add_list_writer(list_measure)
        ecoIs_writers = CompositeWriter().add_kafkaConfluent_writer("ecologicalIsland", KAFKA_HOST, KAFKA_PORT).add_list_writer(list_measure)
        waPr_writers = CompositeWriter().add_kafkaConfluent_writer("waterPresence", KAFKA_HOST, KAFKA_PORT).add_list_writer(list_measure)
        dust_writers = CompositeWriter().add_kafkaConfluent_writer("dust_level_PM10", KAFKA_HOST, KAFKA_PORT).add_list_writer(list_measure)
        eletricalFault_writers = CompositeWriter().add_kafkaConfluent_writer("electrical_fault", KAFKA_HOST, KAFKA_PORT).add_list_writer(list_measure)
        symExecAggregator = SimulatorExecutorFactory()
        num_messages = 1
        num_sensor_per_type = 10
        for i in range(num_sensor_per_type):
            symExecAggregator.add_simulator(SensorFactory.create_temperature_sensor(45.4065, 11.8793, "Test_cell_carico"), temp_writers, 0.01,num_messages)
        for i in range(num_sensor_per_type):
            symExecAggregator.add_simulator(SensorFactory.create_humidity_sensor(45.4068, 11.8794, "Test_cell_carico"), umd_writers, 0.01,num_messages)
        for i in range(num_sensor_per_type):
            symExecAggregator.add_simulator(SensorFactory.create_charging_station_sensor(45.4059, 11.8785, "Test_cell_carico"), chS_writers, 0.01,num_messages)
        for i in range(num_sensor_per_type):
            symExecAggregator.add_simulator(SensorFactory.create_ecological_island_sensor(45.4045, 11.8797, "Test_cell_carico"), ecoIs_writers, 0.01,num_messages)
        for i in range(num_sensor_per_type):
            symExecAggregator.add_simulator(SensorFactory.create_water_presence_sensor(45.4070, 11.8805, "Test_cell_carico"), waPr_writers, 0.01,num_messages)
        for i in range(num_sensor_per_type):
            symExecAggregator.add_simulator(SensorFactory.create_dust_PM10_sensor(45.4069, 11.8800, "Test_cell_carico"), dust_writers, 0.01,num_messages)
        for i in range(num_sensor_per_type):
            symExecAggregator.add_simulator(SensorFactory.create_eletrical_fault_sensor(45.4056, 11.8788, "Test_cell_carico"), eletricalFault_writers, 0.01,num_messages)
        symExecAggregator.run()
        while len(list_measure.get_data_list()) < num_messages*num_sensor_per_type*6:
            await asyncio.sleep(1)
        await asyncio.sleep(10)
        symExecAggregator.stop()

        tmp_table = "temperatures"
        umd_table = "humidity"
        chS_table = "chargingStations"
        ecoIs_table = "ecoIslands"
        waPr_table = "waterPresence"
        dust_table = "dustPM10"
        eletricalFault_table = "electricalFault"
        measure_arrived = []
        # Query ClickHouse to check if all data has been inserted
        result_tmp = clickhouse_client.query(f"SELECT * FROM innovacity.{tmp_table} where cella ='Test_cell_carico' ORDER BY timestamp DESC LIMIT {num_messages*num_sensor_per_type}")
        for measure in result_tmp.result_rows:
            measure_arrived.append(Misurazione(measure[2],measure[3],SensorTypes.TEMPERATURE.value,Coordinate(measure[4],measure[5]) ,measure[0],measure[1]))

        result_umd = clickhouse_client.query(f"SELECT * FROM innovacity.{umd_table} where cella ='Test_cell_carico' ORDER BY timestamp DESC LIMIT {num_messages*num_sensor_per_type}")
        for measure in result_umd.result_rows:
            measure_arrived.append(Misurazione(measure[2],measure[3],SensorTypes.HUMIDITY.value,Coordinate(measure[4],measure[5]) ,measure[0],measure[1]))

        result_chS = clickhouse_client.query(f"SELECT * FROM innovacity.{chS_table} where cella ='Test_cell_carico' ORDER BY timestamp DESC LIMIT {num_messages*num_sensor_per_type}")
        for measure in result_chS.result_rows:
            measure_arrived.append(Misurazione(measure[2],measure[3],SensorTypes.CHARGING_STATION.value,Coordinate(measure[4],measure[5]) ,measure[0],measure[1]))

        result_ecoIs = clickhouse_client.query(f"SELECT * FROM innovacity.{ecoIs_table} where cella ='Test_cell_carico' ORDER BY timestamp DESC LIMIT {num_messages*num_sensor_per_type}")
        for measure in result_ecoIs.result_rows:
            measure_arrived.append(Misurazione(measure[2],measure[3],SensorTypes.ECOLOGICAL_ISLAND.value,Coordinate(measure[4],measure[5]) ,measure[0],measure[1]))

        result_waPr = clickhouse_client.query(f"SELECT * FROM innovacity.{waPr_table} where cella ='Test_cell_carico' ORDER BY timestamp DESC LIMIT {num_messages*num_sensor_per_type}")
        for measure in result_waPr.result_rows:
            measure_arrived.append(Misurazione(measure[2],measure[3],SensorTypes.WATER_PRESENCE.value,Coordinate(measure[4],measure[5]) ,measure[0],measure[1]))

        result_dust = clickhouse_client.query(f"SELECT * FROM innovacity.{dust_table} where cella ='Test_cell_carico' ORDER BY timestamp DESC LIMIT {num_messages*num_sensor_per_type}")
        for measure in result_dust.result_rows:
            measure_arrived.append(Misurazione(measure[2],measure[3],SensorTypes.DUST_PM10.value,Coordinate(measure[4],measure[5]) ,measure[0],measure[1]))

        result_eletricalFault = clickhouse_client.query(f"SELECT * FROM innovacity.{eletricalFault_table} where cella ='Test_cell_carico' ORDER BY timestamp DESC LIMIT {num_messages*num_sensor_per_type}")
        for measure in result_eletricalFault.result_rows:
            measure_arrived.append(Misurazione(measure[2],measure[3],SensorTypes.ELECTRICAL_FAULT.value,Coordinate(measure[4],measure[5]) ,measure[0],measure[1]))

        str_measure = []
        for measure in measure_arrived:
            str_measure.append(measure.to_string())

        for measure in list_measure.get_data_list():
            assert measure.get_Misurazione().to_string() in str_measure


       
    except Exception as e:
        pytest.fail(f"Failed to send and consume data: {e}")