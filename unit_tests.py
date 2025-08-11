from txt_to_pandas_dataframe import *
import unittest

class Test_data_Processing(unittest.TestCase):
    """
    This class contains the unit tests (Still in process of adding some)
    """
    data = text_to_pandas_dataframe("mahdy3-op-by-day_to-08jun25.txt")
    data_integrity_check(data)

    start_date = "16-Apr-1991"
    end_date   = "28-Jul-1991"
    off_date   = "01-Jan-1991"
    wrong_date = "13-Sep-1341"
    
    def test_basic_single_date_get_integrated_current(self):
        """
        Tests to see whether the a succesful current is gathered for a known valid date
        """
        integrated_current = get_integrated_current(self.data, self.start_date)
        
        self.assertIsNotNone(integrated_current)
    def test_basic_dates_get_integrated_current(self):
        """
        Tests to see whether succesful currents are gathered for a known valid range of dates
        """
        integrated_current = get_integrated_current(self.data, self.start_date, self.end_date)
        
        self.assertIsNotNone(integrated_current)
    def test_summing_dates_get_integrated_current(self):
        """
        Tests to see whether succesful currents are gathered and summed for a known valid range of dates
        """
        integrated_currents    = get_integrated_current(self.data, self.start_date, self.end_date)
        integrated_current_sum = get_integrated_current(self.data, self.start_date, self.end_date, is_summed=True)
        
        self.assertEqual(integrated_currents.sum(), integrated_current_sum)
    def test_is_beam_on(self):
        """
        Tests to see whether the code is properly registering the beam being on or off on known days
        where it is either on or off
        """
        self.assertTrue(is_beam_on(self.data, self.start_date))
        self.assertFalse(is_beam_on(self.data, self.off_date))
    def test_condensed_data_size(self):
        """
        Tests the size of the collected data
        """
        daily   = get_integrated_current(self.data, self.start_date, self.end_date)
        weekly  = get_integrated_current(self.data, self.start_date, self.end_date, frequency="Weekly")
        monthly = get_integrated_current(self.data, self.start_date, self.end_date, frequency="Monthly")

        self.assertTrue(6 < len(daily)/len(weekly) < 8)
        self.assertTrue(3 < len(weekly)/len(monthly) < 5)
    def test_summing_basic_get_num_protons(self):
        """
        Tests the summing argument for get_num_protons
        """
        num_protons_per_day = get_num_protons(self.data, self.start_date, self.end_date)/1e17
        total_num_protons   = get_num_protons(self.data, self.start_date, self.end_date, is_summed=True)/1e17

        self.assertAlmostEqual(num_protons_per_day.sum(), total_num_protons)
    def test_condensed_proton_number(self):
        """
        Tests the size of the collected data
        """
        daily   = get_num_protons(self.data, self.start_date, self.end_date)
        weekly  = get_num_protons(self.data, self.start_date, self.end_date, frequency="Weekly")
        monthly = get_num_protons(self.data, self.start_date, self.end_date, frequency="Monthly")

        self.assertTrue(6 < len(daily)/len(weekly) < 8)
        self.assertTrue(3 < len(weekly)/len(monthly) < 5)
        
if __name__ == "__main__":
    unittest.main()
