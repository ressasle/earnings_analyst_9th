import asyncio
import edge_tts
import os

async def test_ssml_text():
    # Test if edge-tts supports <break> if the text starts with <speak>
    ssml = """<speak version="1.0" xmlns="http://www.w3.org/2001/10/synthesis" xml:lang="en-US">
        <voice name="en-US-ChristopherNeural">
            Sentence one.
            <break time="2000ms" />
            Sentence two after pause.
        </voice>
    </speak>"""
    
    # In some versions, you just pass it as 'text'
    communicate = edge_tts.Communicate(text=ssml, voice="en-US-ChristopherNeural")
    output_path = "c:/Users/Administrator/Documents/kasonaops/invest_analysis/08_quarterly-earnings-analyst/tmp_test_ssml_text.mp3"
    try:
        await communicate.save(output_path)
        print("SSML-in-text test successful.")
    except Exception as e:
        print(f"SSML-in-text test failed: {e}")

if __name__ == "__main__":
    asyncio.run(test_ssml_text())
