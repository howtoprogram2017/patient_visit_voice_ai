import json
import os
from dataclasses import dataclass
from typing import Optional, AsyncIterable, AsyncGenerator, Coroutine, Any

import requests
from livekit import rtc, api
from livekit.agents import Agent, function_tool, RunContext, ModelSettings, get_job_context
from sympy.physics.quantum.matrixutils import to_scipy_sparse

from app.message_model import MySessionInfo
from  email_service import send_email


async def hangup_call():
    ctx = get_job_context()
    if ctx is None:
        # Not running in a job context
        return

    if ctx.room.name != 'fake_room':
        await ctx.api.room.delete_room(
            api.DeleteRoomRequest(
                room=ctx.room.name,
            )
        )






class ChainAgent(Agent):
    def __init__(self, instructions: str) -> None:
        super().__init__(instructions=instructions)
        self._next_agent = None

    def next(self, agent: Agent):
        self._next_agent = agent
        return agent

    def get_next_agent(self):
        if self._next_agent is None:
            return None
        return self._next_agent
    async def tts_node(
        self, text: AsyncIterable[str], model_settings: ModelSettings
    ):
        async def adjust_pronunciation(input_text: AsyncIterable[str]) -> AsyncIterable[str]:
            async for chunk in input_text:
                modified_chunk = chunk.replace("**", "  ")
                modified_chunk = modified_chunk.replace("|", " ")

                yield modified_chunk

            # Process with modified text through base TTS implementation

        async for frame in Agent.default.tts_node(
                self,
                adjust_pronunciation(text),
                model_settings
        ):
            yield frame

    async def on_enter(self) -> None:
        userdata: MySessionInfo = self.session.userdata
        # if userdata.user_name:
        await self.session.generate_reply(
            instructions=f"Tell your task to user {userdata.patient_name or None}"
        )


class Collector1(ChainAgent):
    def __init__(self) -> None:
        super().__init__(
            instructions='''Your are an intake agent.
            1.Collect the user's name and date of birth.
            2.Repeat the user's name and date of birth you have collected.
             Let user confirm. 
             '''
        )

    @function_tool()
    async def record_name(self, context: RunContext[MySessionInfo], name: str, dob: str):
        """Use this tool to record the user's name and date of birth."""
        context.userdata.patient_name = name
        context.userdata.patient_dob = dob
        return self.get_next_agent()


class Collector2(ChainAgent):
    def __init__(self) -> None:
        super().__init__(
            instructions=f"Your are an intake agent.\
            1.Collect the user's insurance information: Payer Name,Insurance ID .\
            2.Ask for Confirm."
        )
        # # self.session.c
        # self.session._chat_ctx.add_message("assistant"
        #                                    f"user name is {userdata.user_name}.")

    @function_tool()
    async def record_all(self, context: RunContext[MySessionInfo], name: str, insurance_id: int):
        """Use this tool to record the user's insurance payer name and insurance id."""
        context.userdata.insurance_payer_name = name
        context.userdata.insurance_id = insurance_id
        return self.get_next_agent()



class Collector3(ChainAgent):
    def __init__(self) -> None:
        super().__init__(
            instructions="""Your are an intake agent
            1.Ask if they have a referral, and to which physician.
            2.Ask for confirmation
            """
        )

    @function_tool()
    async def record_referral(self, context: RunContext[MySessionInfo], has_referral: bool, physician_name: str):
        """Use this tool to record if user has referral and which physician"""
        context.userdata.has_referral = has_referral
        context.userdata.referral_physician = physician_name
        return self._next_agent
        # return self._handoff_if_done()


class Collector4(ChainAgent):
    def __init__(self) -> None:
        super().__init__(
            instructions="""Your are an intake agent.
            1. Ask for the chief medical complaint or reason for visiting.
            2. Ask for confirmation
            """
        )
        self._next_agent = None

    @function_tool()
    async def record_all(self, context: RunContext[MySessionInfo], medical_complain_or_reason: str):
        """Use this tool to record the chief medical complaint or reason for visiting, this function is only called once."""
        context.userdata.medical_complain = medical_complain_or_reason

        return self.get_next_agent()


