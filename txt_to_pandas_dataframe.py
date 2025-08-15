import pandas as pd
from numpy import isclose
import matplotlib.pyplot as plt
import os


def text_to_pandas_dataframe(file):
    """
    Grabs the data from the a given beam integrated
    current log file and converts it to a pandas dataframe
    """
    data = pd.read_csv(
        file,
        delim_whitespace=True,
        skiprows=5,
        header=None,
        names=[
            "Modified Julian day no.",
            "Date",
            "Milliamp-hours (Sync)",
            "Milliamp-hours (TS-1)",
            "Milliamp-hours (TS-2)",
            "Cumulative milliamp-hours (Sync)",
            "Cumulative milliamp-hours (TS-1)",
            "Cumulative milliamp-hours (TS-2)",
        ],
    )
    data["Date"] = pd.to_datetime(data["Date"])
    return data


def find_decreasing_value(data, column):
    """
    Locates where a given column has values that decrease
    """
    prev_value = 0
    found = False
    for i, value in enumerate(data[column].values):
        if value < prev_value:
            if not found:
                print("Found decreasing integrated current at:")
                found = True
            # Displays the datetime and column of where the value has decreased
            print(
                f"{pd.to_datetime(data['Date'].values[i]).strftime('%d-%b-%Y')} ({column})"
            )
        prev_value = value
    return found


def data_integrity_check(data):
    """
    Makes sure the data is in the expected format (will put into another file)
    """
    sorted_checks = [
        "Modified Julian day no.",
        # "Cumulative milliamp-hours (Sync)", #04-Sep-2005
        # "Cumulative milliamp-hours (TS-1)", #04-Sep-2005
        "Cumulative milliamp-hours (TS-2)",
    ]

    # Checks the expected columns never decrease in value
    for column in sorted_checks:
        # assert not find_decreasing_value(data, column)
        assert data[column].is_monotonic_increasing, f"{column} is not sorted"

    # Checks that the Cumulative columns are within error equal to the non cumulative columns when summed up to be cumulative
    for target in ("Sync", "TS-1", "TS-2"):
        assert (
            isclose(
                data[f"Milliamp-hours ({target})"].cumsum(),
                data[f"Cumulative milliamp-hours ({target})"],
                atol=0.1,
            )
        ).all()

    # Checks that the Date column doesn't have any duplicates
    assert (
        not data["Modified Julian day no."].duplicated().any()
    ), "Duplicated dates found"


def get_sliced_data(data, start_date, end_date, frequency="Daily", is_averaged=False):
    """
    Gets a slice of the database between given dates
    """
    start_date = pd.to_datetime(start_date)
    end_date = pd.to_datetime(end_date)
    if start_date not in data["Date"].values:
        print("Invalid start_date")
        return None
    elif end_date not in data["Date"].values:
        print("Invalid end_date")
        return None

    # Defining the slice
    start_index = data.index[data["Date"] == start_date].values[0]
    end_index = data.index[data["Date"] == end_date].values[0]

    if end_index < start_index:
        print("end_date can not be before start_date")
        return None

    # Grabs the desired slice of the database
    match frequency:
        case "Daily":
            used_data = data.iloc[start_index:end_index + 1]
        case "Weekly":
            if is_averaged:
                used_data = (
                    data.iloc[start_index:end_index + 1]
                    .resample("W", on="Date")
                    .mean(numeric_only=True)
                )
            else:
                used_data = (
                    data.iloc[start_index:end_index + 1]
                    .resample("W", on="Date")
                    .sum(numeric_only=True)
                )
        case "Monthly":
            if is_averaged:
                used_data = (
                    data.iloc[start_index:end_index + 1]
                    .resample("M", on="Date")
                    .mean(numeric_only=True)
                )
            else:
                used_data = (
                    data.iloc[start_index:end_index + 1]
                    .resample("M", on="Date")
                    .sum(numeric_only=True)
                )
        case _:
            print("Invalid frequency\n(Only: Daily, Weekly, or Monthly allowed)")
            return None

    return used_data


def get_integrated_current(data, start_date, end_date=None, target="TS-1", valid_targets=("Sync", "TS-1", "TS-2"),
                           frequency="Daily", is_averaged=False, is_summed=False):
    """
    Gets the integrated current hitting a given target
    for either a given date or range of dates
    """
    if target not in valid_targets:
        print("Invalid target")
        return None
    if end_date is None:
        start_date = pd.to_datetime(start_date)
        if start_date not in data["Date"].values:
            print("Invalid start_date")
            return None
        # Returns the integrated current for a given date
        return data[data["Date"] == start_date][f"Milliamp-hours ({target})"].values[0]
    else:
        if target not in valid_targets:
            print("Invalid target")
            return None

        used_data = get_sliced_data(
            data, start_date, end_date, frequency=frequency, is_averaged=is_averaged
        )

        if used_data is not None:
            integrated_currents = used_data[f"Milliamp-hours ({target})"].values

            # Returns the sum of the integrated current for a range of given dates
            if is_summed:
                return integrated_currents.sum()

            # Returns the integrated current for a range of given dates
            return integrated_currents


def is_beam_on(data, date, target="TS-1"):
    """
    Checks whether the beam was on for a given date
    """
    return get_integrated_current(data, date, target=target, is_summed=True) > 0


