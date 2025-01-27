# file_handler.py
import streamlit as st
import tempfile
import pandas as pd
import xlrd
import os


def upload_file(should_display: bool = False):
  """
      Upload a file using Streamlit File Uploader widget.

      Returns:
          str or None: The path to the uploaded file if available, otherwise None.
      """
  if should_display:
    with st.expander(":file_folder: UPLOAD FILE", expanded=False):
      st.write("""
    ...         Click **Browse files** or **Drag and drop** to upload clump instrument run export file in the format:
                :blue[RunXXXX.xls] 
    ...     """)
      # file_uploader label should be define with " " to hide the label
      file = st.file_uploader(" ",
                              type=["xls", "xlsx"],
                              label_visibility="collapsed")
      if file is not None:
        # Save the file name in session state
        st.session_state.uploaded_filename = file.name  # Include this line to save the uploaded file name
        # Create a temporary file to store the uploaded file contents
        with tempfile.NamedTemporaryFile(suffix="xls", delete=False) as tmp:
          tmp.write(file.read())

        return tmp.name
  else:
    return None


def open_excel_file(file):
  """
    Read and filter data from two Excel shhets into Pandas DataFrames.

    Args:
    file (str): The path to the Excel file containing data.

    Returns:
        tuple: A tuple containing two Pandas DataFrames.
            - df_std_cp: A filtered DataFrame from 'CLIQS_clumped_export_2203' sheet.
            - df_intensity_cp: A filtered DataFrame from 'CLIQS_clumped_all_cycles_extra_' sheet.
            - df_extra_cup: A filtered DataFrame from 'CLIQS_extra_cup_22032024.wke' sheet.

    Raises:
        FileNotFoundError: If the file is not found.
    """
  # Define the sheet names to read
  sheet_names = [
      ('CLIQS_clumped_export_extra_2203', 'df_std'),
      ('CLIQS_clumped_all_cycles_extra_', 'df_intensity'),
      ('CLIQS_extra_cup_22032024.wke', 'df_extra_cup')]

  # Check if the file name has changed or is new before printing
  if 'uploaded_filename' in st.session_state and st.session_state.uploaded_filename not in st.session_state.get('printed_filenames', []):
      print("Uploaded file name:", st.session_state.uploaded_filename)

  try:
      # Read the sheets
      workbook = xlrd.open_workbook(file, logfile=open(os.devnull, "w"))
      # Get dataframes assigned to each sheet in sheet_names
      # print("Worksheet names:", workbook.sheet_names())

      # Dictionary to hold dataframes
      dfs = {name: pd.DataFrame() for _, name in sheet_names}

      # Read data from the Excel file
      for sheet, df_name in sheet_names:
          # print(f"Reading data from {sheet} sheet")
          if sheet in workbook.sheet_names():
              dfs[df_name] = pd.read_excel(workbook, sheet_name=sheet)
              # print(dfs[df_name].columns.str.strip())
  except FileNotFoundError:
      raise FileNotFoundError("File not found!")

  # Accessing the dataframes
  df_std = dfs['df_std']
  df_intensity = dfs['df_intensity']
  df_extra_cup = dfs['df_extra_cup']

  # # Filter both DataFrames to include only 'standard' and 'standard_refill' identifiers
  df_std_cp = df_std[df_std['Identifier 2'].isin(
      ['standard', 'standard_refill'])]
  df_intensity_cp = df_intensity[df_intensity['Identifier 2'].isin(
      ['standard', 'standard_refill'])]

  # Drop unnecessary columns
  df_std_cp = df_std_cp.drop(columns=["Time", "Date"])

  # Rename column Weight (mg) (mg) to Weight
  df_std_cp = df_std_cp.rename(columns={"Weight (mg)": "Weight"})

  # Convert 'Time Code' to datetime format
  df_std_cp["Time Code"] = pd.to_datetime(df_std_cp["Time Code"])
  df_intensity_cp["Time Code"] = pd.to_datetime(df_intensity_cp["Time Code"])
  df_extra_cup["Time Code"] = pd.to_datetime(df_extra_cup["Time Code"])

  # Identify and convert columns containing text values to strings
  text_columns_std = df_std_cp.select_dtypes(include=["object"]).columns
  text_columns_intensity = df_intensity_cp.select_dtypes(
      include=["object"]).columns
  text_columns_extra = df_extra_cup.select_dtypes(include=["object"]).columns

  df_std_cp[text_columns_std] = df_std_cp[text_columns_std].astype("string")
  df_intensity_cp[text_columns_intensity] = df_intensity_cp[
      text_columns_intensity].astype("string")
  df_extra_cup[text_columns_extra] = df_extra_cup[text_columns_extra].astype("string")
  # numeric columns
  # numeric_columns = df_std_cp.select_dtypes(include=["float64", "Int64"]).columns

  return df_std_cp, df_intensity_cp, df_extra_cup
