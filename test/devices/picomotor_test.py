import unittest
from plico_motor_server.devices.picomotor import Picomotor


class TestPicomotor(unittest.TestCase):

    def setUp(self):
        self.ip = 'localhost'
        self.picomotor = Picomotor(self.ip, timeout=2, name='foo')

    def test_creation(self):
        self.assertEqual(self.ip, self.picomotor.ipaddr)


if __name__ == "__main__":
    unittest.main()
