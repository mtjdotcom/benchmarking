import gspread as gs
import streamlit as st
import pandas as pd
from datetime import datetime
from google.oauth2 import service_account

## CONNECT TO GOOGLE DRIVE #################################################################
credentials = service_account.Credentials.from_service_account_info(
    st.secrets["gcp_service_account"],
    scopes=["https://www.googleapis.com/auth/spreadsheets","https://www.googleapis.com/auth/drive"],)

client=gs.authorize(credentials)
sheet_url = st.secrets["private_gsheets_url"]
sheet = client.open_by_url(sheet_url)
tvpi_gsheet = sheet.worksheet('tvpi')
dpi_gsheet = sheet.worksheet('dpi')
footnote_gsheet = sheet.worksheet('footnotes')

## Password function ######################################################################
def check_password():
    """Returns `True` if the user had the correct password."""

    def password_entered():
        """Checks whether a password entered by the user is correct."""
        if st.session_state["password"] == st.secrets["password"]:
            st.session_state["password_correct"] = True
            del st.session_state["password"]  # don't store password
        else:
            st.session_state["password_correct"] = False

    if "password_correct" not in st.session_state:
        # First run, show input for password.
        st.text_input(
            "Password", type="password", on_change=password_entered, key="password"
        )
        return False
    elif not st.session_state["password_correct"]:
        # Password not correct, show input + error.
        st.text_input(
            "Password", type="password", on_change=password_entered, key="password"
        )
        st.error("😕 Password incorrect")
        return False
    else:
        # Password correct.
        return True

