import unittest
from path1 import Drone

class TestDroneSecureProxy(unittest.TestCase):
    def setUp(self):
        self.drone = Drone()

    def test_takeoff_on_True(self):
        res = self.drone.takeoff()
        self.assertEqual(res, "Дрон взлетает")
        
    def test_takeoff_on_False(self):
        res = self.drone.takeoff()
        self.assertNotEqual(res, "взлет не разрешен")
       
    def test_land_on_True(self):
        res = self.drone.land() 
        self.assertEqual(res, "Дрон приземлился")
    
    def test_land_on_False(self):
        res = self.drone.land() 
        self.assertNotEqual(res, "Drone уже на земле")
 
   
if __name__ == "__main__":
    unittest.main()  