class Collector5(ChainAgent):
    def __init__(self) -> None:
        super().__init__(
            instructions="""Your are an intake agent.
            1. Ask for the user address.
            2. Valid address using function tools
            3. Notify user the validated address or the address is invalid, if not valid go back to step 1
            4. Ask for confirmation and record address, if not confirmed go back to step 1
            """
        )

    @function_tool()
    async def valid_address(self, context: RunContext[MySessionInfo], address: str) -> str | None:
        """Use this tool to validate an address.
         Return a full address if valid, else indicate invalid address."""
        await context.session.generate_reply(instructions=f"""
                      it is taking a little while to validate your address.""")
        try:
            resp = requests.post("https://addressvalidation.googleapis.com/v1:validateAddress", json={
                "address": {
                    "addressLines": [
                        address
                    ]
                }
            }, params={"key": "AIzaSyBuf8bAlRx27S5P4APiCpL7eiODq-6mKyo"})

            object = json.loads(bytearray(resp.content))["result"]
            if object["verdict"]["validationGranularity"] == "PREMISE":
                return object["address"]["formattedAddress"]
        except Exception as e:
            # (e)
            return "Invalid Address"
        return "Invalid Address"

    @function_tool()
    async def record_all(self, context: RunContext[MySessionInfo], address: str):
        """Use this tool to record an address"""
        context.userdata.patient_address = address
        return self.get_next_agent()


class Collector6(ChainAgent):
    def __init__(self) -> None:
        super().__init__(
            instructions="""Your are an intake agent.
            1. Ask for the user phone number and optional email address
            2. Ask for confirmation and record 
            """
        )

    @function_tool()
    async def record_all(self, context: RunContext[MySessionInfo], phone_number: str, email: Optional[str]):
        """Use this tool to record the phone number and optional email address"""
        context.userdata.patient_phone = phone_number
        context.userdata.patient_email = email
        return self.get_next_agent()


class Collector7(ChainAgent):
    def __init__(self) -> None:
        super().__init__(
            instructions="""Your are an intake agent. Help user to make an appointment.
            1. Provide user 2 available timeslot of (provider name, start time,end time) message
            2. Continue to provide more timeslot until user select one.
            3. Ask for confirm on the selected timeslot and record the selection
            """
        )

    @function_tool()
    async def query_timeSlot(self, context: RunContext[MySessionInfo]) -> list:
        """Use this tool to query the available timeslots information: provider_name, start_time, end_time."""
        all_slots = [
            {
                "provider_name": "Jeff",
                "start_time": "05/04/2025 10:00",
                "end_time": "05/04/2025 12:00",
            },
            {
                "provider_name": "Jeff",
                "start_time": "05/06/2025 15:00",
                "end_time": "05/06/2025 17:00",
            },
            {
                "provider_name": "Connor",
                "start_time": "05/04/2025 11:00",
                "end_time": "05/04/2025 12:00",
            },
            {
                "provider_name": "Connor",
                "start_time": "05/05/2025 17:00",
                "end_time": "05/05/2025 19:00",
            },
            {
                "provider_name": "Cole",
                "start_time": "05/09/2025 10:00",
                "end_time": "05/09/2025 12:00",
            },
            {
                "provider_name": "Cole",
                "start_time": "05/10/2025 08:00",
                "end_time": "05/10/2025 10:00",
            },
            {
                "provider_name": "Cole",
                "start_time": "05/11/2025 08:00",
                "end_time": "05/11/2025 10:00",
            },
        ]
        return all_slots

    @function_tool()
    async def record_all(self, context: RunContext[MySessionInfo], provider_name: str, start_time: str, end_time: str):
        """Use this tool to record the selected timeslot information: provider name, start time, end time."""
        context.userdata.appointment_start_time = start_time
        context.userdata.appointment_end_time = end_time
        context.userdata.appointment_provider = provider_name
        return self.get_next_agent()

class TerminateAgent(ChainAgent):
    def __init__(self) -> None:
        super().__init__(
            instructions="""
              Terminate the phone call
            """
        )

    @function_tool()
    async def terminate_call(self, context: RunContext[MySessionInfo]):
        """Use this tool to send information to the provider and terminate the phone call."""
        print("terminate",context.userdata)
        await self.session.generate_reply(
            instructions=f"Thanks for calling. Appreciate their patience. Tell them we will send email to provider"
        )
        send_email("bl2684@nyu.edu",context.userdata)
        await hangup_call()
        return None

