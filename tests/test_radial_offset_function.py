import numpy as np
import pytest
import pandas as pd
from pathlib import Path
from hypothesis import given, strategies as st

from scripts import radialOffset_standaloneFunction_includeMetrologyCalibration as radial
"""
Test the radialOffset_standaloneFunction_includeMetrologyCalibration code
"""



# Share global variables between tests
@pytest.fixture(scope="module")
def config():
    return dict(robot_centre = [324.470,297.834], robot_shifts_file="tests/data/radial_offset_function_files/robot_shifts_abs_220222120000.csv", example_robot_file="tests/data/radial_offset_function_files/Robot_file_for_testing.csv")

@pytest.fixture()
def robot_dataframe(config):
    print("Loading the dataframe...")
    df = pd.read_csv(config['example_robot_file'], skiprows=6)
    df = df.rename(columns={'#Magnet':'Magnet'})
    yield df

@pytest.fixture()
def example_metrology_results():
    yield pd.read_csv("tests/data/radial_offset_function_files/metrology_fitting_results_for_robot_shifts_file.csv")

@pytest.fixture()
def metrology_fit(robot_dataframe, config):
    """
    Run the metrology fit and return the results
    """
    orig_coords = np.array([robot_dataframe['Center_x'], robot_dataframe['Center_y']]).T
    theta_d = robot_dataframe['rot_platePlacing']
    metr_calibrated_coords, calibd_theta_d = radial.perform_metrology_calibration(orig_coords, theta_d, robot_centre=config['robot_centre'], robot_shifts_file=config['robot_shifts_file'])

    yield (metr_calibrated_coords, calibd_theta_d)


@pytest.fixture()
def output_file(config):
    """
    Run the main function and return the output file as a pathlib Path object
    """
    filename = config['example_robot_file']
    robot_shifts_file = config['robot_shifts_file']
    df = radial.radialOffset_standaloneFunction(filename, offset=0.0, T_observed=None, T_configured=None, plate_radius=226.0, alpha=1.2e-6, robot_centre=[324.470,297.834], robot_shifts_file=robot_shifts_file, apply_telecentricity_correction=True, apply_metrology_calibration=True, apply_roll_correction=True, verbose=False)
    input_file = Path(config['example_robot_file'])
    output_file = input_file.parent / (input_file.stem + "_radialOffsetAdjusted.csv")

    yield output_file

    # Now remove the output file
    output_file.unlink()


