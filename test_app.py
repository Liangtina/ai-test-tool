
    def test_power(self):
        self.assertEqual(self.calc.power(2, 3), 8)
        self.assertEqual(self.calc.power(5, 0), 1)
        self.assertEqual(self.calc.power(4, 0.5), 2.0)

    def test_sqrt(self):
        self.assertEqual(self.calc.sqrt(16), 4)
        self.assertEqual(self.calc.sqrt(2), math.sqrt(2))
        with self.assertRaises(ValueError):
            self.calc.sqrt(-1)
