import asyncio
import edge_tts

async def test_ssml():
    # Test if edge-tts supports <break> via SSML string
    # We use a simple SSML structure
    ssml = """
    <speak version="1.0" xmlns="http://www.w3.org/2001/10/synthesis" xml:lang="en-US">
        <voice name="en-US-ChristopherNeural">
            This is a test of the first sentence.
            <break time="2000ms" />
            This is a test of the second sentence after a 2-second pause.
        </voice>
    </speak>
    """
    communicate = edge_tts.Communicate(ssml=ssml)
    # We don't actually need to save it, just check if it initializes without error or we can save it to /tmp/
    output_path = "c:/Users/Administrator/Documents/kasonaops/invest_analysis/08_quarterly-earnings-analyst/tmp_test_ssml.mp3"
    try:
        await communicate.save(output_path)
        print("SSML test successful.")
    except Exception as e:
        print(f"SSML test failed: {e}")

if __name__ == "__main__":
    asyncio.run(test_ssml())