class Test_radial_offset_file_numerical_values:
    
    def test_original_x_values_are_returned_when_no_offset_applied(self, robot_dataframe, config):

        old_x_values = robot_dataframe.Center_x

        updated_df = radial.apply_offsets_to_magnets(robot_dataframe, offset=0, robot_centre=config['robot_centre'], apply_telecentricity_correction=False, verbose=True)

        new_x_values = updated_df.Center_x

        assert np.array_equal(old_x_values, new_x_values)

    def test_original_y_values_are_returned_when_no_offset_applied(self, robot_dataframe, config):

        old_y_values = robot_dataframe.Center_y

        updated_df = radial.apply_offsets_to_magnets(robot_dataframe, offset=0, robot_centre=config['robot_centre'], apply_telecentricity_correction=False, verbose=True)

        new_y_values = updated_df.Center_y

        assert np.array_equal(old_y_values, new_y_values)

    @pytest.mark.parametrize("centre, offset, result", [
        ((50, 50), np.sqrt(2),  (51, 51)), 
        ((50, 50), -np.sqrt(2),  (49, 49)),
        ((-50, 50), np.sqrt(2),  (-51, 51)),
        ((-50, 50), -np.sqrt(2),  (-49, 49)),
        ((50, -50), np.sqrt(2),  (51, -51)),
        ((50, -50), -np.sqrt(2),  (49, -49)),
        ((-50, -50), np.sqrt(2),  (-51, -51)),
        ((-50, -50), -np.sqrt(2),  (-49, -49)),
        ])
    def test_radial_offset_matches_expectations(self, centre, offset, result):
        """ 
        Check that the radial offset function gives the correct results for a wide range of positions on the plate
        """
        circular_magnet = pd.DataFrame(dict(Center_x=centre[0], Center_y=centre[1]), index=[0])

        new_x, new_y = radial.calculate_radial_offset(circular_magnet, offset, robot_centre=[0, 0], apply_telecentricity_correction=False)

        if not np.allclose(a=[new_x - result[0], new_y - result[1]], b=[0, 0]):
            print(centre, offset, result)
        assert np.allclose(a=[new_x - result[0], new_y - result[1]], b=[0, 0])


    @given(centre=st.tuples(st.floats(min_value=0, max_value=1000.0), st.floats(min_value=0.0, max_value=1000.0)), offset=st.floats(min_value=-1000, max_value=1000))
    def test_radial_offset_has_correct_magnitude(self, centre, offset):

        circular_magnet = pd.DataFrame(dict(Center_x=centre[0], Center_y=centre[1]), index=[0])
        new_x, new_y = radial.calculate_radial_offset(circular_magnet, offset, robot_centre=[0, 0], apply_telecentricity_correction=False)

        offset_length = np.sqrt((circular_magnet.Center_x - new_x)**2 + (circular_magnet.Center_y - new_y)**2)

        # Make an exception to test for a magnet at the plate centre where the offset will be 0
        if (centre[0] == 0.0) & (centre[1] == 0.0):
            offset = 0
        assert np.isclose(np.abs(offset_length), np.abs(offset))


    @given(circular_magnet_centre=st.tuples(st.floats(min_value=0, max_value=1000.0), st.floats(min_value=0.0, max_value=1000.0)), angle=st.floats(min_value=-360, max_value=360))
    def test_rectangular_magnets_are_along_line_through_centre_of_circular_magnet(self, circular_magnet_centre, angle):

        x_rect, y_rect = radial.calculate_rectangular_magnet_centre_coordinates(circular_magnet_centre[0], circular_magnet_centre[1], angle)

        delta_x = circular_magnet_centre[0] + 27.2 * np.cos(angle) - x_rect
        delta_y = circular_magnet_centre[1] + 27.2 * np.sin(angle) - y_rect

        assert np.allclose([delta_x, delta_y], [0, 0])

    # @pytest.mark.parametrize("circular_magnet_centre, telecentricity_colour, result", [
    #     ((10, 10), 'Blu', 20.7*0.001),
    #     ((10, 10), 'Gre', 42.0*0.001),
    #     ((-30, 50), 'Yel', 61.2*0.001),
    #     ((-30, 50), 'Mag', 79.9*0.001),
    #     ])
    @given(circular_magnet_centre=st.tuples(st.floats(min_value=0, max_value=1000.0), st.floats(min_value=0, max_value=1000.0)), telecentricity_colour=st.sampled_from(['Blu', 'Gre', 'Yel', 'Mag']))
    def test_telecentricity_correction_is_correct_magnitude(self, config, circular_magnet_centre, telecentricity_colour):

        magnet = pd.DataFrame(dict(Center_x=circular_magnet_centre[0], Center_y=circular_magnet_centre[1], Label=telecentricity_colour), index=[0])
        offset_x, offset_y = radial.calculate_telecentricity_correction(magnet, config['robot_centre'], verbose=False)

        offset_magnitude = np.sqrt(offset_x**2 + offset_y**2)

        if telecentricity_colour == 'Blu':
            correction_magnitude = 20.7*0.001
        elif telecentricity_colour == 'Gre':
            correction_magnitude = 42.0*0.001
        elif telecentricity_colour == 'Yel':
            correction_magnitude = 61.2*0.001
        elif telecentricity_colour == 'Mag':
             correction_magnitude = 79.9*0.001

        assert np.isclose(offset_magnitude, correction_magnitude)

    @given(circular_magnet_centre=st.tuples(st.floats(min_value=0, max_value=1000.0), st.floats(min_value=0, max_value=1000.0)), telecentricity_colour=st.sampled_from(['Blu', 'Gre', 'Yel', 'Mag']))
    def test_telecentricity_correction_is_radially_inwards(self, circular_magnet_centre, telecentricity_colour):

        magnet = pd.DataFrame(dict(Center_x=circular_magnet_centre[0], Center_y=circular_magnet_centre[1], Label=telecentricity_colour), index=[0])
        offset_x, offset_y = radial.calculate_telecentricity_correction(magnet, [0, 0], verbose=False)

        new_x = magnet.Center_x.values + offset_x
        new_y = magnet.Center_y.values + offset_y

        # Calculate r and theta for the original position and the new position
        # The thetas should be equal and the r values should be smaller
        old_magnet_radius = np.sqrt(magnet.Center_x**2 + magnet.Center_y**2).values
        if (magnet.Center_y.values[0] != 0.0) & (magnet.Center_x.values[0] != 0.0):
            old_magnet_theta = np.arctan(magnet.Center_y/magnet.Center_x).values
        else:
            old_magnet_theta = 0.0

        new_magnet_radius = np.sqrt(new_x**2 + new_y**2)
        if (new_y != 0.0) & (new_x != 0.0):
            new_magnet_theta = np.arctan(new_y/new_x)
        else:
            new_magnet_theta = 0.0
    
        assert np.isclose(old_magnet_theta, new_magnet_theta) & (new_magnet_radius <= old_magnet_radius)

    @given(x=st.floats(allow_nan=False, allow_infinity=False, min_value=-1e5, max_value=1e5), y=st.floats(allow_nan=False, allow_infinity=False, min_value=-1e5, max_value=1e5), magnet=st.sampled_from(['circular_magnet', 'rectangular_magnet']))
    def test_roll_correction(self, x, y, magnet):

        if magnet == 'circular_magnet':
            a = 3.313e-07
            b = -4.507e-05
            c = 1.819e-02
        elif magnet == 'rectangular_magnet':
            a = 4.133e-07
            b = -4.151e-05
            c = 1.767e-02

        p = np.poly1d([a, b, c])

        assert np.allclose(radial.roll_correction(x, y, magnet), p(y))


