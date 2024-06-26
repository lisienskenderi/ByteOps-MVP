import unittest
from unittest.mock import Mock
from ..HealthStateModel.misurazione import misurazione


class test_misurazione(unittest.TestCase):
    def setUp(self):
        mock_coordinates = Mock()
        mock_coordinates.get_latitude.return_value = 40.7128
        mock_coordinates.get_longitude.return_value = -74.0060

        self.misurazione = misurazione(
            timestamp = "2024-03-13 15:30:00",
            value = 42.5,
            type_ = "Temperature",
            coord = mock_coordinates,
            ID_sensore = "Sensor123",
            cella = "CellA"
        )

    def test_get_timestamp(self):
        self.assertEqual(self.misurazione.get_timestamp(), "2024-03-13 15:30:00")

    def test_get_value(self):
        self.assertEqual(self.misurazione.get_value(), 42.5)

    def test_get_type(self):
        self.assertEqual(self.misurazione.get_type(), "Temperature")

    def test_get_latitude(self):
        self.assertEqual(self.misurazione.get_latitude(), 40.7128)

    def test_get_longitude(self):
        self.assertEqual(self.misurazione.get_longitude(), -74.0060)

    def test_get_ID_sensore(self):
        self.assertEqual(self.misurazione.get_ID_sensore(), "Sensor123")

    def test_get_cella(self):
        self.assertEqual(self.misurazione.get_cella(), "CellA")


if __name__ == "__main__":
    unittest.main()
