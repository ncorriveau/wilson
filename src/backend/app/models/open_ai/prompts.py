PERSCRIPTION_SYS_MSG = """You will assist in analyzing medical records and returning a list of 
current medications the patient is taking in a valid JSON format. You just return 
valid JSON objects that contain the technical name, brand name, and instructions for each drug found."""

PERSCRIPTION_USER_MSG = """Extract the perscribed medications from the Provider Note below and return a 
list of current medications the patient is taking in a valid JSON format. Please do not return names in all caps, but instead 
each prescription name should be in title case e.g. 'Ibuprofen'.
Provider Note: 
{}"""

METADATA_SYS_MSG = """return metadata about the particular appointment in a valid JSON format. 
The JSON objects must contain the providers first name, last name, degree (e.g. MD), and the date of the appointment. 
If available, also include the provider's NPI number, providers office location, and specialty.
The providers NPI is a 10 digit unique identifier number, the location should include the street, city, state, and zip code. 
The specialty should be one of the following: {}. 

If you are unsure, please respond with a None value for the category"""

METADATA_USER_MSG = """Extract the providers first name, last name, medical degree, NPI, specialty, location, and the date of the appointment 
from the providers note below and return the information in valid JSON format. The first name, last name, and medical degree should always be
available. Please only include the NPI, location, and specialty if available.
Provider Note:
{}"""

FOLLOWUP_SYS_MSG = """return follow up appointments, referal appointments, and tests from the appointment in a valid JSON format.
Examples include scheduling to see a specialist, following up with the current doctor in 3 months, or get a certain type of test. 
Please do not include taking medications. 
If there are referral appointments with specialist, please ensure each type of appointment is separated into a separate task. 
If you are unsure, please respond with an empty string"""

FOLLOWUP_USER_MSG = """Extract the follw up tasks from the doctors note below and return the information in valid JSON format.
Please convert all of the follow up tasks into Title Case e.g. you should not have FOLLOW UP WITH ENT but instead Follow up with ENT. 
Provider Note:
{}"""

SUMMARY_SYS_MSG = """Return a summary of the doctor's note in a valid JSON format. 
Please keep the summary to under three sentences at the most."""

SUMMARY_USER_MSG = """Summarize the doctors note below and return the information in valid JSON format. 
Please keep the summary under three sentences. You are summarizing for me (the patient), thus 
do not need to include my name and age in the summary. Please refrain from calling me 'the patient' in the summary.
You should describe the events at a high level and provide a summary of the diagnosis and treatment plan.
Provider Note: {}"""


def build_system_msg(msg: str, schema: dict[str]) -> str:
    """helper function to build system messages. The msg should contain more specific instructions about the task,
    while the schema should match what you want your response JSON schema to look like
    """
    return f"""You are an expert AI assistant for medical practitioners. 
            You will assist in analyzing medical records, extracting information, and returning the information in valid JSON format. 
            Specifically, please complete the following: {msg}. 
            Follow the JSON schema provided below to ensure the information is returned in the correct format.
            JSON Schema: 
            {schema}"""
