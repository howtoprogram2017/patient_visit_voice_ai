
from dotenv import load_dotenv

from livekit import agents
from livekit.agents import AgentSession, Agent, RoomInputOptions, RoomOutputOptions, AutoSubscribe
from livekit.plugins import (
    openai,
    # elevenlabs,
    deepgram,
    noise_cancellation,
    silero, cartesia,
)
from livekit.plugins.turn_detector.multilingual import MultilingualModel

from ChainAgents import *
from app.message_model import MySessionInfo

load_dotenv()



async def entrypoint(ctx: agents.JobContext):
    await ctx.connect(auto_subscribe=AutoSubscribe.AUDIO_ONLY)
    session = AgentSession(
        userdata=MySessionInfo(),
        stt=deepgram.STT(model="nova-3", language="multi"),
        llm=openai.LLM(model="gpt-4o-mini"),
        tts=cartesia.TTS(),
        vad=silero.VAD.load(),
        turn_detection=MultilingualModel(),
    )
    root_agent = Collector1()
    (root_agent.next(Collector2()).next(Collector3()).next(Collector4())
     .next(Collector5()).next(Collector6()).next(Collector7()).next(TerminateAgent()))
    try:
        await session.start(
            room=ctx.room,
            agent=root_agent,
            room_input_options=RoomInputOptions(
                noise_cancellation=noise_cancellation.BVC(),
            ),
        )
    except Exception as e:
        print(e)





if __name__ == "__main__":
    agents.cli.run_app(agents.WorkerOptions(entrypoint_fnc=entrypoint,
                                            agent_name="my-telephony-agent"
                                            ))