class Test_metrology_calibration:

    def test_fitting_results_against_known_values_for_theta(self, example_metrology_results, metrology_fit):

        metr_calibrated_coords, calibd_theta_d = metrology_fit

        assert np.allclose(calibd_theta_d.values, example_metrology_results['theta'].values)

    def test_fitting_results_against_known_values_for_x(self, example_metrology_results, metrology_fit):

        metr_calibrated_coords, calibd_theta_d = metrology_fit

        assert np.allclose(metr_calibrated_coords[:, 0], example_metrology_results['x'].values)


    def test_fitting_results_against_known_values_for_y(self, example_metrology_results, metrology_fit):

        metr_calibrated_coords, calibd_theta_d = metrology_fit

        assert np.allclose(metr_calibrated_coords[:, 1], example_metrology_results['y'].values)



class Test_radial_offset_file_saving_loading:

    def test_output_file_exists(self, output_file):

        assert output_file.exists()

    def test_header_in_output_file(self, output_file):
        # Make sure the first 6 lines are a header, as we expect
        with open(output_file, 'r') as f:
            lines = f.readlines()

        header = lines[:6]

        header_keys = [h.split(',', 1)[0] for h in header]

        specimen_header_keys = [
        "Label",
        "Date_and_Time_file_created",
        "Radial_Offset_Adjustment",
        "RobotTemp",
        "ObsTemp",
        "Radial_Scale_factor"
        ]

        assert set(header_keys) == set(specimen_header_keys)