if check_password():
	st.title("Benchmarking Tool")
	col1, col2 = st.columns(2)
	tab1, tab2, = st.tabs(["TVPI", "DPI"])

	## IMPORT AND CLEAN DATA ############################################################

	@st.cache_data
	def import_footnotes():
		all_data_fn = pd.DataFrame(footnote_gsheet.get_all_records())
		all_data_fn = all_data_fn.reset_index(drop=True)
		return(all_data_fn)

	all_data_fn = import_footnotes()	

	@st.cache_data
	def import_tvpi():
		all_data_tvpi = pd.DataFrame(tvpi_gsheet.get_all_records())
		all_data_tvpi = all_data_tvpi.reset_index(drop=True)
		
		# convert column names
		all_data_tvpi.columns = ['Vintage Year', 'Pooled Return', 'Arithmetic Mean', 'Median', 'Top 5%', 'Upper Quartile', 'Lower Quartile', 'Bottom 5%', 'Number of Funds', 'As of Date',
		'As of Quarter', 'Year', 'Quarter']
		# change vintage year column into a string
		all_data_tvpi['Vintage Year'] = all_data_tvpi['Vintage Year'].astype(str)
		# change as of date into a datetime
		all_data_tvpi['As of Date'] = pd.to_datetime(all_data_tvpi['As of Date'], dayfirst=True)
		all_data_tvpi = all_data_tvpi.sort_values(by=['Vintage Year', 'As of Date'], ascending=[True, True])
		# drop year and quarter
		all_data_tvpi.drop(['Year', 'Quarter'], axis=1, inplace=True)
		return(all_data_tvpi)

	all_data_tvpi = import_tvpi()

	# import_tvpi()	

	@st.cache_data
	def import_dpi():
		all_data_dpi = pd.DataFrame(dpi_gsheet.get_all_records())
		all_data_dpi = all_data_dpi.reset_index(drop=True)
		all_data_dpi.columns = ['Vintage Year', 'Pooled Return', 'Arithmetic Mean', 'Median', 'Top 5%', 'Upper Quartile', 'Lower Quartile', 'Bottom 5%', 'Number of Funds', 'As of Date',
		'As of Quarter', 'Year', 'Quarter']
		# change vintage year column into a string
		all_data_dpi['Vintage Year'] = all_data_dpi['Vintage Year'].astype(str)
		# change as of date into a datetime
		all_data_dpi['As of Date'] = pd.to_datetime(all_data_dpi['As of Date'], dayfirst=True)
		all_data_dpi = all_data_dpi.sort_values(by=['Vintage Year', 'As of Date'], ascending=[True, True])
		# drop year and quarter
		all_data_dpi.drop(['Year', 'Quarter'], axis=1, inplace=True)
		return(all_data_dpi)

	all_data_dpi = import_dpi()

	## FUNCTIONS ########################################################################

	# function for converting the user selected dataframe into a CSV
	@st.cache_data
	def convert_df(df):
		return(df.to_csv().encode('utf-8'))

	@st.cache_data
	def qcheck_tvpi(vy, asof, tvpi):
		try:
			df = all_data_tvpi.loc[(all_data_tvpi['Vintage Year'] == vy) & (all_data_tvpi['As of Quarter'] == asof)][['Median', 'Upper Quartile', 'Lower Quartile']]
			if float(tvpi) > float(df['Median']):
				if float(tvpi) > float(df['Upper Quartile']):
					return("1st Quartile")
				else:
					return("2nd Quartile")
			else:
				if float(tvpi) > float(df['Lower Quartile']):
					return("3rd Quartile")
				else:
					return("4th Quartile")
		except:
			return(st.write("A quartlie cannot be calculated with your inputs. Your vintage year is too old to have recent performance. Please double check your vintage year and performance quarter."))

			
	@st.cache_data		
	def qcheck_dpi(vy, asof, dpi):
		try:
			df = all_data_dpi.loc[(all_data_dpi['Vintage Year'] == vy) & (all_data_dpi['As of Quarter'] == asof)][['Median', 'Upper Quartile', 'Lower Quartile']]
			if float(dpi) > float(df['Median']):
				if float(dpi) > float(df['Upper Quartile']):
					return("1st Quartile")
				else:
					return("2nd Quartile")
			else:
				if float(dpi) > float(df['Lower Quartile']):
					return("3rd Quartile")
				else:
					return("4th Quartile")
		except:
			return(st.write("A quartlie cannot be calculated with your inputs. Your vintage year is too old to have recent performance. Please double check your vintage year and performance quarter."))

	# TVPI tab ########################################################################################################################################################################

	with tab1:

		#header
		st.subheader("Download TVPI Benchmark Data")
		st.caption("Please select the metrics, vintage year, and as of date below. Not all vintage years have performance figures available for all dates, e.g., 1981 vintage as of Q2 2018. There is no performance data available as of Q3 2014.")

		# create lists for selection and create multi selection box
		by_vy = all_data_tvpi['Vintage Year'].unique().tolist()
		as_of = all_data_tvpi['As of Quarter'].unique().tolist()
		selected_columns = st.multiselect('Select desired benchmark metrics:', all_data_tvpi.columns, ['As of Quarter', 'Vintage Year'])
		VY = st.selectbox("Vintage year:", by_vy)
		as_of_date = st.selectbox('Performance as of:', as_of)

		# dataframe filtering/display
		as_of_df = all_data_tvpi.loc[(all_data_tvpi['Vintage Year']==VY) & (all_data_tvpi['As of Quarter']==as_of_date)]
		as_of_df[selected_columns]

		csv_tvpi = convert_df(as_of_df[selected_columns])

		st.divider()

		# button creation
		st.download_button(
			label="Download data as CSV",
			data=csv_tvpi,
			file_name='benchmark_data_tvpi',
			mime='text/csv')


		with st.expander("Benchmark Composition:"):
			st.write(all_data_fn.loc[all_data_fn['As of Quarter'] == as_of_date]['Footnote'].item())

		st.divider()
		st.subheader("Benchmark Your TVPI")
		st.caption("Please select your Fund's vintage year and the quarter you would like to benchmark your TVPI against.")
		user_vy = all_data_tvpi['Vintage Year'].unique().tolist()
		user_vy_selected = st.selectbox("Fund Vintage Year:", user_vy)
		as_of_user = all_data_tvpi['As of Quarter'].unique().tolist()
		as_of_user_selected = st.selectbox('Performance as of', as_of_user)
		number = st.number_input('Insert Net TVPI:')
		
		st.metric(label='Your TVPI is: ', value=qcheck_tvpi(user_vy_selected, as_of_user_selected, number))

		st.divider()

		with st.expander("Benchmark Composition:"):
			st.write(all_data_fn.loc[all_data_fn['As of Quarter'] == as_of_user_selected]['Footnote'].item())

		st.divider()

	# DPI tab ########################################################################################################################################################################

	with tab2:
		#header
		st.subheader("Download DPI Benchmark Data")
		st.caption("Please select the metrics, vintage year, and as of date below. Not all vintage years have performance figures available for all dates, e.g., 1981 vintage as of Q2 2018. There is no performance data available as of Q3 2014.")

		# create lists for selection and create multi selection box
		by_vy_dpi = all_data_dpi['Vintage Year'].unique().tolist()
		as_of_dpi = all_data_dpi['As of Quarter'].unique().tolist()
		selected_columns_dpi = st.multiselect('Select desired benchmark metrics', all_data_dpi.columns, ['As of Quarter', 'Vintage Year'])
		VY_dpi = st.selectbox("Vintage Year:", by_vy_dpi)
		as_of_date_dpi = st.selectbox('Performance as of date:', as_of_dpi)

		# dataframe filtering/display
		as_of_df_dpi = all_data_dpi.loc[(all_data_dpi['Vintage Year']==VY_dpi) & (all_data_dpi['As of Quarter']==as_of_date_dpi)]
		as_of_df_dpi[selected_columns_dpi]

		csv_dpi = convert_df(as_of_df_dpi[selected_columns_dpi])

		st.divider()

		# button creation
		st.download_button(
			label="Download data as CSV",
			data=csv_dpi,
			file_name='benchmark_data_dpi',
			mime='text/csv')

		with st.expander("Benchmark Composition"):
			st.write(all_data_fn.loc[all_data_fn['As of Quarter'] == as_of_date_dpi]['Footnote'].item())

		st.divider()
		st.subheader("Benchmark Your DPI")
		st.caption("Please select your Fund's vintage year and the quarter you would like to benchmark your DPI against.")
		user_vy_dpi = all_data_dpi['Vintage Year'].unique().tolist()
		user_vy_selected_dpi = st.selectbox("Fund Vintage Year", user_vy_dpi)
		as_of_user_dpi = all_data_dpi['As of Quarter'].unique().tolist()
		as_of_user_selected_dpi = st.selectbox('Performance as of date', as_of_user_dpi)
		number_dpi = st.number_input('Insert DPI:')
		
		st.metric(label='Your DPI is: ', value=qcheck_dpi(user_vy_selected_dpi, as_of_user_selected_dpi, number_dpi))

		st.divider()

		with st.expander("Benchmark Composition"):
			st.write(all_data_fn.loc[all_data_fn['As of Quarter'] == as_of_user_selected_dpi]['Footnote'].item())

		st.divider()
