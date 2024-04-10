PERSCRIPTION_SYS_MSG = """You will assist in analyzing medical records and returning a list of 
current medications the patient is taking in a valid JSON format. You just return 
valid JSON objects that contain the technical name, brand name, and instructions for each drug found."""

PERSCRIPTION_USER_MSG = """Extract the perscribed medications from the Provider Note below and return a 
list of current medications the patient is taking in a valid JSON format. 
Provider Note: 
{}"""

METADATA_SYS_MSG = """return metadata about the particular appointment in a valid JSON format. 
The JSON objects must contain the providers first name, last name, degree (e.g. MD), and the date of the appointment. 
If you are unsure, please respond with an empty string for each category"""

METADATA_USER_MSG = """Extract the providers first name, last name, medical degree, and the date of the appointment 
from the providers note below and return the information in valid JSON format.
Provider Note:
{}"""

FOLLOWUP_SYS_MSG = """return follow up appointments, referal appointments, and tests from the appointment in a valid JSON format.
Examples include scheduling to see a specialist, following up with the current doctor in 3 months, or get a certain type of test. 
Please do not include taking medications. 
If there are referral appointments with specialist, please ensure each type of appointment is separated into a separate task. 
If you are unsure, please respond with an empty string"""

FOLLOWUP_USER_MSG = """Extract the follw up tasks from the doctors note below and return the information in valid JSON format.
Provider Note:
{}"""

SUMMARY_SYS_MSG = """return a summary of the doctor's note in a valid JSON format. 
Please keep the summary to under three sentences at the most."""

SUMMARY_USER_MSG = """Summarize the doctors note below and return the information in valid JSON format. 
Please keep the summary under three sentences. Keep in mind, you are summarizing for me (the patient), thus 
do not need to include my name and age in the summary.
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
