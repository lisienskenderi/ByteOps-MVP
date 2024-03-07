import os
import time
from datetime import datetime
import pytest
import clickhouse_connect

from ..Model.Simulators.Coordinate import Coordinate
from ..Model.Simulators.Misurazione import Misurazione
from ..Model.Writers.KafkaWriter import KafkaWriter
from ..Model.Writers.kafkaAdapter.KafkaConfluentAdapter import KafkaConfluentAdapter
from ..Model.AdapterMisurazione import AdapterMisurazione

KAFKA_HOST = os.environ.get("KAFKA_HOST", "kafka")
KAFKA_PORT = os.environ.get("KAFKA_PORT", "9092")
test_topic = "temperature"
table_to_test = "temperatures"

@pytest.fixture(scope='module')
def clickhouse_client():
    # Set up ClickHouse client
    client = clickhouse_connect.get_client(host='clickhouse', port=8123, database="innovacity")
    yield client
    # Teardown: Close connection after all tests in the module have run
    client.close()

@pytest.fixture
def kafka_writer():
    """
    This function creates a Kafka writer object and yields it.

    Returns:
        KafkaWriter: The Kafka writer object.
    """
    adapter_kafka = KafkaConfluentAdapter(test_topic, KAFKA_HOST, KAFKA_PORT)
    kafka_writer = KafkaWriter(adapter_kafka)
    yield kafka_writer

@pytest.mark.asyncio
async def test_outOfBound_misurazione(clickhouse_client, kafka_writer):
    try:
        timestamp = datetime.now()
        low_bound_limit = -50 
        upper_bound_limit = 50
        sensor_data = [
            {"id": "Id_1_test_correct", "value": 45},
            {"id": "Id_1_test_error", "value": 51}
        ]

        for data in sensor_data:
            misurazione = AdapterMisurazione(
                Misurazione(timestamp, data["value"], "Temperature", Coordinate(45.39214, 11.859271), data["id"], "Arcella1"))
            kafka_writer.write(misurazione)

        kafka_writer.flush_kafka_producer()
        time.sleep(5)

        for data in sensor_data:
            result = clickhouse_client.query(f"SELECT * FROM innovacity.{table_to_test} where ID_sensore ='{data['id']}' and timestamp = '{str(timestamp)}' LIMIT 1")
            if(data["value"] > low_bound_limit and data["value"] < upper_bound_limit):
                assert len(result.result_rows) == 1
                assert float(result.result_rows[0][3]) == data["value"]
                assert str(timestamp)[:22] == str(result.result_rows[0][2])[:22]
            else:
                assert not result.result_rows

    except Exception as e:
        pytest.fail(f"Failed to connect to ClickHouse database: {e}")
"""
@pytest.mark.asyncio
async def test_multiple_misurazioni(clickhouse_client):
    try:
        adapter_kafka = KafkaConfluentAdapter(test_topic, KAFKA_HOST, KAFKA_PORT)
        kafka_writer = KafkaWriter(adapter_kafka)
        num_messages = 100  # Number of messages to send
        # Send data to Kafka
        starting_value = 0
        timestamps = []
        values = []
        for i in range(num_messages):
            timestamp = datetime.now()
            timestamps.append(timestamp)
            values.append(starting_value + i/10)
            misurazione = AdapterMisurazione(
                            Misurazione(timestamp, values[i] , "Temperature", Coordinate(45.39214, 11.859271), "Id_multi_mis_test", "ArcellaTest"))
            kafka_writer.write(misurazione)
        kafka_writer.flush_kafka_producer()
        time.sleep(15)
        # Query ClickHouse to check if all data has been inserted
        result = clickhouse_client.query(f"SELECT * FROM innovacity.{table_to_test} where ID_sensore ='Id_multi_mis_test' ORDER BY (timestamp,value) DESC LIMIT {num_messages}")
       # #print(result.result_rows)
        for i in range(num_messages):
            assert (values[num_messages - 1 -i]) == (round(float(result.result_rows[i][3]),1))
            assert str(timestamps[num_messages -1 -i])[:22] == str(result.result_rows[i][2])[:22]
    except Exception as e:
        pytest.fail(f"Failed to send and consume data: {e}")"""
