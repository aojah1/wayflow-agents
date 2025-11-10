from pyagentspec.llms import OciGenAiConfig
from pyagentspec.llms.ociclientconfig import OciClientConfigWithApiKey

from src.common.config import *

def initialize_llm():
    try:
        return OciGenAiConfig(
            name="OCI model",
            model_id="model_id",
            compartment_id=COMPARTMENT_ID,
            client_config=OciClientConfigWithApiKey(
                name="client_config",
                service_endpoint=ENDPOINT,
                auth_file_location="~/.oci/config",
                auth_profile="DEFAULT",
            ),
        )
    except Exception as e:
        print(f"Error initializing LLM: {e}")
        raise


def test():
    from pyagentspec.agent import Agent
    from pyagentspec.property import Property

    expertise_property = Property(json_schema={"title": "domain_of_expertise", "type": "string"})
    system_prompt = """
    You are an expert in {{domain_of_expertise}}.
    Please help the users with their requests.
    """

    llm = OciGenAiConfig(
            name="OCI model",
            model_id="model_id",
            compartment_id=COMPARTMENT_ID,
            client_config=OciClientConfigWithApiKey(
                name="client_config",
                service_endpoint=ENDPOINT,
                auth_file_location="~/.oci/config",
                auth_profile="DEFAULT",
            ),
        )
    agent = Agent(
        name="Adaptive expert agent",
        system_prompt=system_prompt,
        llm_config=initialize_llm(),
        inputs=[expertise_property],
    )
    

if __name__ == "__main__":
    test()