def plot_integrated_current(data, start_date, end_date, target="TS-1", valid_targets=("Sync", "TS-1", "TS-2"),
                            frequency="Daily", is_averaged=False, is_high_resolution=False, is_shown=False,
                            is_saved=True, date_format="%d-%b-%Y", file_name=None):
    """
    Plots the integrated current over a range of dates
    """
    if target not in valid_targets:
        print("Invalid target")
        return None

    if is_averaged and frequency == "Daily":
        print(
            "Can't extract average daily data\n(minimum frequency for averaging = Weekly)"
        )
        return None

    # Gets the data for the x and y axes
    used_data = get_sliced_data(
        data, start_date, end_date, frequency=frequency, is_averaged=is_averaged
    )
    if frequency == "Daily":
        dates = used_data["Date"]
    else:
        dates = used_data[f"Milliamp-hours ({target})"].keys().values
    integrated_currents = used_data[f"Milliamp-hours ({target})"].values

    # Warning:
    # If enabled, this will make the plotting slower and will produce a larger but more accurate graph
    if is_high_resolution:
        plt.rcParams["savefig.dpi"] = 300
        if is_shown:
            plt.rcParams["figure.dpi"] = 300

    plt.tight_layout()
    plt.figure(figsize=(15, 5))

    start_date = pd.to_datetime(start_date).strftime(date_format)
    end_date = pd.to_datetime(end_date).strftime(date_format)

    plt.xlabel("Date")
    if is_averaged:
        plt.ylabel(f"{target} {frequency} Average Integrated Current (Milliamp-hours)")
        if file_name is None:
            file_name = f"graphs/{target}_averaged_{start_date}_to_{end_date}_{frequency}_Integrated_Currents.png"
    else:
        plt.ylabel(f"{target} {frequency} Integrated Current (Milliamp-hours)")
        if file_name is None:
            file_name = f"graphs/{target}_{start_date}_to_{end_date}_{frequency}_Integrated_Currents.png"

    plt.plot(dates, integrated_currents, ":o")

    if not os.path.isdir("graphs"):
        os.mkdir("graphs")

    if is_saved:
        plt.savefig(file_name, bbox_inches="tight")
        print(f"Saved {file_name}")

    if is_shown:
        plt.show()
    else:
        plt.clf()


def get_num_protons(
    data,
    start_date,
    end_date=None,
    target="TS-1",
    valid_targets=("Sync", "TS-1", "TS-2"),
    frequency="Daily",
    is_averaged=False,
    is_summed=False,
    per_second=False,
):
    """
    Returns a list of the number of protons per specified amount of time (need to double check)
    """
    proton_charge = 1.6e-19
    integrated_current = get_integrated_current(
        data,
        start_date,
        end_date,
        target=target,
        valid_targets=valid_targets,
        frequency=frequency,
        is_averaged=is_averaged,
        is_summed=is_summed,
    )
    num_protons = (integrated_current * (1e-3)) / proton_charge

    if per_second:
        return num_protons / 86400

    return num_protons


def get_average_power(data, start_date, end_date=None, target="TS-1", valid_targets=("Sync", "TS-1", "TS-2"),
                      frequency="Daily", is_averaged=False, is_summed=False, voltage=800,
                      voltage_unit_factor=(1e6)*(1.6e-19), current_unit_factor=(1e-3)/86400):

    # Default: MeV -> J
    voltage *= voltage_unit_factor

    # Default: mAh -> A
    integrated_current = current_unit_factor * get_integrated_current(
        data,
        start_date,
        end_date=end_date,
        target=target,
        valid_targets=valid_targets,
        frequency=frequency,
        is_averaged=is_averaged,
        is_summed=is_summed,
    )

    return voltage * integrated_current


if __name__ == "__main__":
    data = text_to_pandas_dataframe("mahdy3-op-by-day_to-08jun25.txt")

    data_integrity_check(data)

    start_date = "16-Apr-1991"
    end_date = "28-Jul-1991"
    wrong_date = "16-Apr-1891"
    print(get_integrated_current(data, start_date))
    print(get_integrated_current(data, wrong_date))
    print(get_integrated_current(data, wrong_date, end_date))
    print(get_integrated_current(data, start_date, end_date))
    print(get_integrated_current(data, start_date, end_date, is_summed=True))
    print(is_beam_on(data, start_date))
    print(is_beam_on(data, "01-Jan-1991"))
    daily = get_integrated_current(data, start_date, end_date)
    weekly = get_integrated_current(data, start_date, end_date, frequency="Weekly")
    monthly = get_integrated_current(data, start_date, end_date, frequency="Monthly")
    print(len(daily))
    print(daily)
    print(len(weekly))
    print(weekly)
    print(len(monthly))
    print(monthly)
    plot_integrated_current(data, start_date, end_date)
    plot_integrated_current(data, start_date, end_date, frequency="Weekly")
    plot_integrated_current(data, start_date, end_date, frequency="Monthly")
    plot_integrated_current(
        data, start_date, end_date, frequency="Weekly", is_averaged=True
    )
    plot_integrated_current(
        data, start_date, end_date, frequency="Monthly", is_averaged=True
    )
    print(f"{get_num_protons(data, start_date, is_summed=True):e}")
    print(get_num_protons(data, start_date, end_date, is_summed=True))
    print(
        get_num_protons(
            data, start_date, end_date, frequency="Weekly", is_averaged=True
        )
    )
    print(get_average_power(data, start_date, end_date, is_summed=True))

    print("Done")

